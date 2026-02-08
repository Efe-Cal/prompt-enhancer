import json
import asyncio
import os
import traceback
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from django.conf import settings
from asgiref.sync import sync_to_async
from dotenv import load_dotenv
from . import log
from .shared_utils import PromptConfig

load_dotenv()

def _check_rate_limit_sync(ip_address):
        """Check if IP has exceeded rate limit."""
        cache_key = f"ws_enhance_limit_{ip_address}"
        count = cache.get(cache_key, 0)
        
        limit = getattr(settings, 'WS_RATE_LIMIT', 5)
        
        if count >= limit:
            return False
            
        if count == 0:
            cache.set(cache_key, 1, 60)
        else:
            cache.incr(cache_key)
            
        return True


class EnhanceConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pending_answer = None
        self.answer_event = None
        self.enhancement_task = None

    async def connect(self):
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.room_group_name = f'enhance_{self.task_id}'
        self.pending_answer = None
        self.answer_event = asyncio.Event()

        log(f"[WebSocket] Client connecting to group: {self.room_group_name}")

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        log(f"[WebSocket] Client connected and joined group: {self.room_group_name}")

    async def disconnect(self, close_code):
        log(f"[WebSocket] Client disconnecting from group: {self.room_group_name}")
        if self.enhancement_task and not self.enhancement_task.done():
            self.enhancement_task.cancel()
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        log(f"[WebSocket] Received message: {text_data[:200]}")
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            log(f"[WebSocket] Message type: {message_type}")

            if message_type == 'user_answer':
                answer = text_data_json.get('answers')
                self.pending_answer = answer
                self.answer_event.set()
                
                await self.send(text_data=json.dumps({
                    'type': 'answer_received',
                    'status': 'ok'
                }))

            elif message_type == 'enhance':
                # Rate limit check
                client_ip = self.scope.get('client', ['0.0.0.0'])[0]
                is_allowed = await sync_to_async(_check_rate_limit_sync)(client_ip)
                
                if not is_allowed:
                    log(f"[WebSocket] Rate limit exceeded for IP: {client_ip}")
                    await self.send(text_data=json.dumps({
                        'type': 'task_error',
                        'error': 'Rate limit exceeded. Please wait a minute before trying again.'
                    }))
                    return

                log("[WebSocket] Starting enhancement...")
                # Send acknowledgment first
                await self.send(text_data=json.dumps({
                    'type': 'processing',
                    'message': 'Enhancement started'
                }))
                
                # Run enhancement and handle result in callback
                self.enhancement_task = asyncio.create_task(
                    self._run_enhancement_with_callback(text_data_json)
                )

        except Exception as e:
            log(f"[WebSocket] Error in receive: {e}")
            traceback.print_exc()

    async def _run_enhancement_with_callback(self, data):
        """Wrapper that ensures errors are properly sent to client."""
        try:
            await self.run_enhancement(data)
        except asyncio.CancelledError:
            log("[WebSocket] Enhancement task was cancelled")
        except Exception as e:
            log(f"[WebSocket] Unhandled error in enhancement: {e}")
            traceback.print_exc()
            try:
                await self.send(text_data=json.dumps({
                    'type': 'task_error',
                    'error': str(e)
                }))
            except Exception:
                pass

    async def run_enhancement(self, data):
        """Run the enhancement process directly in the WebSocket consumer."""
        try:
            # Import here to avoid circular imports at module load time
            from .enhance import enhance_prompt_async
            
            log(f"[WebSocket] Calling enhance_prompt_async with task: {data.get('task', '')[:50]}")
            
            config = PromptConfig(
                model=os.getenv("MODEL", "gemini-3-flash-preview"),
                use_web_search=data.get('use_web_search', True),
                additional_context_query=data.get('additional_context_query', ''),
                ask_user_func=self.ask_user_question,
                target_model=data.get('target_model', 'gpt-5.1'),
                is_reasoning_native=data.get('is_reasoning_native', False),
                prompt_style=data.get('prompt_style', {}),
            )
            result, is_fallback, messages = await enhance_prompt_async(
                task=data.get('task', ''),
                lazy_prompt=data.get('lazy_prompt', ''),
                config=config,
            )
            
            result = result or "Sorry, I couldn't generate a response."
            messages = messages or []
            
            serializable_messages = []
            for msg in messages:
                if hasattr(msg, 'model_dump'):
                    serializable_messages.append(msg.model_dump(mode="json"))
                elif isinstance(msg, dict):
                    serializable_messages.append(msg)
                else:
                    serializable_messages.append(str(msg))
            cache.set(f"enhance_messages_{self.task_id}", serializable_messages, timeout=3600)
            
            log(f"[WebSocket] Enhancement complete, result length: {len(result)}, messages stored: {len(messages)}")
            
            await self.send(text_data=json.dumps({
                'type': 'task_complete',
                'result': result,
                'is_fallback': is_fallback
            }))
            log("[WebSocket] Sent task_complete to client")
            
        except Exception as e:
            log(f"[WebSocket] Enhancement error: {e}")
            traceback.print_exc()
            await self.send(text_data=json.dumps({
                'type': 'task_error',
                'error': str(e)
            }))

    async def ask_user_question(self, questions: str, timeout: int = 300) -> str:
        """Ask user a question and wait for answer via WebSocket."""
        self.answer_event.clear()
        self.pending_answer = None
        
        log(f"[WebSocket] Asking user question: {questions}")
        await self.send(text_data=json.dumps({
            'type': 'user_question',
            'questions': questions
        }))
        
        try:
            await asyncio.wait_for(self.answer_event.wait(), timeout=timeout)
            answer = self.pending_answer
            self.pending_answer = None
            log(f"[WebSocket] Got user answer: {answer}")
            return answer or ""
        except asyncio.TimeoutError:
            raise TimeoutError(f"User did not respond within {timeout} seconds")


    async def task_complete(self, event):
        """Send task completion to WebSocket (for group messages)."""
        await self.send(text_data=json.dumps({
            'type': 'task_complete',
            'result': event['result']
        }))

    async def task_error(self, event):
        """Send task error to WebSocket (for group messages)."""
        await self.send(text_data=json.dumps({
            'type': 'task_error',
            'error': event['error']
        }))


class EditConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.messages: list[dict] = []
        self.edit_task = None
        self.pending_answer = None
        self.answer_event = None
    
    async def connect(self):
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.room_group_name = f'edit_{self.task_id}'
        self.answer_event = asyncio.Event()


        log(f"[WebSocket] EditConsumer connecting to group: {self.room_group_name}")

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        log(f"[WebSocket] EditConsumer connected and joined group: {self.room_group_name}")
    
    async def disconnect(self, close_code):
        log(f"[WebSocket] EditConsumer disconnecting from group: {self.room_group_name}")
        if self.edit_task and not self.edit_task.done():
            self.edit_task.cancel()
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    async def receive(self, text_data):
        
        # Rate limit check
        client_ip = self.scope.get('client', ['0.0.0.0'])[0]
        is_allowed = await sync_to_async(_check_rate_limit_sync)(client_ip)
        
        if not is_allowed:
            log(f"[WebSocket] Rate limit exceeded for IP: {client_ip}")
            await self.send(text_data=json.dumps({
                'type': 'task_error',
                'error': 'Rate limit exceeded. Please wait a minute before trying again.'
            }))
            return
        
        log(f"[WebSocket] EditConsumer received message: {text_data[:200]}")
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            log(f"[WebSocket] EditConsumer message type: {message_type}")

            if message_type == 'edit_request':
                log("[WebSocket] Starting edit process...")
                # Send acknowledgment first
                await self.send(text_data=json.dumps({
                    'type': 'processing',
                    'message': 'Edit process started'
                }))
                
                enhancement_task_id = text_data_json.get("enhancement_task_id", None)
                
                if enhancement_task_id:
                    cached_messages = cache.get(f"enhance_messages_{enhancement_task_id}")
                    if cached_messages:
                        self.messages = cached_messages
                        log(f"[WebSocket] Loaded messages from cache for enhancement_task_id: {enhancement_task_id}, messages count: {len(self.messages)}")
                    else:
                        log(f"[WebSocket] No cached messages found for enhancement_task_id: {enhancement_task_id}")
                
                # Run edit process and handle result in callback
                self.edit_task = asyncio.create_task(
                    self._run_edit_with_callback(text_data_json)
                )
            else:
                log(f"[WebSocket] Unknown message type received: {message_type}")
                await self.send(text_data=json.dumps({
                    'type': 'task_error',
                    'error': f'Unknown message type: {message_type}'
                }))
        except Exception as e:
            log(f"[WebSocket] EditConsumer error in receive: {e}")
            traceback.print_exc()
            await self.send(text_data=json.dumps({
                'type': 'task_error',
                'error': str(e)
            }))
    
    async def _run_edit_with_callback(self, data):
        """Wrapper that ensures errors are properly sent to client."""
        try:
            await self.run_edit(data)
        except asyncio.CancelledError:
            log("[WebSocket] Edit task was cancelled")
        except Exception as e:
            log(f"[WebSocket] Unhandled error in edit: {e}")
            traceback.print_exc()
            try:
                await self.send(text_data=json.dumps({
                    'type': 'task_error',
                    'error': str(e)
                }))
            except Exception:
                pass

    async def run_edit(self, data):
        """Run the edit process directly in the WebSocket consumer."""
        try:
            if data.get("edit_instructions", "") == "" :
                raise ValueError("Edit instructions cannot be empty.")
            
            # Import here to avoid circular imports at module load time
            from .edit import edit_prompt_async
            
            log(f"[WebSocket] Calling edit_prompt_async with instructions: {data.get('edit_instructions', '')[:50]}")
            
            enhancement_task_id = data.get("enhancement_task_id", None)
            enhancement_messages = self._get_enhancement_messages(enhancement_task_id)
            
            config = PromptConfig(
                model=os.getenv("MODEL", "gemini-3-flash-preview"),
                use_web_search=data.get('use_web_search', True),
                additional_context_query=data.get('additional_context_query', ''),
                ask_user_func=self.ask_user_question,
                target_model=data.get('target_model', 'gpt-5.1'),
                is_reasoning_native=data.get('is_reasoning_native', False),
                prompt_style=data.get('prompt_style', {}),
            )
            result = await edit_prompt_async(
                edit_instructions=data.get('edit_instructions', ''),
                current_prompt=data.get('current_prompt', ''),
                config=config,
                enhancement_messages=enhancement_messages
            )
        
            await self.send(text_data=json.dumps({
                'type': 'task_complete',
                'result': result
            }))
            log("[WebSocket] Sent task_complete to client")
        except Exception as e:
            log(f"[WebSocket] Edit error: {e}")
            traceback.print_exc()
            await self.send(text_data=json.dumps({
                'type': 'task_error',
                'error': str(e)
            }))


    async def ask_user_question(self, questions: str, timeout: int = 300) -> str:
        """Ask user a question and wait for answer via WebSocket."""
        self.answer_event.clear()
        self.pending_answer = None
        
        log(f"[WebSocket] Asking user question: {questions}")
        await self.send(text_data=json.dumps({
            'type': 'user_question',
            'questions': questions
        }))
        
        try:
            await asyncio.wait_for(self.answer_event.wait(), timeout=timeout)
            answer = self.pending_answer
            self.pending_answer = None
            log(f"[WebSocket] Got user answer: {answer}")
            return answer or ""
        except asyncio.TimeoutError:
            raise TimeoutError(f"User did not respond within {timeout} seconds")
    
    def _get_enhancement_messages(self, enhancement_task_id):
        """Helper to get enhancement messages from cache."""
        if enhancement_task_id:
            cached_messages = cache.get(f"enhance_messages_{enhancement_task_id}")
            if cached_messages:
                log(f"[WebSocket] Loaded messages from cache for enhancement_task_id: {enhancement_task_id}, messages count: {len(cached_messages)}")
                return cached_messages
            else:
                log(f"[WebSocket] No cached messages found for enhancement_task_id: {enhancement_task_id}")
        return []
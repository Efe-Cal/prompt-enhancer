import json
import asyncio
import os
import traceback
from channels.generic.websocket import AsyncWebsocketConsumer
from dotenv import load_dotenv

load_dotenv()


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

        print(f"[WebSocket] Client connecting to group: {self.room_group_name}")

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print(f"[WebSocket] Client connected and joined group: {self.room_group_name}")

    async def disconnect(self, close_code):
        print(f"[WebSocket] Client disconnecting from group: {self.room_group_name}")
        if self.enhancement_task and not self.enhancement_task.done():
            self.enhancement_task.cancel()
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        print(f"[WebSocket] Received message: {text_data[:200]}")
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            print(f"[WebSocket] Message type: {message_type}")

            if message_type == 'user_answer':
                answer = text_data_json.get('answer')
                self.pending_answer = answer
                self.answer_event.set()
                
                await self.send(text_data=json.dumps({
                    'type': 'answer_received',
                    'status': 'ok'
                }))

            elif message_type == 'enhance':
                print("[WebSocket] Starting enhancement...")
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
            print(f"[WebSocket] Error in receive: {e}")
            traceback.print_exc()

    async def _run_enhancement_with_callback(self, data):
        """Wrapper that ensures errors are properly sent to client."""
        try:
            await self.run_enhancement(data)
        except asyncio.CancelledError:
            print("[WebSocket] Enhancement task was cancelled")
        except Exception as e:
            print(f"[WebSocket] Unhandled error in enhancement: {e}")
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
            
            print(f"[WebSocket] Calling enhance_prompt_async with task: {data.get('task', '')[:50]}")
            
            result = await enhance_prompt_async(
                task=data.get('task', ''),
                lazy_prompt=data.get('lazy_prompt', ''),
                model=data.get('model') or os.getenv("MODEL", "gpt-4o"),
                use_web_search=data.get('use_web_search', True),
                additional_context_query=data.get('additional_context_query', ''),
                ask_user_func=self.ask_user_question
            )
            
            print(f"[WebSocket] Enhancement complete, result length: {len(result)}")
            
            await self.send(text_data=json.dumps({
                'type': 'task_complete',
                'result': result
            }))
            print("[WebSocket] Sent task_complete to client")
            
        except Exception as e:
            print(f"[WebSocket] Enhancement error: {e}")
            traceback.print_exc()
            await self.send(text_data=json.dumps({
                'type': 'task_error',
                'error': str(e)
            }))

    async def ask_user_question(self, question: str, timeout: int = 300) -> str:
        """Ask user a question and wait for answer via WebSocket."""
        self.pending_answer = None
        self.answer_event.clear()
        
        print(f"[WebSocket] Asking user question: {question}")
        await self.send(text_data=json.dumps({
            'type': 'user_question',
            'question': question
        }))
        
        try:
            await asyncio.wait_for(self.answer_event.wait(), timeout=timeout)
            print(f"[WebSocket] Got user answer: {self.pending_answer}")
            return self.pending_answer or ""
        except asyncio.TimeoutError:
            raise TimeoutError(f"User did not respond within {timeout} seconds")

    async def user_question(self, event):
        """Send user question to WebSocket (for group messages)."""
        await self.send(text_data=json.dumps({
            'type': 'user_question',
            'question': event['question']
        }))

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

import json
import time
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.cache import cache
from .enhance import enhance_prompt as enhance_prompt_sync


def ask_user_question(task_id: str, question: str, timeout: int = 300) -> str:
    """
    Ask the user a question via WebSocket and wait for the answer.
    
    Args:
        task_id: The task ID (used for WebSocket room)
        question: The question to ask the user
        timeout: Maximum time to wait for answer (seconds)
    
    Returns:
        The user's answer
    """
    channel_layer = get_channel_layer()
    
    if channel_layer is None:
        raise RuntimeError("Channel layer not configured! Check CHANNEL_LAYERS in settings.py")
    
    print(f"[ask_user_question] Sending question to group: enhance_{task_id}")
    print(f"[ask_user_question] Question: {question}")
    
    # Send question to WebSocket
    async_to_sync(channel_layer.group_send)(
        f'enhance_{task_id}',
        {
            'type': 'user_question',
            'question': question
        }
    )
    
    print(f"[ask_user_question] Message sent, waiting for answer...")
    
    # Poll for answer in cache
    cache_key = f'user_answer_{task_id}'
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        answer = cache.get(cache_key)
        if answer is not None:
            # Clear the cache key
            cache.delete(cache_key)
            return answer
        time.sleep(0.5)  # Poll every 500ms
    
    raise TimeoutError(f"User did not respond within {timeout} seconds")


@shared_task(bind=True)
def enhance_prompt_task(self, task_id: str, task: str, lazy_prompt: str, 
                        use_web_search: bool, additional_context_query: str, model: str):
    """
    Celery task that enhances a prompt.
    This task can ask the user questions during processing.
    
    DEMO: Uncomment the lines below to test asking user a question!
    """
    channel_layer = get_channel_layer()
    
    try:
        # ============================================================
        # DEMO: Uncomment these lines to test user question dialog!
        # ============================================================
        
        # user_preference = ask_user_question(
        #     task_id=task_id,
        #     question="What tone should the enhanced prompt have? (formal/casual/technical)"
        # )
        # print(f"User wants tone: {user_preference}")
        
        # ============================================================
        
        result = enhance_prompt_sync(
            task=task,
            lazy_prompt=lazy_prompt,
            model=model,
            use_web_search=use_web_search,
            additional_context_query=additional_context_query,
            task_id=task_id
        )
        
        # Send success to WebSocket
        async_to_sync(channel_layer.group_send)(
            f'enhance_{task_id}',
            {
                'type': 'task_complete',
                'result': result
            }
        )
        
        return {'status': 'success', 'result': result}
        
    except Exception as e:
        # Send error to WebSocket
        async_to_sync(channel_layer.group_send)(
            f'enhance_{task_id}',
            {
                'type': 'task_error',
                'error': str(e)
            }
        )
        
        raise


@shared_task(bind=True)
def enhance_prompt_with_user_input_task(self, task_id: str, task: str, lazy_prompt: str, 
                                        use_web_search: bool, additional_context_query: str, model: str):
    """
    Enhanced version that demonstrates asking user questions.
    This integrates with the LLM's tool calling mechanism.
    """
    channel_layer = get_channel_layer()
    
    try:
        # Here's where you'd integrate with your LLM tool calling
        # When the LLM calls a tool that needs user input, you call ask_user_question
        
        # Example of asking user a question:
        # user_answer = ask_user_question(
        #     task_id=task_id,
        #     question="What specific industry or use case should this prompt target?"
        # )
        
        # Then use the answer in your processing
        # For now, we'll use the standard enhance_prompt
        
        result = enhance_prompt_sync(
            task=task,
            lazy_prompt=lazy_prompt,
            model=model,
            use_web_search=use_web_search,
            additional_context_query=additional_context_query,
            task_id=task_id
        )
        
        # Send success to WebSocket
        async_to_sync(channel_layer.group_send)(
            f'enhance_{task_id}',
            {
                'type': 'task_complete',
                'result': result
            }
        )
        
        return {'status': 'success', 'result': result}
        
    except Exception as e:
        # Send error to WebSocket
        async_to_sync(channel_layer.group_send)(
            f'enhance_{task_id}',
            {
                'type': 'task_error',
                'error': str(e)
            }
        )
        
        raise

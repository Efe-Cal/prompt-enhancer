import os
import uuid
from dotenv import load_dotenv

from rest_framework.generics import GenericAPIView, CreateAPIView
from .models import SavedPrompt
from .serializers import EnhancePromptRequestSerializer, SavePromptSerializer
from rest_framework.response import Response

load_dotenv()


class EnhancePromptView(GenericAPIView):
    """
    Returns a task_id for the client to connect via WebSocket.
    The actual enhancement is triggered by sending an 'enhance' message through the WebSocket.
    """
    serializer_class = EnhancePromptRequestSerializer
    
    def post(self, request):
        data = request.data
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Use client-provided task_id or generate one
        task_id = data.get('task_id') or str(uuid.uuid4())

        return Response({
            'task_id': task_id,
            'status': 'ready',
            'message': 'Connect to WebSocket and send enhance message to start processing.'
        })


class SavePromptView(CreateAPIView):
    serializer_class = SavePromptSerializer
    
    def create(self, request):
        
        serialzer = self.get_serializer(data=request.data)
        serialzer.is_valid(raise_exception=True)
    
        task = serialzer.validated_data['task']
        lazy_prompt = serialzer.validated_data['lazy_prompt']
        enhanced_prompt = serialzer.validated_data['enhanced_prompt']
        
        SavedPrompt.objects.create(
            task=task,
            lazy_prompt=lazy_prompt,
            enhanced_prompt=enhanced_prompt
        )
            
        return Response({'status': 'Prompt saved successfully'})

    
class ListSavedPromptsView(GenericAPIView):
    def get(self, request):
        prompts = SavedPrompt.objects.all().order_by('-created_at')
        prompt_list = [
            {
                'id': prompt.id,
                'task': prompt.task,
                'lazy_prompt': prompt.lazy_prompt,
                'enhanced_prompt': prompt.enhanced_prompt,
                'created_at': prompt.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            for prompt in prompts
        ]
        return Response({'prompts': prompt_list})

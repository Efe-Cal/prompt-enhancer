import os
import uuid
from dotenv import load_dotenv

from rest_framework.generics import GenericAPIView, CreateAPIView
from .models import SavedPrompt
from .enhance import enhance_prompt
from .serializers import EnhancePromptRequestSerializer, SavePromptSerializer
from rest_framework.response import Response
from .tasks import enhance_prompt_task

load_dotenv()

class EnhancePromptView(GenericAPIView):
    serializer_class = EnhancePromptRequestSerializer
    
    def post(self, request):
        data = request.data
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        task = serializer.validated_data['task']
        lazy_prompt = serializer.validated_data['lazy_prompt']
        use_web_search = serializer.validated_data.get('use_web_search', False)
        additional_context_query = serializer.validated_data.get('additional_context_query', "")
        
        # Use client-provided task_id or generate one
        task_id = data.get('task_id') or str(uuid.uuid4())
        
        # Start Celery task asynchronously
        enhance_prompt_task.delay(
            task_id=task_id,
            task=task,
            lazy_prompt=lazy_prompt,
            use_web_search=use_web_search,
            additional_context_query=additional_context_query,
            model=os.getenv("MODEL", "gpt-5.1")
        )

        return Response({
            'task_id': task_id,
            'status': 'processing',
            'message': 'Task started. Connect to WebSocket for real-time updates.'
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
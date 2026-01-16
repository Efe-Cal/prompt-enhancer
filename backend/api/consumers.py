import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async


class EnhanceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.room_group_name = f'enhance_{self.task_id}'

        print(f"[WebSocket] Client connecting to group: {self.room_group_name}")

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print(f"[WebSocket] Client connected and joined group: {self.room_group_name}")

    async def disconnect(self, close_code):
        print(f"[WebSocket] Client disconnecting from group: {self.room_group_name}")
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')

        if message_type == 'user_answer':
            # Store the user's answer in cache/database
            answer = text_data_json.get('answer')
            await self.store_user_answer(self.task_id, answer)
            
            # Send acknowledgment
            await self.send(text_data=json.dumps({
                'type': 'answer_received',
                'status': 'ok'
            }))

    async def store_user_answer(self, task_id, answer):
        """Store user answer so Celery task can retrieve it"""
        from django.core.cache import cache
        await sync_to_async(cache.set)(f'user_answer_{task_id}', answer, timeout=300)  # 5 min timeout

    # Receive message from room group
    async def user_question(self, event):
        """Send user question to WebSocket"""
        question = event['question']
        print(f"[WebSocket] Received user_question event, forwarding to client: {question}")

        await self.send(text_data=json.dumps({
            'type': 'user_question',
            'question': question
        }))
        print(f"[WebSocket] Sent user_question to client")

    async def task_complete(self, event):
        """Send task completion to WebSocket"""
        result = event['result']

        await self.send(text_data=json.dumps({
            'type': 'task_complete',
            'result': result
        }))

    async def task_error(self, event):
        """Send task error to WebSocket"""
        error = event['error']

        await self.send(text_data=json.dumps({
            'type': 'task_error',
            'error': error
        }))

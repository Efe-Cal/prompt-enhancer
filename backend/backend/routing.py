from django.urls import re_path
from api import consumers

websocket_urlpatterns = [
    re_path(r'ws/enhance/(?P<task_id>[^/]+)/$', consumers.EnhanceConsumer.as_asgi()),
]

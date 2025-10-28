from django.urls import re_path
from . import consumers
from django.urls import path
from .consumers import ChatConsumer

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<username>\w+)/$', consumers.ChatConsumer.as_asgi()),
    path('ws/chat/admins/', ChatConsumer.as_asgi()),
]
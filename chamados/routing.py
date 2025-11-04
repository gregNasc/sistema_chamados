from django.urls import re_path, path
from .consumers import ChatConsumer

websocket_urlpatterns = [
    # Rota dinâmica por username
    re_path(r'ws/chat/(?P<username>\w+)/$', ChatConsumer.as_asgi()),
    ]

    # Rota fixa para admins

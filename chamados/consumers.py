import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Import local para evitar AppRegistryNotReady
        from .models import ChatMessage

        self.usuario_id = self.scope['url_route']['kwargs']['usuario_id']
        self.room_group_name = f'chat_{self.usuario_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        from .models import ChatMessage  # Import local aqui também

        data = json.loads(text_data)
        mensagem = data['mensagem']
        enviado_por_admin = data.get('admin', False)

        # Salva a mensagem no banco
        await database_sync_to_async(ChatMessage.objects.create)(
            usuario_id=self.usuario_id,
            texto=mensagem,
            enviado_por_admin=enviado_por_admin
        )

        # Envia a mensagem para todos do grupo
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'mensagem': mensagem,
                'admin': enviado_por_admin
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'mensagem': event['mensagem'],
            'admin': event['admin']
        }))

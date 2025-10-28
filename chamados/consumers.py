from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        self.usuario_nome = self.scope['url_route']['kwargs']['username']
        self.group_name = f'chat_user_{self.usuario_nome}'

        if self.scope["user"].is_staff:
            # Admin entra no grupo geral de admins
            await self.channel_layer.group_add("chat_admins", self.channel_name)
            print(f"✅ Admin conectado ao grupo geral de admins")
        else:
            # Usuário entra no próprio grupo
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            # Usuário também entra no grupo de admins para enviar mensagens
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            print(f"✅ Usuário conectado à sua sala e ao grupo de admins")

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await self.channel_layer.group_discard("chat_admins", self.channel_name)

    async def receive(self, text_data):
        from django.contrib.auth import get_user_model
        from .models import ChatMessage
        from asgiref.sync import sync_to_async

        data = json.loads(text_data)
        print(f"📥 Payload recebido: {data}")

        enviado_por_admin = self.scope["user"].is_staff
        mensagem = data.get('mensagem', '').strip()
        destinatario_username = data.get("destinatario_username", None)

        if not mensagem:
            return

        User = get_user_model()
        remetente_nome = self.scope["user"].get_full_name() or self.scope["user"].username

        try:
            if enviado_por_admin:
                if destinatario_username:
                    # Enviar para usuário específico
                    usuario_destino = await database_sync_to_async(User.objects.get)(username=destinatario_username)

                    await database_sync_to_async(ChatMessage.objects.create)(
                        usuario=usuario_destino,
                        texto=mensagem,
                        enviado_por_admin=True
                    )

                    await self.channel_layer.group_send(
                        f'chat_user_{destinatario_username}',
                        {
                            'type': 'chat_message',
                            'mensagem': mensagem,
                            'admin': True,
                            'remetente': remetente_nome,
                            'usuario_nome': remetente_nome,
                            'alert': False
                        }
                    )
                else:
                    # Enviar para todos usuários
                    usuarios = await database_sync_to_async(list)(User.objects.filter(is_staff=False))
                    for usuario in usuarios:
                        await database_sync_to_async(ChatMessage.objects.create)(
                            usuario=usuario,
                            texto=mensagem,
                            enviado_por_admin=True
                        )
                        await self.channel_layer.group_send(
                            f'chat_user_{usuario.username}',
                            {
                                'type': 'chat_message',
                                'mensagem': mensagem,
                                'admin': True,
                                'remetente': remetente_nome,
                                'usuario_nome': remetente_nome,
                                'alert': False
                            }
                        )
            else:
                # Usuário envia mensagem
                usuario = await database_sync_to_async(User.objects.get)(username=self.usuario_nome)
                await database_sync_to_async(ChatMessage.objects.create)(
                    usuario=usuario,
                    texto=mensagem,
                    enviado_por_admin=False
                )

                # Enviar para todos admins
                await self.channel_layer.group_send(
                    "chat_admins",
                    {
                        'type': 'chat_message',
                        'mensagem': mensagem,
                        'admin': False,
                        'remetente': remetente_nome,
                        'usuario_nome': remetente_nome,
                        'alert': True
                    }
                )

                # Enviar de volta para o próprio usuário
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'chat_message',
                        'mensagem': mensagem,
                        'admin': False,
                        'remetente': remetente_nome,
                        'usuario_nome': remetente_nome,
                        'alert': False
                    }
                )

        except User.DoesNotExist:
            print(f"⚠️ Usuário não encontrado: {destinatario_username or self.usuario_nome}")
        except Exception as e:
            print(f"❌ Erro ao processar mensagem: {str(e)}")

    async def chat_message(self, event):
        print(f" Enviando evento para cliente: {event}")
        await self.send(text_data=json.dumps({
            'mensagem': event['mensagem'],
            'admin': event['admin'],
            'remetente': event.get('remetente'),
            'usuario_nome': event.get('usuario_nome'),
            'alert': event.get('alert', False)
        }))
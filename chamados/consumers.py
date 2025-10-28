import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print(f"[CONNECT] Canal: {self.channel_name}, Usuário: {self.scope['user']}, URL: {self.scope['path']}")
        ...
        self.usuario_nome = self.scope['url_route']['kwargs']['username']
        self.group_name = f'chat_user_{self.usuario_nome}'

        if self.scope["user"].is_staff:
            # Admin entra no grupo de admins (para receber alertas)
            await self.channel_layer.group_add("chat_admins", self.channel_name)

            # E também no grupo do usuário específico (para conversar)
            if self.usuario_nome != self.scope["user"].username:
                await self.channel_layer.group_add(self.group_name, self.channel_name)
                print(f"✅ Admin conectado ao grupo do usuário {self.group_name}")
            else:
                print(f"⚠️ Admin conectou ao próprio chat ({self.group_name}) — sem interação de suporte")
        else:
            # Usuário entra apenas no próprio grupo
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            print(f"✅ Usuário conectado ao grupo {self.group_name}")

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        if self.scope["user"].is_staff:
            await self.channel_layer.group_discard("chat_admins", self.channel_name)
            if self.usuario_nome != self.scope["user"].username:
                await self.channel_layer.group_add(self.group_name, self.channel_name)

    async def receive(self, text_data):
        from django.contrib.auth import get_user_model
        from .models import ChatMessage

        data = json.loads(text_data)
        print(f"📥 Payload recebido: {data}")

        if self.scope["user"].is_staff and data.get("acao") == "entrar_no_chat":
            group_name = f"chat_user_{data['usuario']}"
            await self.channel_layer.group_add(group_name, self.channel_name)
            print(f"👂 Admin {self.scope['user'].username} escutando o grupo {group_name}")
            print(f"🔎 Enviando para grupo: chat_user_{'usuario'}")
            return  # encerra aqui, sem processar como mensagem normal

        mensagem = data.get('mensagem', '').strip()
        enviado_por_admin = data.get('admin', True)

        if not mensagem:
            return

        User = get_user_model()

        try:
            if enviado_por_admin:
                destinatario_username = data.get("destinatario_username") or getattr(self, "ultimo_remetente", None)
                print(f"📤 Admin {self.scope['user'].username} enviando mensagem para: {destinatario_username}")
                if not destinatario_username:
                    print("⚠️ Destinatário não definido")
                    return

                usuario_destino = await database_sync_to_async(User.objects.get)(username=destinatario_username)

                # Salvar mensagem no banco
                await database_sync_to_async(ChatMessage.objects.create)(
                    usuario=usuario_destino,
                    texto=mensagem,
                    enviado_por_admin=True
                )

                print(f"📤 Enviando mensagem para o grupo: chat_user_{destinatario_username}")

                await self.channel_layer.group_add(f'chat_user_{destinatario_username}', self.channel_name)
                # Enviar mensagem para destinatário
                await self.channel_layer.group_send(
                    f'chat_user_{destinatario_username}',
                    {
                        'type': 'chat_message',
                        'mensagem': mensagem,
                        'admin': True,
                        'remetente': self.scope["user"].get_full_name() or self.scope["user"].username,
                        'usuario_nome': self.scope["user"].get_full_name() or self.scope["user"].username,
                        'alert': False,  # usuário não recebe alerta
                    }
                )
            else:
                # Usuário enviando → admins
                usuario = await database_sync_to_async(User.objects.get)(username=self.usuario_nome)

                await database_sync_to_async(ChatMessage.objects.create)(
                    usuario=usuario,
                    texto=mensagem,
                    enviado_por_admin=False
                )

                # Enviar para admins
                await self.channel_layer.group_send(
                    "chat_admins",
                    {
                        'type': 'chat_message',
                        'mensagem': mensagem,
                        'admin': False,
                        'remetente': self.scope["user"].get_full_name() or self.scope["user"].username,
                        'usuario_nome': self.scope["user"].get_full_name() or self.scope["user"].username,
                        'alert': True  # alerta apenas para admins
                    }
                )

                # Enviar para o próprio usuário
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'chat_message',
                        'mensagem': mensagem,
                        'admin': False,
                        'remetente': self.scope["user"].get_full_name() or self.scope["user"].username,
                        'usuario_nome': self.scope["user"].get_full_name() or self.scope["user"].username,
                        'alert': False
                    }
                )
        except User.DoesNotExist:
            print(f"⚠️ Usuário não encontrado: {data.get('destinatario_username', self.usuario_nome)}")
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
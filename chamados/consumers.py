from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
import uuid


class ChatConsumer(AsyncWebsocketConsumer):
    admins_online = {}
    user_to_admin_channel = {}
    admin_to_user = {}

    async def connect(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        self.usuario_nome = self.scope['url_route']['kwargs']['username'].lower()
        self.group_name = f'chat_user_{self.usuario_nome}'
        self.is_admin = self.scope["user"].is_staff or getattr(self.scope["user"], 'papel', '').lower() == 'gestor'

        if self.is_admin:
            await self.channel_layer.group_add("chat_admins", self.channel_name)
            await self.channel_layer.group_add("chat_users", self.channel_name)
            print(f"Admin/Gestor '{self.usuario_nome}' conectado")

            self.scope["user"].is_online = True
            await database_sync_to_async(self.scope["user"].save)()

            nome_exibicao = (self.scope["user"].get_full_name() or self.scope["user"].username).split()[0]
            self.__class__.admins_online[self.channel_name] = nome_exibicao

            # Notifica todos
            await self.channel_layer.group_send("chat_admins", {
                "type": "admin_status",
                "username": nome_exibicao,
                "online": True,
                "channel": self.channel_name
            })
            await self.channel_layer.group_send("chat_users", {
                "type": "admin_status",
                "username": nome_exibicao,
                "online": True,
                "channel": self.channel_name
            })

        else:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.channel_layer.group_add("chat_users", self.channel_name)
            print(f"Usuário '{self.usuario_nome}' conectado")

        await self.accept()

        if not self.is_admin:
            await self.send_welcome_and_list()

    async def disconnect(self, close_code):
        if self.is_admin:
            nome = self.__class__.admins_online.pop(self.channel_name, None)
            if nome:
                self.scope["user"].is_online = False
                await database_sync_to_async(self.scope["user"].save)()
                await self.channel_layer.group_send("chat_admins", {
                    "type": "admin_status",
                    "username": nome,
                    "online": False
                })
                await self.channel_layer.group_send("chat_users", {
                    "type": "admin_status",
                    "username": nome,
                    "online": False
                })

        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await self.channel_layer.group_discard("chat_admins", self.channel_name)
        await self.channel_layer.group_discard("chat_users", self.channel_name)

    async def receive(self, text_data):
        from .models import ChatMessage
        from django.contrib.auth import get_user_model
        User = get_user_model()

        data = json.loads(text_data)
        message_id = str(uuid.uuid4())  # ID único para deduplicação

        # === SELEÇÃO DE ATENDENTE ===
        if data.get("type") == "select_attendant" and not self.is_admin:
            admin_channel = data.get("admin_channel")
            if admin_channel in self.__class__.admins_online:
                self.__class__.user_to_admin_channel[self.channel_name] = admin_channel
                self.__class__.admin_to_user[admin_channel] = self.usuario_nome

                await self.channel_layer.send(admin_channel, {
                    "type": "user_selected_you",
                    "username": self.usuario_nome.capitalize(),
                    "user_channel": self.channel_name
                })
            return

        # === MENSAGEM DIRETA DO ADMIN/GESTOR ===
        if self.is_admin and data.get("type") == "direct_message":
            mensagem = data.get("mensagem", "").strip()
            if not mensagem:
                return

            usuario_nome = self.__class__.admin_to_user.get(self.channel_name)
            if not usuario_nome:
                print(f"[ERRO] Admin '{self.usuario_nome}' não vinculado a usuário.")
                return

            try:
                usuario = await database_sync_to_async(User.objects.get)(username=usuario_nome)
            except User.DoesNotExist:
                return

            await database_sync_to_async(ChatMessage.objects.create)(
                usuario=usuario,
                texto=mensagem,
                enviado_por_admin=True
            )

            remetente_nome = self.scope["user"].get_full_name() or self.scope["user"].username

            payload = {
                "type": "chat_message",
                "mensagem": mensagem,
                "admin": True,
                "remetente": remetente_nome,
                "usuario_nome": usuario_nome,
                "message_id": message_id
            }

            # 1. Envia para o usuário
            await self.channel_layer.group_send(f"chat_user_{usuario_nome}", payload)

            # 2. Envia para o próprio admin (sincroniza abas)
            await self.channel_layer.send(self.channel_name, payload)

            # NÃO envia para chat_admins → evita duplicação
            return

        # === MENSAGEM DO USUÁRIO COMUM ===
        if data.get('mensagem') and not self.is_admin:
            mensagem = data['mensagem'].strip()
            if not mensagem:
                return

            remetente_nome = self.scope["user"].get_full_name() or self.scope["user"].username

            try:
                usuario = await database_sync_to_async(User.objects.get)(username=self.usuario_nome)
                await database_sync_to_async(ChatMessage.objects.create)(
                    usuario=usuario, texto=mensagem, enviado_por_admin=False
                )
            except User.DoesNotExist:
                return

            admin_channel = self.__class__.user_to_admin_channel.get(self.channel_name)
            payload = {
                "type": "chat_message",
                "mensagem": mensagem,
                "admin": False,
                "remetente": remetente_nome,
                "usuario_nome": self.usuario_nome,
                "alert": True,
                "message_id": message_id
            }

            if admin_channel and admin_channel in self.__class__.admins_online:
                await self.channel_layer.send(admin_channel, payload)
                self.__class__.admin_to_user[admin_channel] = self.usuario_nome
            else:
                await self.channel_layer.group_send("chat_admins", payload)

            # Eco para o usuário
            await self.channel_layer.group_send(self.group_name, {
                **payload,
                "alert": False  # usuário não precisa de alerta
            })
            return

    async def send_welcome_and_list(self):
        nome = self.usuario_nome.capitalize()
        await self.send(text_data=json.dumps({
            'mensagem': f"Olá, {nome}! Como está seu dia? Aguarde um momento...",
            'remetente': 'Sistema'
        }))
        await self.enviar_lista_admins()

    async def enviar_lista_admins(self):
        lista = [
            {"nome": nome, "channel": channel}
            for channel, nome in self.__class__.admins_online.items()
        ]
        await self.send(text_data=json.dumps({
            "type": "admins_online_list",
            "admins": lista
        }))

    # === HANDLERS DE EVENTOS ===
    async def admin_status(self, event):
        await self.send(text_data=json.dumps({
            "type": "admin_status",
            "username": event["username"],
            "online": event["online"],
            "channel": event.get("channel")
        }))

    async def user_selected_you(self, event):
        await self.send(text_data=json.dumps({
            "type": "user_selected_you",
            "username": event["username"],
            "user_channel": event["user_channel"]
        }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'mensagem': event['mensagem'],
            'admin': event['admin'],
            'remetente': event.get('remetente'),
            'usuario_nome': event.get('usuario_nome'),
            'alert': event.get('alert', False),
            'message_id': event.get('message_id')
        }))
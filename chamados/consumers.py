from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Normaliza o nome do usuário
        self.usuario_nome = self.scope['url_route']['kwargs']['username'].lower()
        self.group_name = f'chat_user_{self.usuario_nome}'

        # Verifica se é admin (staff ou gestor)
        self.is_admin = self.scope["user"].is_staff

        if self.is_admin:
            # Admin/Gestor entra no grupo geral de admins
            await self.channel_layer.group_add("chat_admins", self.channel_name)
            print(f"✅ Admin/Gestor conectado ao grupo geral de admins")
        else:
            # Usuário entra no próprio grupo
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            print(f"✅ Usuário conectado à sua sala privada: {self.usuario_nome}")

        # Aceita a conexão WebSocket
        await self.accept()

        # 🔄 Mensagem automática para o usuário (somente quando não for admin/gestor)
        if not self.is_admin:
            nome_formatado = self.usuario_nome.capitalize()
            await self.send(text_data=json.dumps({
                'mensagem': (
                    f"🔄 Olá, {nome_formatado}! 😃\n\n"
                    "Como está seu dia hoje? Aguarda só um pouquinho que já vamos te atender.\n\n"
                    "Para agilizar seu atendimento, poderia nos contar resumidamente o motivo do seu contato? 🚀"
                ),
                'remetente': 'Sistema'
            }))

    async def disconnect(self, close_code):
        # remover dos grupos
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await self.channel_layer.group_discard("chat_admins", self.channel_name)

    async def receive(self, text_data):
        from django.contrib.auth import get_user_model
        from .models import ChatMessage
        from asgiref.sync import sync_to_async

        data = json.loads(text_data)
        print(f"📥 Payload recebido: {data}")

        enviado_por_admin = data.get('admin', False)
        mensagem = data.get('mensagem', '').strip()
        destinatario_username = data.get("destinatario_username", "")

        if not mensagem:
            return

        User = get_user_model()
        remetente_nome = self.scope["user"].get_full_name() or self.scope["user"].username

        try:
            if enviado_por_admin:
                # ADMIN enviando — requer destinatario_username para envio privado
                if destinatario_username:
                    # Nome do grupo (sempre lowercase)
                    group_name = f"chat_user_{destinatario_username.lower()}"

                    # Recupera usuário de destino e nome original para exibição
                    usuario_destino = await database_sync_to_async(User.objects.get)(
                        username__iexact=destinatario_username
                    )
                    usuario_exibicao = usuario_destino.get_full_name() or usuario_destino.username

                    # Salva mensagem (enviado_por_admin=True)
                    await database_sync_to_async(ChatMessage.objects.create)(
                        usuario=usuario_destino,
                        texto=mensagem,
                        enviado_por_admin=True
                    )

                    print(f"📤 Enviando para grupo: {group_name}")

                    # Envia para o usuário destinatário
                    await self.channel_layer.group_send(
                        group_name,
                        {
                            'type': 'chat_message',
                            'mensagem': mensagem,
                            'admin': True,
                            'remetente': remetente_nome,
                            'usuario_nome': usuario_exibicao,  # nome original para o frontend
                            'alert': False
                        }
                    )

                    # Eco para o admin na aba correta
                    await self.channel_layer.group_send(
                        "chat_admins",
                        {
                            'type': 'chat_message',
                            'mensagem': mensagem,
                            'admin': True,
                            'remetente': remetente_nome,
                            'usuario_nome': usuario_exibicao,
                            'alert': False
                        }
                    )

                else:
                    # Admin sem destinatário: broadcast para todos os usuários
                    usuarios = await database_sync_to_async(list)(User.objects.filter(is_staff=False))
                    for usuario in usuarios:
                        usuario_exibicao = usuario.get_full_name() or usuario.username
                        await database_sync_to_async(ChatMessage.objects.create)(
                            usuario=usuario,
                            texto=mensagem,
                            enviado_por_admin=True
                        )
                        await self.channel_layer.group_send(
                            f'chat_user_{usuario.username.lower()}',
                            {
                                'type': 'chat_message',
                                'mensagem': mensagem,
                                'admin': True,
                                'remetente': remetente_nome,
                                'usuario_nome': usuario_exibicao,
                                'alert': False
                            }
                        )
            else:
                # Usuário enviando mensagem → admins
                usuario = await database_sync_to_async(User.objects.get)(username=self.usuario_nome)
                await database_sync_to_async(ChatMessage.objects.create)(
                    usuario=usuario,
                    texto=mensagem,
                    enviado_por_admin=False
                )

                # Envia para admins
                await self.channel_layer.group_send(
                    "chat_admins",
                    {
                        'type': 'chat_message',
                        'mensagem': mensagem,
                        'admin': False,
                        'remetente': remetente_nome,
                        'usuario_nome': self.usuario_nome,
                        'alert': True
                    }
                )

                # Eco para o próprio usuário
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'chat_message',
                        'mensagem': mensagem,
                        'admin': False,
                        'remetente': remetente_nome,
                        'usuario_nome': self.usuario_nome,
                        'alert': False
                    }
                )

        except User.DoesNotExist:
            print(f"⚠️ Usuário não encontrado: {destinatario_username or self.usuario_nome}")
        except Exception as e:
            print(f"❌ Erro ao processar mensagem: {str(e)}")

    async def chat_message(self, event):
        # evento enviado pelas group_send
        print(f" Enviando evento para cliente: {event}")
        await self.send(text_data=json.dumps({
            'mensagem': event['mensagem'],
            'admin': event['admin'],
            'remetente': event.get('remetente'),
            'usuario_nome': event.get('usuario_nome'),
            'alert': event.get('alert', False)
        }))

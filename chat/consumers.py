import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Message, MessageReaction
from chatrooms.models import Chatroom, ChatroomMessage, ChatroomMessageReaction


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        self.username = self.user.username
        self.user_group_name = f'user_{self.username}'

        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )

        if hasattr(self, 'chatroom_group_name'):
            await self.channel_layer.group_discard(
                self.chatroom_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', '')

        if message_type == 'authentication':
            if 'chatroom_id' in data:
                await self.join_chatroom(data['chatroom_id'])

        elif message_type == 'message':
            if 'chatroom_id' in data:
                await self.handle_chatroom_message(data)
            else:
                await self.handle_private_message(data)

        elif message_type == 'reaction':
            if 'chatroom_id' in data:
                await self.handle_chatroom_reaction(data)
            else:
                await self.handle_private_reaction(data)

    async def join_chatroom(self, chatroom_id):
        self.chatroom_id = chatroom_id
        self.chatroom_group_name = f'chatroom_{chatroom_id}'

        await self.channel_layer.group_add(
            self.chatroom_group_name,
            self.channel_name
        )

    @database_sync_to_async
    def save_private_message(self, data):
        recipient_username = data['recipient']
        content = data['message']

        try:
            recipient = User.objects.get(username=recipient_username)
            message = Message.objects.create(
                sender=self.user,
                recipient=recipient,
                content=content,
                image=data.get('image_url')
            )
            return message
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def save_chatroom_message(self, data):
        chatroom_id = data['chatroom_id']
        content = data['message']
        image_url = data.get('image_url')

        try:
            chatroom = Chatroom.objects.get(id=chatroom_id)
            if chatroom.members.filter(id=self.user.id).exists():
                message = ChatroomMessage.objects.create(
                    chatroom=chatroom,
                    user=self.user,
                    content=content
                )

                if image_url:
                    if image_url.startswith('/media/'):
                        image_path = image_url[7:]

                        if image_path:
                            try:
                                from django.core.files.storage import default_storage
                                if default_storage.exists(image_path):
                                    message.image = image_path
                                    message.save()
                            except Exception as e:
                                print(f"Error setting image on message: {str(e)}")

                return message
            return None
        except Chatroom.DoesNotExist:
            return None

    async def handle_chatroom_message(self, data):
        message = await self.save_chatroom_message(data)
        if not message:
            return

        image_url = None
        if message.image:
            try:
                image_url = message.image.url
                if not image_url.startswith('/media/'):
                    image_url = f'/media/{message.image.name}'
                elif image_url.startswith('/media/media/'):
                    image_url = image_url.replace('/media/media/', '/media/')
            except Exception as e:
                print(f"Error preparing image URL: {str(e)}")

        await self.channel_layer.group_send(
            self.chatroom_group_name,
            {
                'type': 'chatroom_message',
                'message': {
                    'id': message.id,
                    'sender': self.username,
                    'chatroom_id': message.chatroom.id,
                    'message': message.content,
                    'image_url': image_url,
                    'timestamp': message.sent_at.isoformat(),
                    'type': 'message'
                }
            }
        )

    @database_sync_to_async
    def save_private_reaction(self, data):
        message_id = data['message_id']
        reaction_type = data['reaction_type']

        try:
            message = Message.objects.get(id=message_id)
            reaction, created = MessageReaction.objects.update_or_create(
                message=message,
                user=self.user,
                defaults={'reaction_type': reaction_type}
            )
            return message, reaction
        except Message.DoesNotExist:
            return None, None

    @database_sync_to_async
    def save_chatroom_reaction(self, data):
        message_id = data['message_id']
        reaction_type = data['reaction_type']

        try:
            message = ChatroomMessage.objects.get(id=message_id)
            reaction, created = ChatroomMessageReaction.objects.update_or_create(
                message=message,
                user=self.user,
                defaults={'reaction_type': reaction_type}
            )
            return message, reaction, message.chatroom.id
        except ChatroomMessage.DoesNotExist:
            return None, None, None

    async def handle_private_message(self, data):
        message = await self.save_private_message(data)
        if not message:
            return

        recipient_username = data['recipient']

        await self.channel_layer.group_send(
            f'user_{recipient_username}',
            {
                'type': 'chat_message',
                'message': {
                    'id': message.id,
                    'sender': self.username,
                    'recipient': recipient_username,
                    'message': message.content,
                    'image_url': message.image.url if message.image else None,
                    'timestamp': message.timestamp.isoformat(),
                    'type': 'message'
                }
            }
        )

    async def handle_private_reaction(self, data):
        message, reaction = await self.save_private_reaction(data)
        if not message:
            return

        recipient_username = message.recipient.username if message.sender == self.user else message.sender.username

        await self.channel_layer.group_send(
            f'user_{recipient_username}',
            {
                'type': 'chat_reaction',
                'reaction': {
                    'message_id': message.id,
                    'reaction_type': reaction.reaction_type,
                    'sender': self.username,
                    'type': 'reaction'
                }
            }
        )

    async def handle_chatroom_reaction(self, data):
        message, reaction, chatroom_id = await self.save_chatroom_reaction(data)
        if not message:
            return

        await self.channel_layer.group_send(
            self.chatroom_group_name,
            {
                'type': 'chatroom_reaction',
                'reaction': {
                    'message_id': message.id,
                    'reaction_type': reaction.reaction_type,
                    'sender': self.username,
                    'chatroom_id': chatroom_id,
                    'type': 'reaction'
                }
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))

    async def chatroom_message(self, event):
        await self.send(text_data=json.dumps(event['message']))

    async def chat_reaction(self, event):
        await self.send(text_data=json.dumps(event['reaction']))

    async def chatroom_reaction(self, event):
        await self.send(text_data=json.dumps(event['reaction']))
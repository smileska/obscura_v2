import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from chat.models import Message, MessageReaction
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
        print(f"WebSocket connected for user: {self.username}")

    async def disconnect(self, close_code):
        print(f"WebSocket disconnected for user: {getattr(self, 'username', 'unknown')}")

        if hasattr(self, 'user_group_name'):
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
        try:
            data = json.loads(text_data)
            message_type = data.get('type', '')
            print(f"Received message type: {message_type}, data: {data}")

            if message_type == 'authentication':
                print(f"Authentication received for user: {self.username}")
                if 'chatroom_id' in data:
                    await self.join_chatroom(data['chatroom_id'])

            elif message_type == 'message':
                if 'chatroom_id' in data:
                    await self.handle_chatroom_message(data)
                elif 'recipient' in data:
                    await self.handle_private_message(data)
                else:
                    print("ERROR: Message type 'message' without chatroom_id or recipient")

            elif message_type == 'reaction':
                if 'chatroom_id' in data:
                    await self.handle_chatroom_reaction(data)
                else:
                    await self.handle_private_reaction(data)

        except Exception as e:
            print(f"Error in receive: {e}")
            import traceback
            traceback.print_exc()

    async def join_chatroom(self, chatroom_id):
        self.chatroom_id = chatroom_id
        self.chatroom_group_name = f'chatroom_{chatroom_id}'

        await self.channel_layer.group_add(
            self.chatroom_group_name,
            self.channel_name
        )
        print(f"User {self.username} joined chatroom group: {self.chatroom_group_name}")

    @database_sync_to_async
    def save_private_message(self, data):
        recipient_username = data.get('recipient')
        content = data.get('message', '')

        try:
            recipient = User.objects.get(username=recipient_username)
            message = Message.objects.create(
                sender=self.user,
                recipient=recipient,
                content=content
            )

            image_url = data.get('image_url')
            if image_url and image_url.startswith('/media/'):
                image_path = image_url[7:]
                if image_path:
                    try:
                        from django.core.files.storage import default_storage
                        if default_storage.exists(image_path):
                            message.image = image_path
                            message.save()
                            print(f"Image saved to message: {image_path}")
                    except Exception as e:
                        print(f"Error saving image to message: {e}")

            print(f"Saved private message: {message.id} from {self.user.username} to {recipient_username}")
            return message
        except User.DoesNotExist:
            print(f"ERROR: Recipient user '{recipient_username}' not found")
            return None
        except Exception as e:
            print(f"Error saving private message: {e}")
            return None

    async def handle_private_message(self, data):
        print(f"Handling private message: {data}")
        message = await self.save_private_message(data)
        if not message:
            print("Failed to save private message")
            return

        recipient_username = data['recipient']

        image_url = None
        if message.image:
            try:
                image_url = message.image.url
                print(f"Message image URL: {image_url}")
            except Exception as e:
                print(f"Error getting image URL: {e}")
                from django.conf import settings
                if message.image.name:
                    image_url = f"{settings.MEDIA_URL}{message.image.name}"
                    print(f"Fallback image URL: {image_url}")

        message_data = {
            'id': message.id,
            'sender': self.username,
            'recipient': recipient_username,
            'message': message.content,
            'image_url': image_url,
            'timestamp': message.timestamp.isoformat(),
            'type': 'message'
        }

        print(f"Sending message to groups: user_{recipient_username} and {self.user_group_name}")
        print(f"Message data: {message_data}")

        await self.channel_layer.group_send(
            f'user_{recipient_username}',
            {
                'type': 'chat_message',
                'message': message_data
            }
        )

        await self.channel_layer.group_send(
            self.user_group_name,
            {
                'type': 'chat_message',
                'message': message_data
            }
        )

    @database_sync_to_async
    def save_chatroom_message(self, data):
        chatroom_id = data.get('chatroom_id')
        content = data.get('message', '')
        image_url = data.get('image_url')

        try:
            chatroom = Chatroom.objects.get(id=chatroom_id)
            if chatroom.members.filter(id=self.user.id).exists():
                message = ChatroomMessage.objects.create(
                    chatroom=chatroom,
                    user=self.user,
                    content=content
                )

                if image_url and image_url.startswith('/media/'):
                    image_path = image_url[7:]
                    if image_path:
                        try:
                            from django.core.files.storage import default_storage
                            if default_storage.exists(image_path):
                                message.image = image_path
                                message.save()
                                print(f"Image saved to chatroom message: {image_path}")
                        except Exception as e:
                            print(f"Error saving image to chatroom message: {e}")

                return message
            return None
        except Exception as e:
            print(f"Error saving chatroom message: {e}")
            return None

    async def handle_chatroom_message(self, data):
        message = await self.save_chatroom_message(data)
        if not message:
            return

        image_url = None
        if message.image:
            try:
                image_url = message.image.url
                print(f"Chatroom message image URL: {image_url}")
            except Exception as e:
                print(f"Error getting chatroom image URL: {e}")
                from django.conf import settings
                if message.image.name:
                    image_url = f"{settings.MEDIA_URL}{message.image.name}"
                    print(f"Fallback chatroom image URL: {image_url}")

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
                    'sent_at': message.sent_at.isoformat(),
                    'type': 'message'
                }
            }
        )

    @database_sync_to_async
    def save_private_reaction(self, data):
        message_id = data.get('message_id')
        reaction_type = data.get('reaction_type')

        try:
            message = Message.objects.get(id=message_id)
            if message.sender == self.user or message.recipient == self.user:
                reaction, created = MessageReaction.objects.update_or_create(
                    message=message,
                    user=self.user,
                    defaults={'reaction_type': reaction_type}
                )
                return message, reaction
            return None, None
        except:
            return None, None

    @database_sync_to_async
    def save_chatroom_reaction(self, data):
        message_id = data.get('message_id')
        reaction_type = data.get('reaction_type')

        try:
            message = ChatroomMessage.objects.get(id=message_id)
            reaction, created = ChatroomMessageReaction.objects.update_or_create(
                message=message,
                user=self.user,
                defaults={'reaction_type': reaction_type}
            )
            return message, reaction, message.chatroom.id
        except:
            return None, None, None

    async def handle_private_reaction(self, data):
        message, reaction = await self.save_private_reaction(data)
        if not message:
            return
        other_user = message.recipient if message.sender == self.user else message.sender

        reaction_data = {
            'message_id': message.id,
            'reaction_type': reaction.reaction_type,
            'sender': self.username,
            'type': 'reaction'
        }
        await self.channel_layer.group_send(
            f'user_{other_user.username}',
            {
                'type': 'chat_reaction',
                'reaction': reaction_data
            }
        )

        await self.channel_layer.group_send(
            self.user_group_name,
            {
                'type': 'chat_reaction',
                'reaction': reaction_data
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
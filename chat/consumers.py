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
            print(f"Rejecting connection for unauthenticated user")
            await self.close()
            return

        self.username = self.user.username
        self.user_group_name = f'user_{self.username}'

        print(f"User {self.username} connected, adding to group {self.user_group_name}")

        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        await self.accept()
        print(f"Connection accepted for user {self.username}")

    async def disconnect(self, close_code):
        print(f"User {self.username if hasattr(self, 'username') else 'unknown'} disconnected with code {close_code}")

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

            print(f"Received {message_type} message from {self.username}: {data}")

            if message_type == 'authentication':
                if 'chatroom_id' in data:
                    await self.join_chatroom(data['chatroom_id'])
                    print(f"User {self.username} authenticated and joined chatroom {data['chatroom_id']}")
                else:
                    print(f"User {self.username} authenticated for private messages")

            elif message_type == 'message':
                if 'chatroom_id' in data:
                    print(f"Handling chatroom message from {self.username}")
                    await self.handle_chatroom_message(data)
                else:
                    print(f"Handling private message from {self.username} to {data.get('recipient', 'unknown')}")
                    await self.handle_private_message(data)

            elif message_type == 'reaction':
                if 'chatroom_id' in data:
                    await self.handle_chatroom_reaction(data)
                else:
                    await self.handle_private_reaction(data)
        except json.JSONDecodeError:
            print(f"Invalid JSON received: {text_data}")
        except Exception as e:
            print(f"Error processing message: {e}")

    async def join_chatroom(self, chatroom_id):
        self.chatroom_id = chatroom_id
        self.chatroom_group_name = f'chatroom_{chatroom_id}'

        await self.channel_layer.group_add(
            self.chatroom_group_name,
            self.channel_name
        )

    @database_sync_to_async
    def save_private_message(self, data):
        try:
            recipient_username = data.get('recipient')
            content = data.get('message', '')

            if not recipient_username:
                print(f"No recipient specified in message data: {data}")
                return None

            try:
                recipient = User.objects.get(username=recipient_username)

                image_url = data.get('image_url')
                image = None

                if image_url and image_url.startswith('/media/'):
                    image_path = image_url[7:]
                    if image_path:
                        try:
                            from django.core.files.storage import default_storage
                            if default_storage.exists(image_path):
                                message = Message.objects.create(
                                    sender=self.user,
                                    recipient=recipient,
                                    content=content
                                )
                                message.image = image_path
                                message.save()
                                return message
                        except Exception as e:
                            print(f"Error setting image on message: {str(e)}")

                message = Message.objects.create(
                    sender=self.user,
                    recipient=recipient,
                    content=content
                )
                return message

            except User.DoesNotExist:
                print(f"Recipient user {recipient_username} does not exist")
                return None

        except Exception as e:
            print(f"Error saving private message: {str(e)}")
            return None

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

    @database_sync_to_async
    def get_private_reaction_data(self, data):
        message_id = data.get('message_id')
        reaction_type = data.get('reaction_type')

        try:
            message = Message.objects.get(id=message_id)
            return {
                'message': message,
                'recipient_username': message.recipient.username if message.sender == self.user else message.sender.username
            }
        except Message.DoesNotExist:
            return None

    @database_sync_to_async
    def save_private_reaction(self, message_id, reaction_type):
        try:
            message = Message.objects.get(id=message_id)
            reaction, created = MessageReaction.objects.update_or_create(
                message=message,
                user=self.user,
                defaults={'reaction_type': reaction_type}
            )
            return True
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def get_chatroom_reaction_data(self, data):
        message_id = data.get('message_id')

        try:
            message = ChatroomMessage.objects.get(id=message_id)
            return {
                'message': message,
                'chatroom_id': message.chatroom.id
            }
        except ChatroomMessage.DoesNotExist:
            return None

    @database_sync_to_async
    def save_chatroom_reaction(self, message_id, reaction_type):
        try:
            message = ChatroomMessage.objects.get(id=message_id)
            reaction, created = ChatroomMessageReaction.objects.update_or_create(
                message=message,
                user=self.user,
                defaults={'reaction_type': reaction_type}
            )
            return True
        except ChatroomMessage.DoesNotExist:
            return False

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

    async def handle_private_reaction(self, data):
        message_id = data.get('message_id')
        reaction_type = data.get('reaction_type')

        reaction_data = await self.get_private_reaction_data(data)
        if not reaction_data:
            return

        message = reaction_data['message']
        recipient_username = reaction_data['recipient_username']

        success = await self.save_private_reaction(message_id, reaction_type)
        if not success:
            return

        await self.channel_layer.group_send(
            f'user_{recipient_username}',
            {
                'type': 'chat_reaction',
                'reaction': {
                    'message_id': message.id,
                    'reaction_type': reaction_type,
                    'sender': self.username,
                    'type': 'reaction'
                }
            }
        )

    async def handle_chatroom_reaction(self, data):
        message_id = data.get('message_id')
        reaction_type = data.get('reaction_type')

        reaction_data = await self.get_chatroom_reaction_data(data)
        if not reaction_data:
            return

        message = reaction_data['message']
        chatroom_id = reaction_data['chatroom_id']

        success = await self.save_chatroom_reaction(message_id, reaction_type)
        if not success:
            return

        await self.channel_layer.group_send(
            self.chatroom_group_name,
            {
                'type': 'chatroom_reaction',
                'reaction': {
                    'message_id': message.id,
                    'reaction_type': reaction_type,
                    'sender': self.username,
                    'chatroom_id': chatroom_id,
                    'type': 'reaction'
                }
            }
        )

    async def handle_private_message(self, data):
        try:
            if 'recipient' not in data or not data.get('message', '') and not data.get('image_url'):
                print(f"Missing required fields in message data: {data}")
                return

            message = await self.save_private_message(data)
            if not message:
                print(f"Failed to save message: {data}")
                return

            recipient_username = data['recipient']

            try:
                image_url = message.image.url if message.image else None
            except Exception as e:
                print(f"Error getting image URL: {e}")
                image_url = None

            message_data = {
                'id': message.id,
                'sender': self.username,
                'recipient': recipient_username,
                'message': message.content,
                'image_url': image_url,
                'timestamp': message.timestamp.isoformat(),
                'type': 'message'
            }

            print(f"Sending message to recipient {recipient_username}: {message_data}")

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

            print(f"Message sent from {self.username} to {recipient_username}")

        except Exception as e:
            print(f"Error in handle_private_message: {e}")

    async def chat_message(self, event):
        print(f"Sending chat message to client: {event['message']}")
        await self.send(text_data=json.dumps(event['message']))

    async def chatroom_message(self, event):
        await self.send(text_data=json.dumps(event['message']))

    async def chat_reaction(self, event):
        await self.send(text_data=json.dumps(event['reaction']))

    async def chatroom_reaction(self, event):
        await self.send(text_data=json.dumps(event['reaction']))
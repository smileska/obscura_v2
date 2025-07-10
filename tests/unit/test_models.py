import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from accounts.models import Profile
from chat.models import Message, MessageReaction
from chatrooms.models import Chatroom, ChatroomUser, ChatroomMessage


@pytest.mark.django_db
class TestUserModel:

    def test_user_creation(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
        assert user.is_active
        assert not user.is_staff
        assert not user.is_superuser

    def test_profile_auto_creation(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert hasattr(user, 'profile')
        assert user.profile.status == 'Offline'
        assert not user.profile.is_verified
        assert user.profile.user == user

    def test_user_uniqueness(self):
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username='testuser',
                email='different@example.com',
                password='testpass123'
            )

    def test_profile_status_update(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        user.profile.update_status('Online')
        assert user.profile.status == 'Online'

        user.profile.update_status('Offline')
        assert user.profile.status == 'Offline'


@pytest.mark.django_db
class TestMessageModel:

    def test_message_creation(self, multiple_users):
        sender = multiple_users[0]
        recipient = multiple_users[1]

        message = Message.objects.create(
            sender=sender,
            recipient=recipient,
            content='Test message'
        )

        assert message.sender == sender
        assert message.recipient == recipient
        assert message.content == 'Test message'
        assert message.timestamp is not None
        assert str(message) == f"{sender.username} to {recipient.username}: Test message"

    def test_message_ordering(self, multiple_users):
        sender = multiple_users[0]
        recipient = multiple_users[1]

        message1 = Message.objects.create(
            sender=sender,
            recipient=recipient,
            content='First message'
        )

        message2 = Message.objects.create(
            sender=sender,
            recipient=recipient,
            content='Second message'
        )

        messages = Message.objects.all()
        assert messages[0] == message1
        assert messages[1] == message2

    def test_message_reactions(self, multiple_users):
        sender = multiple_users[0]
        recipient = multiple_users[1]

        message = Message.objects.create(
            sender=sender,
            recipient=recipient,
            content='Test message'
        )

        reaction = MessageReaction.objects.create(
            message=message,
            user=recipient,
            reaction_type=1
        )

        assert reaction.message == message
        assert reaction.user == recipient
        assert reaction.reaction_type == 1
        assert reaction.created_at is not None

        with pytest.raises(IntegrityError):
            MessageReaction.objects.create(
                message=message,
                user=recipient,
                reaction_type=2
            )


@pytest.mark.django_db
class TestChatroomModel:

    def test_chatroom_creation(self, user):
        chatroom = Chatroom.objects.create(
            name='Test Chatroom',
            owner=user
        )

        assert chatroom.name == 'Test Chatroom'
        assert chatroom.owner == user
        assert chatroom.created_at is not None
        assert str(chatroom) == 'Test Chatroom'

    def test_chatroom_membership(self, user, multiple_users):
        chatroom = Chatroom.objects.create(
            name='Test Chatroom',
            owner=user
        )

        ChatroomUser.objects.create(
            user=multiple_users[0],
            chatroom=chatroom,
            is_admin=False
        )

        assert chatroom.members.count() == 1
        assert multiple_users[0] in chatroom.members.all()

        with pytest.raises(IntegrityError):
            ChatroomUser.objects.create(
                user=multiple_users[0],
                chatroom=chatroom,
                is_admin=True
            )

    def test_chatroom_messages(self, user, multiple_users):
        chatroom = Chatroom.objects.create(
            name='Test Chatroom',
            owner=user
        )

        ChatroomUser.objects.create(
            user=multiple_users[0],
            chatroom=chatroom,
            is_admin=False
        )

        message = ChatroomMessage.objects.create(
            chatroom=chatroom,
            user=multiple_users[0],
            content='Test chatroom message'
        )

        assert message.chatroom == chatroom
        assert message.user == multiple_users[0]
        assert message.content == 'Test chatroom message'
        assert message.sent_at is not None
        expected_str = f"{multiple_users[0].username} in {chatroom.name}: Test chatroom messag"
        assert str(message) == expected_str

    def test_chatroom_admin_functionality(self, user, multiple_users):
        chatroom = Chatroom.objects.create(
            name='Test Chatroom',
            owner=user
        )

        admin_user = ChatroomUser.objects.create(
            user=multiple_users[0],
            chatroom=chatroom,
            is_admin=True
        )

        regular_user = ChatroomUser.objects.create(
            user=multiple_users[1],
            chatroom=chatroom,
            is_admin=False
        )

        assert admin_user.is_admin
        assert not regular_user.is_admin
        assert admin_user.joined_at is not None
        assert regular_user.joined_at is not None


@pytest.mark.django_db
class TestModelValidation:

    def test_message_content_required(self, multiple_users):
        sender = multiple_users[0]
        recipient = multiple_users[1]

        message = Message.objects.create(
            sender=sender,
            recipient=recipient,
            content=''
        )
        assert message.content == ''

    def test_chatroom_name_required(self, user):
        chatroom = Chatroom.objects.create(
            name='',
            owner=user
        )
        assert chatroom.name == ''

    def test_reaction_type_validation(self, multiple_users):
        sender = multiple_users[0]
        recipient = multiple_users[1]

        message = Message.objects.create(
            sender=sender,
            recipient=recipient,
            content='Test message'
        )

        for reaction_type in range(1, 6):
            reaction = MessageReaction.objects.create(
                message=message,
                user=multiple_users[reaction_type % len(multiple_users)],
                reaction_type=reaction_type
            )
            assert reaction.reaction_type == reaction_type
import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail
from django.contrib.messages import get_messages
from accounts.models import UnverifiedUser, Profile
from chat.models import Message, MessageReaction
from chatrooms.models import Chatroom, ChatroomUser, ChatroomMessage
import json
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io


@pytest.mark.integration
@pytest.mark.django_db
class TestAuthenticationFlow:

    def test_complete_registration_flow(self):
        client = Client()

        response = client.get(reverse('accounts:register'))
        assert response.status_code == 200
        assert 'Create Account' in response.content.decode()

        registration_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }

        response = client.post(reverse('accounts:register'), registration_data)
        assert response.status_code == 302

        assert UnverifiedUser.objects.filter(username='newuser').exists()

        assert len(mail.outbox) == 1
        assert 'verify' in mail.outbox[0].subject.lower()

    def test_email_verification_flow(self):
        client = Client()

        unverified_user = UnverifiedUser.objects.create(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            verification_code='test-code-123'
        )

        response = client.get(reverse('accounts:verify_email') + '?code=test-code-123')
        assert response.status_code == 302

        assert User.objects.filter(username='testuser').exists()
        assert not UnverifiedUser.objects.filter(username='testuser').exists()

        user = User.objects.get(username='testuser')
        assert hasattr(user, 'profile')
        assert user.profile.is_verified

    def test_login_logout_flow(self):
        client = Client()

        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        response = client.get(reverse('accounts:login'))
        assert response.status_code == 200

        response = client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'TestPass123!'
        })
        assert response.status_code == 302

        response = client.get(reverse('accounts:profile'))
        assert response.status_code == 200

        response = client.post(reverse('accounts:logout'))
        assert response.status_code == 302


@pytest.mark.integration
@pytest.mark.django_db
class TestChatIntegration:

    def test_private_chat_flow(self, multiple_users):
        client = Client()
        sender = multiple_users[0]
        recipient = multiple_users[1]

        client.force_login(sender)

        response = client.get(reverse('chat:chat_view', args=[recipient.username]))
        assert response.status_code == 200
        assert recipient.username in response.content.decode()

        response = client.get(reverse('chat:get_messages', args=[recipient.username]))
        assert response.status_code == 200
        messages = json.loads(response.content)
        assert len(messages) == 0

        message = Message.objects.create(
            sender=sender,
            recipient=recipient,
            content='Test message'
        )

        response = client.get(reverse('chat:get_messages', args=[recipient.username]))
        assert response.status_code == 200
        messages = json.loads(response.content)
        assert len(messages) == 1
        assert messages[0]['message'] == 'Test message'

    def test_message_reaction_flow(self, multiple_users):
        client = Client()
        sender = multiple_users[0]
        recipient = multiple_users[1]

        message = Message.objects.create(
            sender=sender,
            recipient=recipient,
            content='Test message'
        )

        client.force_login(recipient)

        response = client.post(reverse('chat:react_to_message', args=[message.id]), {
            'reaction_type': 1
        })
        assert response.status_code == 200
        result = json.loads(response.content)
        assert result['success']

        assert MessageReaction.objects.filter(
            message=message,
            user=recipient,
            reaction_type=1
        ).exists()

    def test_image_upload_flow(self, user):
        client = Client()
        client.force_login(user)

        image = Image.new('RGB', (100, 100), color='red')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)

        uploaded_file = SimpleUploadedFile(
            "test.jpg",
            image_io.getvalue(),
            content_type="image/jpeg"
        )

        response = client.post(reverse('chat:upload_image'), {
            'image': uploaded_file
        })
        assert response.status_code == 200
        result = json.loads(response.content)
        assert result['success']
        assert 'image_url' in result


@pytest.mark.integration
@pytest.mark.django_db
class TestChatroomIntegration:

    def test_chatroom_creation_flow(self, user):
        client = Client()
        client.force_login(user)

        response = client.get(reverse('chatrooms:chatroom_list'))
        assert response.status_code == 200
        assert 'You don\'t have any chatrooms' in response.content.decode()

        response = client.get(reverse('chatrooms:create_chatroom'))
        assert response.status_code == 200

        response = client.post(reverse('chatrooms:create_chatroom'), {
            'name': 'Test Chatroom'
        })
        assert response.status_code == 302

        chatroom = Chatroom.objects.get(name='Test Chatroom')
        assert chatroom.owner == user

        assert ChatroomUser.objects.filter(
            chatroom=chatroom,
            user=user,
            is_admin=True
        ).exists()

    def test_chatroom_membership_flow(self, multiple_users):
        client = Client()
        owner = multiple_users[0]
        user_to_add = multiple_users[1]

        chatroom = Chatroom.objects.create(name='Test Room', owner=owner)
        ChatroomUser.objects.create(chatroom=chatroom, user=owner, is_admin=True)

        client.force_login(owner)

        response = client.post(reverse('chatrooms:add_user_to_chatroom', args=[chatroom.id]), {
            'username': user_to_add.username
        })
        assert response.status_code == 200
        result = json.loads(response.content)
        assert result['success']

        assert ChatroomUser.objects.filter(
            chatroom=chatroom,
            user=user_to_add
        ).exists()

        response = client.post(reverse('chatrooms:remove_user', args=[chatroom.id]), {
            'username': user_to_add.username
        })
        assert response.status_code == 200
        result = json.loads(response.content)
        assert result['success']

        assert not ChatroomUser.objects.filter(
            chatroom=chatroom,
            user=user_to_add
        ).exists()

    def test_chatroom_messaging_flow(self, multiple_users):
        client = Client()
        owner = multiple_users[0]
        member = multiple_users[1]

        chatroom = Chatroom.objects.create(name='Test Room', owner=owner)
        ChatroomUser.objects.create(chatroom=chatroom, user=owner, is_admin=True)
        ChatroomUser.objects.create(chatroom=chatroom, user=member, is_admin=False)

        client.force_login(member)

        response = client.get(reverse('chatrooms:chatroom_detail', args=[chatroom.id]))
        assert response.status_code == 200
        assert chatroom.name in response.content.decode()

        response = client.get(reverse('chatrooms:get_chatroom_messages', args=[chatroom.id]))
        assert response.status_code == 200
        messages = json.loads(response.content)
        assert len(messages) == 0

        message = ChatroomMessage.objects.create(
            chatroom=chatroom,
            user=member,
            content='Hello everyone!'
        )

        response = client.get(reverse('chatrooms:get_chatroom_messages', args=[chatroom.id]))
        assert response.status_code == 200
        messages = json.loads(response.content)
        assert len(messages) == 1
        assert messages[0]['content'] == 'Hello everyone!'


@pytest.mark.integration
@pytest.mark.django_db
class TestProfileIntegration:

    def test_profile_update_flow(self, user):
        client = Client()
        client.force_login(user)

        response = client.get(reverse('accounts:profile'))
        assert response.status_code == 200
        assert user.username in response.content.decode()

        response = client.post(reverse('accounts:update_username'), {
            'new_username': 'updateduser',
            'password_for_username': 'testpass123'
        })
        assert response.status_code == 302

        user.refresh_from_db()
        assert user.username == 'updateduser'

        response = client.post(reverse('accounts:update_password'), {
            'current_password': 'testpass123',
            'new_password': 'NewPass123!',
            'confirm_new_password': 'NewPass123!'
        })
        assert response.status_code == 302

        user.refresh_from_db()
        assert user.check_password('NewPass123!')

    def test_user_search_flow(self, multiple_users):
        client = Client()
        searcher = multiple_users[0]

        client.force_login(searcher)

        response = client.get(reverse('chat:search_users') + '?q=user1')
        assert response.status_code == 200
        result = json.loads(response.content)
        assert len(result['users']) >= 1

        usernames = [user['username'] for user in result['users']]
        assert searcher.username not in usernames


@pytest.mark.integration
@pytest.mark.django_db
class TestAccessControl:

    def test_unauthenticated_access(self):
        client = Client()

        protected_urls = [
            reverse('accounts:profile'),
            reverse('chatrooms:chatroom_list'),
            reverse('chat:search_users'),
        ]

        for url in protected_urls:
            response = client.get(url)
            assert response.status_code == 302
            assert '/accounts/login/' in response.url

    def test_chatroom_access_control(self, multiple_users):
        client = Client()
        owner = multiple_users[0]
        non_member = multiple_users[1]

        chatroom = Chatroom.objects.create(name='Private Room', owner=owner)
        ChatroomUser.objects.create(chatroom=chatroom, user=owner, is_admin=True)

        client.force_login(non_member)
        response = client.get(reverse('chatrooms:chatroom_detail', args=[chatroom.id]))
        assert response.status_code == 302

        response = client.get(reverse('chatrooms:get_chatroom_messages', args=[chatroom.id]))
        assert response.status_code == 403

    def test_admin_only_actions(self, multiple_users):
        client = Client()
        owner = multiple_users[0]
        regular_member = multiple_users[1]
        user_to_add = multiple_users[2]

        chatroom = Chatroom.objects.create(name='Test Room', owner=owner)
        ChatroomUser.objects.create(chatroom=chatroom, user=owner, is_admin=True)
        ChatroomUser.objects.create(chatroom=chatroom, user=regular_member, is_admin=False)

        client.force_login(regular_member)
        response = client.post(reverse('chatrooms:add_user_to_chatroom', args=[chatroom.id]), {
            'username': user_to_add.username
        })
        assert response.status_code == 403
        result = json.loads(response.content)
        assert not result['success']
        assert 'admin' in result['error'].lower()
import pytest
import json
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from chat.models import Message, MessageReaction
from chatrooms.models import Chatroom, ChatroomUser, ChatroomMessage, SuggestedUser
from accounts.models import Profile, UnverifiedUser
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io
import time


@pytest.mark.django_db
class TestAPIComprehensive:

    def test_search_users_api_various_queries(self, multiple_users):
        client = Client()
        client.force_login(multiple_users[0])

        test_cases = [
            ('user', True),
            ('USER', True),
            ('nonexistent', False),
            ('us', True),
            ('a', False),
            ('user1', True),
            ('user123456', False),
        ]

        for query, should_find in test_cases:
            response = client.get(f'/chat/search-users/?q={query}')
            assert response.status_code == 200

            data = json.loads(response.content)
            assert 'users' in data
            assert isinstance(data['users'], list)

            if should_find and len(query) >= 2:
                usernames = [user['username'] for user in data['users']]
                assert multiple_users[0].username not in usernames

            print(f"Query '{query}': Found {len(data['users'])} users")

    def test_search_users_api_pagination_and_limits(self, db):
        client = Client()

        users = []
        for i in range(15):
            user = User.objects.create_user(
                username=f'searchtest{i:02d}',
                email=f'searchtest{i:02d}@example.com',
                password='testpass123'
            )
            users.append(user)

        client.force_login(users[0])

        response = client.get('/chat/search-users/?q=searchtest')
        assert response.status_code == 200

        data = json.loads(response.content)
        assert len(data['users']) <= 10

    def test_get_messages_api_edge_cases(self, multiple_users):
        client = Client()
        sender = multiple_users[0]
        recipient = multiple_users[1]
        other_user = multiple_users[2]

        client.force_login(sender)
        response = client.get(f'/chat/{recipient.username}/messages/')
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data == []

        Message.objects.create(sender=sender, recipient=recipient, content="Hello from sender")
        Message.objects.create(sender=recipient, recipient=sender, content="Hello from recipient")
        Message.objects.create(sender=other_user, recipient=recipient, content="Should not see this")

        response = client.get(f'/chat/{recipient.username}/messages/')
        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data) == 2

        response = client.get('/chat/nonexistentuser/messages/')
        assert response.status_code == 404

    def test_get_messages_api_with_reactions(self, multiple_users):
        client = Client()
        sender = multiple_users[0]
        recipient = multiple_users[1]

        message = Message.objects.create(
            sender=sender,
            recipient=recipient,
            content="Message with reaction"
        )
        MessageReaction.objects.create(
            message=message,
            user=sender,
            reaction_type=1
        )

        client.force_login(sender)
        response = client.get(f'/chat/{recipient.username}/messages/')
        assert response.status_code == 200

        data = json.loads(response.content)
        assert len(data) == 1
        assert data[0]['reaction_type'] == 1

    def test_message_reaction_api_comprehensive(self, multiple_users):
        client = Client()
        sender = multiple_users[0]
        recipient = multiple_users[1]
        other_user = multiple_users[2]

        message = Message.objects.create(
            sender=sender,
            recipient=recipient,
            content="Test reaction message"
        )

        client.force_login(sender)
        response = client.post(f'/chat/message/{message.id}/react/', {
            'reaction_type': 1
        })
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success']

        response = client.post(f'/chat/message/{message.id}/react/', {
            'reaction_type': 2
        })
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success']

        reaction = MessageReaction.objects.get(message=message, user=sender)
        assert reaction.reaction_type == 2

        client.force_login(other_user)
        response = client.post(f'/chat/message/{message.id}/react/', {
            'reaction_type': 3
        })
        assert response.status_code == 403

    def test_chatroom_api_comprehensive(self, multiple_users):
        client = Client()
        owner = multiple_users[0]
        member = multiple_users[1]
        admin = multiple_users[2]

        chatroom = Chatroom.objects.create(name='API Test Room', owner=owner)
        ChatroomUser.objects.create(chatroom=chatroom, user=owner, is_admin=True)
        ChatroomUser.objects.create(chatroom=chatroom, user=member, is_admin=False)
        ChatroomUser.objects.create(chatroom=chatroom, user=admin, is_admin=True)

        client.force_login(owner)
        response = client.get('/chatrooms/get-chatrooms/')
        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data) >= 1

        chatroom_data = next(room for room in data if room['name'] == 'API Test Room')
        assert chatroom_data['is_admin'] == True

        response = client.get(f'/chatrooms/{chatroom.id}/users/')
        assert response.status_code == 200
        users_data = json.loads(response.content)
        assert len(users_data) == 3

        response = client.get(f'/chatrooms/{chatroom.id}/messages/')
        assert response.status_code == 200
        messages_data = json.loads(response.content)
        assert len(messages_data) == 0

    def test_chatroom_suggestion_api(self, multiple_users):
        client = Client()
        owner = multiple_users[0]
        regular_member = multiple_users[1]
        suggested_user = multiple_users[2]

        chatroom = Chatroom.objects.create(name='Suggestion Test Room', owner=owner)
        ChatroomUser.objects.create(chatroom=chatroom, user=owner, is_admin=True)
        ChatroomUser.objects.create(chatroom=chatroom, user=regular_member, is_admin=False)

        client.force_login(regular_member)
        response = client.post(f'/chatrooms/{chatroom.id}/suggest-user/', {
            'username': suggested_user.username
        })
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success']

        assert SuggestedUser.objects.filter(
            chatroom=chatroom,
            suggested_user=suggested_user
        ).exists()

        client.force_login(owner)
        response = client.get(f'/chatrooms/{chatroom.id}/suggested-users/')
        assert response.status_code == 200
        suggestions = json.loads(response.content)
        assert len(suggestions) == 1
        assert suggestions[0]['username'] == suggested_user.username

        user_id = suggestions[0]['id']
        response = client.post(f'/chatrooms/{chatroom.id}/approve-suggestion/', {
            'user_id': user_id
        })
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success']

        assert ChatroomUser.objects.filter(chatroom=chatroom, user=suggested_user).exists()
        assert not SuggestedUser.objects.filter(chatroom=chatroom, suggested_user=suggested_user).exists()

    def test_image_upload_api_comprehensive(self, user):
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

        response = client.post('/chat/upload-image/', {
            'image': uploaded_file
        })
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success']
        assert 'image_url' in data

        response = client.post('/chat/upload-image/', {})
        assert response.status_code == 400

        text_file = SimpleUploadedFile(
            "test.txt",
            b"This is not an image",
            content_type="text/plain"
        )

        response = client.post('/chat/upload-image/', {
            'image': text_file
        })
        assert response.status_code == 400

    def test_api_performance_with_data(self, multiple_users):
        client = Client()
        sender = multiple_users[0]
        recipient = multiple_users[1]

        messages = []
        for i in range(100):
            message = Message(
                sender=sender,
                recipient=recipient,
                content=f'Performance test message {i}'
            )
            messages.append(message)
        Message.objects.bulk_create(messages)

        client.force_login(sender)

        start_time = time.time()
        response = client.get(f'/chat/{recipient.username}/messages/')
        end_time = time.time()

        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data) == 100

        response_time = end_time - start_time
        print(f"API responded with 100 messages in {response_time:.3f} seconds")

        assert response_time < 2.0

    def test_api_authentication_edge_cases(self, user):
        client = Client()

        response = client.get('/chatrooms/get-chatrooms/')
        assert response.status_code == 302

        client.force_login(user)
        client.logout()

        response = client.get('/chatrooms/get-chatrooms/')
        assert response.status_code == 302

    def test_api_response_consistency(self, user):
        client = Client()
        client.force_login(user)

        responses = []
        for i in range(5):
            response = client.get('/chat/search-users/?q=test')
            responses.append({
                'status': response.status_code,
                'call': i + 1
            })
            time.sleep(0.1)

        status_codes = [r['status'] for r in responses]
        assert all(status == 200 for status in status_codes), f"Inconsistent responses: {status_codes}"

        print(f"API consistency test: All {len(responses)} calls returned status 200")

    def test_chatroom_basic_functionality(self, multiple_users):
        client = Client()
        owner = multiple_users[0]
        member = multiple_users[1]

        chatroom = Chatroom.objects.create(name='Basic Test Room', owner=owner)
        ChatroomUser.objects.create(chatroom=chatroom, user=owner, is_admin=True)
        ChatroomUser.objects.create(chatroom=chatroom, user=member, is_admin=False)

        client.force_login(owner)

        response = client.get(f'/chatrooms/{chatroom.id}/')
        assert response.status_code == 200

        response = client.get(f'/chatrooms/{chatroom.id}/users/')
        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data) == 2

        response = client.get(f'/chatrooms/{chatroom.id}/messages/')
        assert response.status_code == 200
        data = json.loads(response.content)
        assert isinstance(data, list)

    def test_user_profile_api_access(self, multiple_users):
        client = Client()
        user = multiple_users[0]
        other_user = multiple_users[1]

        client.force_login(user)
        response = client.get('/accounts/profile/')
        assert response.status_code == 200

        response = client.get(f'/accounts/{other_user.username}/')
        assert response.status_code == 200

        response = client.get('/chat/search-users/?q=user')
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'users' in data

    def test_basic_message_operations(self, multiple_users):
        client = Client()
        sender = multiple_users[0]
        recipient = multiple_users[1]

        client.force_login(sender)

        message = Message.objects.create(
            sender=sender,
            recipient=recipient,
            content="Basic test message"
        )

        response = client.get(f'/chat/{recipient.username}/messages/')
        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data) == 1
        assert data[0]['message'] == "Basic test message"

        response = client.post(f'/chat/message/{message.id}/react/', {
            'reaction_type': 1
        })
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success']

        reaction = MessageReaction.objects.get(message=message, user=sender)
        assert reaction.reaction_type == 1
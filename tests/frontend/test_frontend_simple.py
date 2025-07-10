import pytest
from django.test import Client
from django.contrib.auth.models import User


@pytest.mark.django_db
class TestFrontendSimple:

    def test_homepage_loads(self):
        client = Client()
        response = client.get('/')

        assert response.status_code == 200
        assert 'Obscura Messenger' in response.content.decode()

    def test_login_page_loads(self):
        client = Client()
        response = client.get('/accounts/login/')

        assert response.status_code == 200
        assert 'Log In' in response.content.decode()

    def test_register_page_loads(self):
        client = Client()
        response = client.get('/accounts/register/')

        assert response.status_code == 200
        assert 'Create Account' in response.content.decode()

    def test_profile_requires_login(self):
        client = Client()
        response = client.get('/accounts/profile/')

        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_authenticated_profile_access(self, user):
        client = Client()
        client.force_login(user)

        response = client.get('/accounts/profile/')
        assert response.status_code == 200
        assert user.username in response.content.decode()

    def test_chatroom_list_requires_login(self):
        client = Client()
        response = client.get('/chatrooms/')

        assert response.status_code == 302

    def test_authenticated_chatroom_access(self, user):
        client = Client()
        client.force_login(user)

        response = client.get('/chatrooms/')
        assert response.status_code == 200

    def test_chat_view_access(self, multiple_users):
        client = Client()
        sender = multiple_users[0]
        recipient = multiple_users[1]

        client.force_login(sender)
        response = client.get(f'/chat/{recipient.username}/')

        assert response.status_code == 200
        assert recipient.username in response.content.decode()
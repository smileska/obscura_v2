import os
import sys
import django
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.test_settings')

django.setup()

import pytest
from django.conf import settings
from django.core.management import call_command
from faker import Faker

fake = Faker()

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup):
    pass

@pytest.fixture
def user(db):
    from django.contrib.auth.models import User
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

@pytest.fixture
def admin_user(db):
    from django.contrib.auth.models import User
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )

@pytest.fixture
def multiple_users(db):
    from django.contrib.auth.models import User
    users = []
    for i in range(5):
        user = User.objects.create_user(
            username=f'user{i}',
            email=f'user{i}@example.com',
            password='testpass123'
        )
        users.append(user)
    return users

@pytest.fixture
def authenticated_client(client, user):
    client.force_login(user)
    return client

@pytest.fixture
def admin_client(client, admin_user):
    client.force_login(admin_user)
    return client

@pytest.fixture
def fake_data():
    return fake

@pytest.fixture
def chatroom(db, user):
    from chatrooms.models import Chatroom
    return Chatroom.objects.create(
        name='Test Chatroom',
        owner=user
    )

@pytest.fixture
def message(db, user, multiple_users):
    from chat.models import Message
    return Message.objects.create(
        sender=user,
        recipient=multiple_users[0],
        content='Test message content'
    )

import pytest
import time
import threading
from django.test import Client, TransactionTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import transaction, connections
from django.core.cache import cache
from chat.models import Message, MessageReaction
from chatrooms.models import Chatroom, ChatroomUser, ChatroomMessage
from accounts.models import Profile
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
import psutil
import os
from django.test.utils import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io


@pytest.mark.performance
@pytest.mark.django_db
class TestDatabasePerformance:

    def test_user_creation_performance(self):
        start_time = time.time()

        users = []
        for i in range(20):
            user = User(
                username=f'user_{i}',
                email=f'user_{i}@example.com',
                password='pbkdf2_sha256$260000$fixed_hash_for_testing'
            )
            users.append(user)

        User.objects.bulk_create(users)

        end_time = time.time()
        creation_time = end_time - start_time

        print(f"Created 20 users in {creation_time:.3f} seconds")
        assert creation_time < 10.0
        assert User.objects.filter(username__startswith='user_').count() >= 20

    def test_message_creation_performance(self, multiple_users):
        sender = multiple_users[0]
        recipient = multiple_users[1]

        start_time = time.time()

        messages = []
        for i in range(100):
            message = Message(
                sender=sender,
                recipient=recipient,
                content=f'Performance test message {i}'
            )
            messages.append(message)

        Message.objects.bulk_create(messages)

        end_time = time.time()
        creation_time = end_time - start_time

        print(f"Created 100 messages in {creation_time:.3f} seconds")
        assert Message.objects.filter(content__startswith='Performance test').count() >= 100

    def test_message_query_performance(self, multiple_users):
        sender = multiple_users[0]
        recipient = multiple_users[1]

        messages = []
        for i in range(200):
            message = Message(
                sender=sender,
                recipient=recipient,
                content=f'Test message {i}'
            )
            messages.append(message)
        Message.objects.bulk_create(messages)

        start_time = time.time()

        messages = Message.objects.filter(
            sender=sender, recipient=recipient
        ).select_related('sender', 'recipient').order_by('timestamp')[:50]

        list(messages)

        end_time = time.time()
        query_time = end_time - start_time

        print(f"Queried 50 messages from 200+ in {query_time:.3f} seconds")
        assert query_time < 1.0

    def test_chatroom_member_query_performance(self, multiple_users):
        owner = multiple_users[0]
        chatroom = Chatroom.objects.create(name='Performance Test Room', owner=owner)

        chatroom_users = []
        for i, user in enumerate(multiple_users):
            chatroom_user = ChatroomUser(
                chatroom=chatroom,
                user=user,
                is_admin=(i == 0)
            )
            chatroom_users.append(chatroom_user)

        ChatroomUser.objects.bulk_create(chatroom_users)

        start_time = time.time()

        members = ChatroomUser.objects.filter(
            chatroom=chatroom
        ).select_related('user')

        list(members)

        end_time = time.time()
        query_time = end_time - start_time

        print(f"Queried chatroom members in {query_time:.3f} seconds")
        assert query_time < 0.5


@pytest.mark.performance
@pytest.mark.django_db
class TestViewPerformance:

    def test_login_view_performance(self, user):
        client = Client()

        response_times = []

        for _ in range(5):
            start_time = time.time()

            response = client.post(reverse('accounts:login'), {
                'username': user.username,
                'password': 'testpass123'
            })

            end_time = time.time()
            response_times.append(end_time - start_time)

            assert response.status_code in [200, 302]

            client.logout()

        avg_time = statistics.mean(response_times)
        max_time = max(response_times)

        print(f"Login view - Average: {avg_time:.3f}s, Max: {max_time:.3f}s")
        assert avg_time < 2.0
        assert max_time < 5.0

    def test_chat_view_performance(self, multiple_users):
        client = Client()
        sender = multiple_users[0]
        recipient = multiple_users[1]

        messages = []
        for i in range(20):
            message = Message(
                sender=sender,
                recipient=recipient,
                content=f'Test message {i}'
            )
            messages.append(message)
        Message.objects.bulk_create(messages)

        client.force_login(sender)

        response_times = []

        for _ in range(3):
            start_time = time.time()

            response = client.get(reverse('chat:chat_view', args=[recipient.username]))

            end_time = time.time()
            response_times.append(end_time - start_time)

            assert response.status_code == 200

        avg_time = statistics.mean(response_times)
        print(f"Chat view - Average: {avg_time:.3f}s")
        assert avg_time < 3.0

    def test_message_api_performance(self, multiple_users):
        client = Client()
        sender = multiple_users[0]
        recipient = multiple_users[1]

        messages = []
        for i in range(50):
            message = Message(
                sender=sender,
                recipient=recipient,
                content=f'API test message {i}'
            )
            messages.append(message)
        Message.objects.bulk_create(messages)

        client.force_login(sender)

        response_times = []

        for _ in range(3):
            start_time = time.time()

            response = client.get(reverse('chat:get_messages', args=[recipient.username]))

            end_time = time.time()
            response_times.append(end_time - start_time)

            assert response.status_code == 200
            data = json.loads(response.content)
            assert len(data) == 50

        avg_time = statistics.mean(response_times)
        print(f"Message API - Average: {avg_time:.3f}s")
        assert avg_time < 1.5


@pytest.mark.performance
@pytest.mark.django_db
class TestMemoryPerformance:

    def get_memory_usage(self):
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024

    def test_bulk_data_memory_usage(self):
        initial_memory = self.get_memory_usage()

        users = []
        for i in range(100):
            user = User(
                username=f'memory_test_user_{i}',
                email=f'memory_user_{i}@example.com',
                password='pbkdf2_sha256$260000$fixed_hash_for_testing'
            )
            users.append(user)

        User.objects.bulk_create(users)

        after_creation_memory = self.get_memory_usage()
        memory_increase = after_creation_memory - initial_memory

        print(f"Memory usage - Initial: {initial_memory:.1f}MB, After: {after_creation_memory:.1f}MB")
        print(f"Memory increase: {memory_increase:.1f}MB for 100 users")

        assert memory_increase < 200

    def test_message_query_memory_efficiency(self, multiple_users):
        sender = multiple_users[0]
        recipient = multiple_users[1]

        messages = []
        for i in range(500):
            message = Message(
                sender=sender,
                recipient=recipient,
                content=f'Memory test message {i}' * 5
            )
            messages.append(message)
        Message.objects.bulk_create(messages)

        initial_memory = self.get_memory_usage()

        messages = Message.objects.filter(
            sender=sender, recipient=recipient
        ).select_related('sender', 'recipient')[:50]

        message_list = list(messages)

        after_query_memory = self.get_memory_usage()
        memory_increase = after_query_memory - initial_memory

        print(f"Query memory usage - Initial: {initial_memory:.1f}MB, After: {after_query_memory:.1f}MB")
        print(f"Memory increase: {memory_increase:.1f}MB for querying 50 messages")

        assert len(message_list) == 50
        assert memory_increase < 100


@pytest.mark.performance
@pytest.mark.django_db
class TestImageUploadPerformance:
    def create_test_image(self, size=(200, 150)):
        image = Image.new('RGB', size, color='red')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG', quality=70)
        image_io.seek(0)
        return image_io.getvalue()

    def test_single_image_upload_performance(self, user):
        client = Client()
        client.force_login(user)

        image_data = self.create_test_image()

        response_times = []

        for i in range(3):
            uploaded_file = SimpleUploadedFile(
                f"test_{i}.jpg",
                image_data,
                content_type="image/jpeg"
            )

            start_time = time.time()

            response = client.post(reverse('chat:upload_image'), {
                'image': uploaded_file
            })

            end_time = time.time()
            response_times.append(end_time - start_time)

            assert response.status_code == 200
            result = json.loads(response.content)
            assert result['success']

        avg_time = statistics.mean(response_times)
        max_time = max(response_times)

        print(f"Image upload - Average: {avg_time:.3f}s, Max: {max_time:.3f}s")
        assert avg_time < 5.0
        assert max_time < 10.0

@pytest.mark.performance
@pytest.mark.django_db
class TestSimpleStressTest:

    def test_sequential_user_creation_stress(self):
        start_time = time.time()
        users_created = 0
        for batch in range(5):
            users = []
            for i in range(20):
                user = User(
                    username=f'stress_user_{batch}_{i}',
                    email=f'stress_{batch}_{i}@example.com',
                    password='pbkdf2_sha256$260000$fixed_hash_for_testing'
                )
                users.append(user)

            User.objects.bulk_create(users)
            users_created += len(users)

        end_time = time.time()
        total_time = end_time - start_time

        print(f"Created {users_created} users in {total_time:.3f} seconds")
        print(f"Rate: {users_created / total_time:.1f} users/second")

        assert users_created == 100
        assert total_time < 30.0
        assert users_created / total_time > 2

    def test_database_query_stress(self, multiple_users):
        messages = []
        for i in range(100):
            message = Message(
                sender=multiple_users[0],
                recipient=multiple_users[1],
                content=f'Stress test message {i}'
            )
            messages.append(message)
        Message.objects.bulk_create(messages)

        start_time = time.time()
        successful_queries = 0

        for _ in range(20):
            try:
                count = Message.objects.filter(
                    sender=multiple_users[0]
                ).count()
                if count > 0:
                    successful_queries += 1
            except Exception:
                pass

        end_time = time.time()
        total_time = end_time - start_time

        success_rate = successful_queries / 20
        avg_time = total_time / 20

        print(f"Database stress test - Average query time: {avg_time:.3f}s")
        print(f"Success rate: {success_rate:.2%}")

        assert success_rate >= 0.9
        assert avg_time < 1.0

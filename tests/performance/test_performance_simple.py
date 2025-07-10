import pytest
import time
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from chat.models import Message
import json
import statistics


@pytest.mark.django_db
class TestBasicPerformance:

    def test_user_creation_performance_realistic(self):
        start_time = time.time()

        users = []
        for i in range(10):
            user = User(
                username=f'perf_user_{i}',
                email=f'perf_user_{i}@example.com'
            )
            user.password = 'pbkdf2_sha256$260000$test_hash_for_performance'
            users.append(user)

        User.objects.bulk_create(users)

        end_time = time.time()
        creation_time = end_time - start_time

        print(f"Created 10 users in {creation_time:.3f} seconds")

        assert creation_time < 30.0
        assert User.objects.filter(username__startswith='perf_user_').count() == 10

    def test_message_creation_performance_realistic(self, multiple_users):
        if len(multiple_users) < 2:
            pytest.skip("Need at least 2 users for this test")

        sender = multiple_users[0]
        recipient = multiple_users[1]

        start_time = time.time()

        messages = []
        for i in range(20):
            message = Message(
                sender=sender,
                recipient=recipient,
                content=f'Performance test message {i}'
            )
            messages.append(message)

        Message.objects.bulk_create(messages)

        end_time = time.time()
        creation_time = end_time - start_time

        print(f"Created 20 messages in {creation_time:.3f} seconds")

        assert creation_time < 15.0
        assert Message.objects.filter(content__startswith='Performance test').count() >= 20

    def test_homepage_load_performance(self):
        client = Client()

        response_times = []

        for _ in range(3):
            start_time = time.time()
            response = client.get('/')
            end_time = time.time()

            response_times.append(end_time - start_time)
            assert response.status_code == 200

        avg_time = statistics.mean(response_times)
        max_time = max(response_times)

        print(f"Homepage load - Average: {avg_time:.3f}s, Max: {max_time:.3f}s")

        assert avg_time < 10.0
        assert max_time < 20.0

    def test_login_performance_realistic(self, user):
        client = Client()

        response_times = []

        for _ in range(3):
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
        print(f"Login performance - Average: {avg_time:.3f}s")

        assert avg_time < 15.0

    def test_message_retrieval_performance(self, multiple_users):
        if len(multiple_users) < 2:
            pytest.skip("Need at least 2 users for this test")

        client = Client()
        sender = multiple_users[0]
        recipient = multiple_users[1]

        messages = []
        for i in range(10):
            message = Message(
                sender=sender,
                recipient=recipient,
                content=f'API test message {i}'
            )
            messages.append(message)
        Message.objects.bulk_create(messages)

        client.force_login(sender)

        start_time = time.time()

        response = client.get(reverse('chat:get_messages', args=[recipient.username]))

        end_time = time.time()
        api_time = end_time - start_time

        print(f"Message API took {api_time:.3f} seconds")

        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data) == 10

        assert api_time < 10.0

    def test_basic_database_operations(self):
        start_time = time.time()

        user = User.objects.create_user(
            username='db_test_user',
            email='dbtest@example.com',
            password='testpass123'
        )
        found_user = User.objects.get(username='db_test_user')
        assert found_user.email == 'dbtest@example.com'

        found_user.email = 'updated@example.com'
        found_user.save()

        found_user.delete()

        end_time = time.time()
        operation_time = end_time - start_time

        print(f"Basic CRUD operations took {operation_time:.3f} seconds")

        assert operation_time < 30.0

    def test_profile_access_performance(self, user):
        client = Client()
        client.force_login(user)

        start_time = time.time()

        response = client.get(reverse('accounts:profile'))

        end_time = time.time()
        profile_time = end_time - start_time

        print(f"Profile page loaded in {profile_time:.3f} seconds")

        assert response.status_code == 200
        assert user.username.encode() in response.content

        assert profile_time < 15.0

    def test_search_users_performance(self, multiple_users):
        client = Client()
        client.force_login(multiple_users[0])

        start_time = time.time()

        response = client.get('/chat/search-users/?q=user')

        end_time = time.time()
        search_time = end_time - start_time

        print(f"User search took {search_time:.3f} seconds")

        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'users' in data

        assert search_time < 10.0


@pytest.mark.django_db
class TestMemoryBasics:

    def test_memory_doesnt_explode(self):
        try:
            import psutil
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024
        except ImportError:
            pytest.skip("psutil not available for memory testing")

        users = []
        for i in range(5):
            user = User(
                username=f'memory_user_{i}',
                email=f'memory_{i}@example.com',
                password='pbkdf2_sha256$260000$test_hash'
            )
            users.append(user)

        User.objects.bulk_create(users)

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory

        print(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (increase: {memory_increase:.1f}MB)")

        assert memory_increase < 500


if __name__ == '__main__':
    print("Performance tests loaded successfully!")
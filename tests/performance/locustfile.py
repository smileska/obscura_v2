from locust import HttpUser, task, between
import random
import json
from urllib.parse import urljoin
import time


class ObscuraUser(HttpUser):

    wait_time = between(1, 3)

    def on_start(self):
        self.username = f"user_{random.randint(1000, 9999)}"
        self.email = f"{self.username}@example.com"
        self.password = "TestPass123!"

        self.register_user()
        self.login_user()

        self.chat_partners = []
        self.chatrooms = []

    def register_user(self):
        response = self.client.get("/accounts/register/")
        if response.status_code == 200:
            csrf_token = self.extract_csrf_token(response.text)

            registration_data = {
                'username': self.username,
                'email': self.email,
                'password1': self.password,
                'password2': self.password,
                'csrfmiddlewaretoken': csrf_token
            }

            with self.client.post("/accounts/register/",
                                  data=registration_data,
                                  catch_response=True) as response:
                if response.status_code in [200, 302]:
                    response.success()
                else:
                    response.failure(f"Registration failed: {response.status_code}")

    def login_user(self):
        response = self.client.get("/accounts/login/")
        if response.status_code == 200:
            csrf_token = self.extract_csrf_token(response.text)

            login_data = {
                'username': self.username,
                'password': self.password,
                'csrfmiddlewaretoken': csrf_token
            }

            with self.client.post("/accounts/login/",
                                  data=login_data,
                                  catch_response=True) as response:
                if response.status_code in [200, 302]:
                    response.success()
                else:
                    response.failure(f"Login failed: {response.status_code}")

    def extract_csrf_token(self, html):
        import re
        csrf_pattern = r'name=["\']csrfmiddlewaretoken["\'] value=["\']([^"\']+)["\']'
        match = re.search(csrf_pattern, html)
        return match.group(1) if match else 'dummy-csrf-token'

    @task(3)
    def view_homepage(self):
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                if "Obscura Messenger" in response.text:
                    response.success()
                else:
                    response.failure("Homepage doesn't contain expected content")
            else:
                response.failure(f"Homepage failed: {response.status_code}")

    @task(2)
    def view_profile(self):
        with self.client.get("/accounts/profile/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 302:
                response.success()
            else:
                response.failure(f"Profile view failed: {response.status_code}")

    @task(2)
    def search_users(self):
        search_query = random.choice(['user', 'test', 'admin'])
        with self.client.get(f"/chat/search-users/?q={search_query}",
                             catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'users' in data:
                        if data['users'] and len(self.chat_partners) < 3:
                            self.chat_partners.extend([u['username'] for u in data['users'][:2]])
                        response.success()
                    else:
                        response.failure("Invalid search response format")
                except json.JSONDecodeError:
                    response.failure("Search response is not valid JSON")
            else:
                response.failure(f"User search failed: {response.status_code}")

    @task(1)
    def view_chatrooms(self):
        with self.client.get("/chatrooms/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 302:
                response.success()
            else:
                response.failure(f"Chatroom list failed: {response.status_code}")

    @task(1)
    def create_chatroom(self):
        if len(self.chatrooms) < 2:
            response = self.client.get("/chatrooms/create/")
            if response.status_code == 200:
                csrf_token = self.extract_csrf_token(response.text)

                chatroom_name = f"Room_{self.username}_{random.randint(1, 100)}"

                create_data = {
                    'name': chatroom_name,
                    'csrfmiddlewaretoken': csrf_token
                }

                with self.client.post("/chatrooms/create/",
                                      data=create_data,
                                      catch_response=True) as response:
                    if response.status_code in [200, 302]:
                        self.chatrooms.append(chatroom_name)
                        response.success()
                    else:
                        response.failure(f"Chatroom creation failed: {response.status_code}")

    @task(2)
    def view_chat_with_user(self):
        if self.chat_partners:
            partner = random.choice(self.chat_partners)
            with self.client.get(f"/chat/{partner}/", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 302:
                    response.success()
                else:
                    response.failure(f"Chat view failed: {response.status_code}")

    @task(1)
    def get_messages(self):
        if self.chat_partners:
            partner = random.choice(self.chat_partners)
            with self.client.get(f"/chat/{partner}/messages/",
                                 catch_response=True) as response:
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            response.success()
                        else:
                            response.failure("Messages response is not a list")
                    except json.JSONDecodeError:
                        response.failure("Messages response is not valid JSON")
                elif response.status_code in [302, 403]:
                    response.success()
                else:
                    response.failure(f"Get messages failed: {response.status_code}")


class AdminUser(HttpUser):

    wait_time = between(2, 5)
    weight = 1

    def on_start(self):
        self.username = "admin"
        self.password = "admin"

        response = self.client.get("/accounts/login/")
        if response.status_code == 200:
            csrf_token = self.extract_csrf_token(response.text)

            login_data = {
                'username': self.username,
                'password': self.password,
                'csrfmiddlewaretoken': csrf_token
            }

            self.client.post("/accounts/login/", data=login_data)

    def extract_csrf_token(self, html):
        import re
        csrf_pattern = r'name=["\']csrfmiddlewaretoken["\'] value=["\']([^"\']+)["\']'
        match = re.search(csrf_pattern, html)
        return match.group(1) if match else 'dummy-csrf-token'

    @task(2)
    def admin_view_users(self):
        with self.client.get("/admin/", catch_response=True) as response:
            if response.status_code in [200, 302]:
                response.success()
            else:
                response.failure(f"Admin access failed: {response.status_code}")

    @task(1)
    def admin_search_users(self):
        search_terms = ['user', 'test', 'admin', 'demo']
        search_query = random.choice(search_terms)

        with self.client.get(f"/chat/search-users/?q={search_query}",
                             catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Admin user search failed: {response.status_code}")


class ChatroomHeavyUser(HttpUser):

    wait_time = between(1, 2)
    weight = 2

    def on_start(self):
        self.username = f"chatroom_user_{random.randint(1000, 9999)}"
        self.email = f"{self.username}@example.com"
        self.password = "TestPass123!"
        self.chatroom_ids = []

        self.register_and_login()

    def register_and_login(self):
        response = self.client.get("/accounts/register/")
        if response.status_code == 200:
            csrf_token = self.extract_csrf_token(response.text)

            self.client.post("/accounts/register/", data={
                'username': self.username,
                'email': self.email,
                'password1': self.password,
                'password2': self.password,
                'csrfmiddlewaretoken': csrf_token
            })

        response = self.client.get("/accounts/login/")
        if response.status_code == 200:
            csrf_token = self.extract_csrf_token(response.text)

            self.client.post("/accounts/login/", data={
                'username': self.username,
                'password': self.password,
                'csrfmiddlewaretoken': csrf_token
            })

    def extract_csrf_token(self, html):
        import re
        csrf_pattern = r'name=["\']csrfmiddlewaretoken["\'] value=["\']([^"\']+)["\']'
        match = re.search(csrf_pattern, html)
        return match.group(1) if match else 'dummy-csrf-token'

    @task(4)
    def view_chatrooms(self):
        self.client.get("/chatrooms/")

    @task(2)
    def create_chatroom(self):
        if len(self.chatroom_ids) < 5:
            response = self.client.get("/chatrooms/create/")
            if response.status_code == 200:
                csrf_token = self.extract_csrf_token(response.text)

                chatroom_name = f"Heavy_Room_{random.randint(1, 1000)}"

                with self.client.post("/chatrooms/create/",
                                      data={
                                          'name': chatroom_name,
                                          'csrfmiddlewaretoken': csrf_token
                                      },
                                      catch_response=True) as response:
                    if response.status_code in [200, 302]:
                        response.success()
                    else:
                        response.failure(f"Heavy user chatroom creation failed")

    @task(3)
    def get_chatrooms_api(self):
        with self.client.get("/chatrooms/get-chatrooms/",
                             catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        self.chatroom_ids = [room.get('id') for room in data if room.get('id')]
                        response.success()
                    else:
                        response.failure("Chatrooms API returned invalid format")
                except json.JSONDecodeError:
                    response.failure("Chatrooms API response is not valid JSON")
            else:
                response.failure(f"Chatrooms API failed: {response.status_code}")

    @task(2)
    def view_chatroom_detail(self):
        if self.chatroom_ids:
            chatroom_id = random.choice(self.chatroom_ids)
            with self.client.get(f"/chatrooms/{chatroom_id}/",
                                 catch_response=True) as response:
                if response.status_code in [200, 302, 403]:
                    response.success()
                else:
                    response.failure(f"Chatroom detail failed: {response.status_code}")


class QuickTest(HttpUser):
    wait_time = between(0.5, 1)

    @task
    def quick_homepage_test(self):
        start_time = time.time()
        response = self.client.get("/")
        end_time = time.time()

        response_time = end_time - start_time

        if response.status_code == 200 and response_time < 2.0:
            pass
        elif response_time >= 2.0:
            print(f"Slow response: {response_time:.2f}s")


class APIPerformanceUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def on_start(self):
        self.client.get("/accounts/login/")

    @task(5)
    def test_search_api_performance(self):
        search_terms = ['user', 'test', 'admin', 'demo', 'chat']
        query = random.choice(search_terms)

        start_time = time.time()
        with self.client.get(f"/chat/search-users/?q={query}",
                             catch_response=True) as response:
            end_time = time.time()
            response_time = end_time - start_time

            if response.status_code == 200 and response_time < 1.0:
                response.success()
            elif response_time >= 1.0:
                response.failure(f"Search API too slow: {response_time:.2f}s")
            else:
                response.failure(f"Search API failed: {response.status_code}")

    @task(3)
    def test_homepage_performance(self):
        start_time = time.time()
        with self.client.get("/", catch_response=True) as response:
            end_time = time.time()
            response_time = end_time - start_time

            if response.status_code == 200 and response_time < 0.5:
                response.success()
            elif response_time >= 0.5:
                response.failure(f"Homepage too slow: {response_time:.2f}s")
            else:
                response.failure(f"Homepage failed: {response.status_code}")
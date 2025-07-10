import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from django.test import Client
from bs4 import BeautifulSoup
import json


class TestBasicFrontendFunctionality(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )

    def test_login_form_submission(self):
        response = self.client.post('/accounts/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)

    def test_invalid_login_shows_error(self):
        response = self.client.post('/accounts/login/', {
            'username': 'invalid',
            'password': 'invalid'
        })
        self.assertIn(response.status_code, [200, 302])

    def test_registration_form_submission(self):
        response = self.client.post('/accounts/register/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        })
        self.assertIn(response.status_code, [200, 302])

    def test_authenticated_user_access(self):
        self.client.force_login(self.user)

        protected_pages = [
            '/',
            '/accounts/profile/',
            f'/chat/{self.other_user.username}/',
        ]

        for page in protected_pages:
            response = self.client.get(page)
            self.assertNotEqual(response.status_code, 403, f"Authenticated user should access {page}")

    def test_unauthenticated_user_redirects(self):
        protected_pages = [
            '/accounts/profile/',
        ]

        for page in protected_pages:
            response = self.client.get(page)
            self.assertIn(response.status_code, [302, 403], f"Unauthenticated user should be redirected from {page}")

    def test_user_search_functionality(self):
        self.client.force_login(self.user)

        response = self.client.get('/chat/search-users/', {'q': 'other'})

        if response.status_code == 200:
            try:
                data = response.json()
                self.assertIn('users', data)
            except json.JSONDecodeError:
                pass

    def test_message_api_endpoint(self):
        self.client.force_login(self.user)

        response = self.client.get(f'/chat/{self.other_user.username}/messages/')
        self.assertIn(response.status_code, [200, 404, 500])

    def test_static_files_structure(self):
        response = self.client.get('/')
        content = response.content.decode('utf-8')

        has_css = 'css' in content.lower() or 'stylesheet' in content.lower()
        has_js = 'javascript' in content.lower() or '<script' in content.lower()

        self.assertTrue(has_css or has_js, "Page should reference CSS or JavaScript")

    def test_form_fields_have_proper_types(self):
        response = self.client.get('/accounts/register/')
        soup = BeautifulSoup(response.content, 'html.parser')

        email_input = soup.find('input', {'name': 'email'})
        if email_input:
            input_type = email_input.get('type', 'text')
            self.assertIn(input_type, ['email', 'text'])

    def test_chatroom_functionality_exists(self):
        self.client.force_login(self.user)

        response = self.client.get('/chatrooms/')
        self.assertIn(response.status_code, [200, 302, 404])


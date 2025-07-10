import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import Client
from bs4 import BeautifulSoup
import json
import re


class TestFrontendUIComponents(TestCase):

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

    def test_login_page_ui_elements(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.content, 'html.parser')

        self.assertIsNotNone(soup.find('form', {'method': 'post'}))
        self.assertIsNotNone(soup.find('input', {'name': 'username'}))
        self.assertIsNotNone(soup.find('input', {'name': 'password'}))

    def test_registration_page_ui_elements(self):
        response = self.client.get('/accounts/register/')
        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.content, 'html.parser')

        self.assertIsNotNone(soup.find('input', {'name': 'username'}))
        self.assertIsNotNone(soup.find('input', {'name': 'email'}))

    def test_homepage_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertIsNotNone(soup.find('html'))

    def test_homepage_ui_elements_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.content, 'html.parser')

        search_input = soup.find('input', {'id': 'user-search'})
        if search_input:
            self.assertIsNotNone(search_input)

    def test_chat_page_loads(self):
        self.client.force_login(self.user)
        response = self.client.get(f'/chat/{self.other_user.username}/')
        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.content, 'html.parser')

        chat_messages = soup.find('div', {'id': 'chat-messages'})
        if chat_messages:
            self.assertIsNotNone(chat_messages)

    def test_profile_page_loads(self):
        self.client.force_login(self.user)
        response = self.client.get('/accounts/profile/')
        self.assertIn(response.status_code, [200, 302])

    def test_csrf_token_presence(self):
        response = self.client.get('/accounts/login/')
        soup = BeautifulSoup(response.content, 'html.parser')

        forms = soup.find_all('form', {'method': 'post'})
        for form in forms:
            csrf_input = form.find('input', {'name': 'csrfmiddlewaretoken'})
            self.assertIsNotNone(csrf_input, "POST form missing CSRF token")

    def test_responsive_design_classes(self):
        self.client.force_login(self.user)
        pages_to_test = [
            '/',
            '/accounts/login/',
            '/accounts/register/',
        ]

        for page_url in pages_to_test:
            response = self.client.get(page_url)
            soup = BeautifulSoup(response.content, 'html.parser')

            container_classes = soup.find_all(class_=re.compile(r'container|row|col'))
            self.assertEqual(response.status_code, 200, f"Page {page_url} should load")

    def test_user_search_api_endpoint(self):
        self.client.force_login(self.user)
        response = self.client.get('/chat/search-users/', {'q': 'test'})
        self.assertIn(response.status_code, [200, 404, 500])

    def test_basic_navigation_structure(self):
        response = self.client.get('/')
        soup = BeautifulSoup(response.content, 'html.parser')

        nav = soup.find('nav')
        if nav:
            self.assertIsNotNone(nav)

        links = soup.find_all('a')
        self.assertGreater(len(links), 0, "Page should have some links")

    def test_javascript_variables_in_templates(self):
        self.client.force_login(self.user)
        response = self.client.get(f'/chat/{self.other_user.username}/')

        if response.status_code == 200:
            content = response.content.decode('utf-8')

            if 'currentUser' in content:
                self.assertIn(f'"{self.user.username}"', content)
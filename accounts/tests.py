from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Profile

# Create your tests here.

class AccountsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_profile_creation(self):
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, Profile)
        self.assertEqual(self.user.profile.status, 'Offline')

    def test_login_view_get(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)

    def test_register_view_get(self):
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)

    def test_profile_view_requires_login(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)

    def test_profile_status_update(self):
        profile = self.user.profile
        profile.update_status('Online')
        self.assertEqual(profile.status, 'Online')

class IndexViewTestCase(TestCase):
    def test_index_view_anonymous(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
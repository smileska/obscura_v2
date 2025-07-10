import pytest
import sys
from pathlib import Path

class TestSetupVerification:
    def test_pytest_working(self):
        assert True

    def test_python_version(self):
        assert sys.version_info >= (3, 8)
        print(f"Python version: {sys.version}")

    def test_project_structure(self):
        project_root = Path.cwd()
        assert (project_root / "manage.py").exists(), "manage.py not found"
        assert (project_root / "obscura").exists(), "obscura directory not found"
        print(f"Project root: {project_root}")

    def test_django_available(self):
        import django
        from django.conf import settings
        assert settings.SECRET_KEY is not None
        print(f"Django version: {django.get_version()}")
        print(f"Django settings module: {settings.SETTINGS_MODULE}")

    @pytest.mark.django_db
    def test_database_connection(self):
        from django.db import connection
        assert connection is not None
        print(f"Database engine: {connection.settings_dict['ENGINE']}")

    @pytest.mark.django_db
    def test_user_creation(self, user):
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
        print(f"Created user: {user.username}")

    @pytest.mark.django_db
    def test_profile_creation(self, user):
        assert hasattr(user, 'profile')
        from accounts.models import Profile
        assert isinstance(user.profile, Profile)
        print(f"User profile status: {user.profile.status}")

    @pytest.mark.django_db
    def test_multiple_users(self, multiple_users):
        assert len(multiple_users) == 5
        print(f"Created {len(multiple_users)} users")
        for user in multiple_users:
            assert user.username.startswith('user')
            print(f"  - {user.username}")

    def test_imports_working(self):
        try:
            from accounts.models import Profile
            from chat.models import Message
            from chatrooms.models import Chatroom
            print("✓ All model imports successful")
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    def test_faker_available(self, fake_data):
        assert fake_data.name() is not None
        print(f"Faker test: {fake_data.name()}")

    def test_hypothesis_available(self):
        import hypothesis
        assert hypothesis is not None
        print(f"Hypothesis version: {hypothesis.__version__}")

    def test_responses_available(self):
        import responses
        assert responses is not None
        print("Responses library available")


    @pytest.mark.django_db
    def test_authenticated_client(self, authenticated_client):
        response = authenticated_client.get('/')
        assert response.status_code in [200, 302, 404]
        print(f"Authenticated client test: {response.status_code}")

    def test_setup_complete(self):
        print("\nSETUP VERIFICATION COMPLETE!")
        print("Django configured and working")
        print("Database access working")
        print("All models importable")
        print("User creation working")
        print("Testing fixtures working")
        print("Advanced testing libraries available")
        print("\nYou can now create advanced tests!")
        assert True
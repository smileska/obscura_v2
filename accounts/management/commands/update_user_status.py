from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta


class Command(BaseCommand):
    help = 'Update user online/offline status based on activity'

    def handle(self, *args, **options):
        inactive_threshold = timezone.now() - timedelta(minutes=5)

        inactive_users = User.objects.filter(
            profile__status='Online',
            profile__last_activity__lt=inactive_threshold
        )

        for user in inactive_users:
            user.profile.update_status('Offline')
            self.stdout.write(self.style.SUCCESS(f'User {user.username} set to offline'))

        self.stdout.write(self.style.SUCCESS(f'Updated {inactive_users.count()} users to offline status'))
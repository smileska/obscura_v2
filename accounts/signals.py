from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.auth.models import User

@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    user.profile.update_status('Online')

@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    if user:
        user.profile.update_status('Offline')
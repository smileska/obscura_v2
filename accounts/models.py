from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    STATUS_CHOICES = (
        ('Online', 'Online'),
        ('Offline', 'Offline'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    image = models.ImageField(upload_to='profile_pics', default='profile_pics/default.png')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Offline')
    verification_code = models.CharField(max_length=100, blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class UnverifiedUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    image = models.ImageField(upload_to='profile_pics', default='profile_pics/default.png')
    verification_code = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Unverified: {self.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
from django.db import models
from django.contrib.auth.models import User

class Chatroom(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, related_name='owned_chatrooms', on_delete=models.CASCADE)
    members = models.ManyToManyField(User, through='ChatroomUser', related_name='chatrooms')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ChatroomUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chatroom = models.ForeignKey(Chatroom, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'chatroom']


class ChatroomMessage(models.Model):
    chatroom = models.ForeignKey(Chatroom, related_name='messages', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='chatroom_messages', on_delete=models.CASCADE)
    content = models.TextField()
    image = models.ImageField(upload_to='chatroom_images/', blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sent_at']

    def __str__(self):
        return f"{self.user.username} in {self.chatroom.name}: {self.content[:20]}"


class ChatroomMessageReaction(models.Model):
    REACTION_CHOICES = [
        (1, '👍'),
        (2, '❤️'),
        (3, '😂'),
        (4, '😮'),
        (5, '😢'),
        (6, '🐴'),
        (7, '🍮'),
        (8, '🌹'),
    ]

    message = models.ForeignKey(ChatroomMessage, related_name='reactions', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='chatroom_reactions', on_delete=models.CASCADE)
    reaction_type = models.PositiveSmallIntegerField(choices=REACTION_CHOICES)

    class Meta:
        unique_together = ['message', 'user']


class SuggestedUser(models.Model):
    chatroom = models.ForeignKey(Chatroom, related_name='suggested_users', on_delete=models.CASCADE)
    suggested_user = models.ForeignKey(User, related_name='chatroom_suggestions', on_delete=models.CASCADE)
    suggested_by = models.ForeignKey(User, related_name='user_suggestions', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['chatroom', 'suggested_user']
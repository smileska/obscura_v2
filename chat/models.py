from django.db import models
from django.contrib.auth.models import User

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username} to {self.recipient.username}: {self.content[:20]}"


class MessageReaction(models.Model):
    REACTION_CHOICES = [
        (1, '👍'),
        (2, '❤️'),
        (3, '😂'),
        (4, '😮'),
        (5, '😢'),
    ]

    message = models.ForeignKey(Message, related_name='reactions', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='message_reactions', on_delete=models.CASCADE)
    reaction_type = models.PositiveSmallIntegerField(choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['message', 'user']
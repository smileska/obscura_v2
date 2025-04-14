from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings


class UserStatusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            if request.user.profile.status == 'Offline':
                request.user.profile.update_status('Online')

            request.user.profile.last_activity = timezone.now()
            request.user.profile.save(update_fields=['last_activity'])

        return response
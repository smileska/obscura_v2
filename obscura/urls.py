from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import JsonResponse
import os

def debug_media(request):
    media_root = settings.MEDIA_ROOT
    debug_info = {
        'MEDIA_ROOT': str(media_root),
        'MEDIA_URL': settings.MEDIA_URL,
        'media_exists': os.path.exists(media_root),
        'media_dirs': {},
        'recent_files': []
    }

    for subdir in ['chat_images', 'chatroom_images', 'profile_pics']:
        path = os.path.join(media_root, subdir)
        files = []
        if os.path.exists(path):
            try:
                files = os.listdir(path)[:5]
            except:
                files = ['Error reading directory']

        debug_info['media_dirs'][subdir] = {
            'path': path,
            'exists': os.path.exists(path),
            'files': files
        }

    return JsonResponse(debug_info, indent=2)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('accounts/', include('accounts.urls')),
    path('chat/', include('chat.urls', namespace='chat')),
    path('chatrooms/', include('chatrooms.urls', namespace='chatrooms')),
]

if settings.DEBUG or True:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
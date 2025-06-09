from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Message, MessageReaction
import os
import uuid
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings


@login_required
def chat_view(request, username):
    user = request.user
    chat_partner = get_object_or_404(User, username=username)

    if user == chat_partner:
        return redirect('index')

    context = {
        'chat_partner': chat_partner,
    }
    return render(request, 'chat/chat.html', context)


@login_required
def get_messages(request, username):
    user = request.user
    chat_partner = get_object_or_404(User, username=username)

    messages = Message.objects.filter(
        (Q(sender=user) & Q(recipient=chat_partner)) |
        (Q(sender=chat_partner) & Q(recipient=user))
    ).select_related('sender', 'recipient').order_by('timestamp')

    reaction_dict = {}
    reactions = MessageReaction.objects.filter(
        user=user,
        message__in=messages
    )
    for reaction in reactions:
        reaction_dict[reaction.message_id] = reaction.reaction_type

    messages_data = []
    for message in messages:
        image_url = None
        if message.image:
            try:
                image_url = message.image.url
                print(f"Message {message.id} image URL: {image_url}")
            except Exception as e:
                print(f"Error getting image URL for message {message.id}: {e}")
                image_url = None

        messages_data.append({
            'id': message.id,
            'sender': message.sender.username,
            'recipient': message.recipient.username,
            'message': message.content,
            'image_url': image_url,
            'timestamp': message.timestamp.isoformat(),
            'reaction_type': reaction_dict.get(message.id)
        })

    return JsonResponse(messages_data, safe=False)


@login_required
def react_to_message(request, message_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

    try:
        reaction_type = int(request.POST.get('reaction_type'))
        message = get_object_or_404(Message, id=message_id)
        user = request.user

        if user != message.sender and user != message.recipient:
            return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)

        reaction, created = MessageReaction.objects.update_or_create(
            message=message,
            user=user,
            defaults={'reaction_type': reaction_type}
        )

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def upload_image(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

    try:
        image = request.FILES.get('image')
        if not image:
            return JsonResponse({'success': False, 'error': 'No image provided'}, status=400)

        if not image.content_type.startswith('image/'):
            return JsonResponse({'success': False, 'error': 'File must be an image'}, status=400)

        _, ext = os.path.splitext(image.name)
        clean_filename = f"{uuid.uuid4().hex}{ext.lower()}"

        path = f'chat_images/{clean_filename}'

        saved_path = default_storage.save(path, ContentFile(image.read()))

        image_url = f'{settings.MEDIA_URL}{saved_path}'

        print(f"Image uploaded: {saved_path}, URL: {image_url}")

        return JsonResponse({'success': True, 'image_url': image_url})
    except Exception as e:
        print(f"Error uploading image: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def search_users(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'users': []})

    users = User.objects.filter(username__icontains=query).exclude(id=request.user.id)[:10]

    users_data = []
    for user in users:
        try:
            image_url = user.profile.image.url if user.profile.image else None
        except (AttributeError, ValueError):
            image_url = None

        users_data.append({
            'id': user.id,
            'username': user.username,
            'image': image_url
        })

    return JsonResponse({'users': users_data})


@login_required
def debug_images(request):
    debug_info = {
        'settings': {
            'MEDIA_ROOT': str(settings.MEDIA_ROOT),
            'MEDIA_URL': settings.MEDIA_URL,
            'DEBUG': settings.DEBUG,
        },
        'directories': {},
        'recent_messages': []
    }

    media_dirs = ['chat_images', 'chatroom_images', 'profile_pics']
    for dir_name in media_dirs:
        dir_path = os.path.join(settings.MEDIA_ROOT, dir_name)
        exists = os.path.exists(dir_path)
        files = []
        if exists:
            try:
                files = os.listdir(dir_path)
            except:
                files = ['Error reading directory']

        debug_info['directories'][dir_name] = {
            'path': dir_path,
            'exists': exists,
            'files': files[:10]
        }

    recent_messages = Message.objects.filter(image__isnull=False).order_by('-timestamp')[:5]

    for msg in recent_messages:
        msg_info = {
            'id': msg.id,
            'sender': msg.sender.username,
            'recipient': msg.recipient.username,
            'image_field': str(msg.image),
            'image_name': msg.image.name if msg.image else None,
            'image_url': None,
            'file_exists': False
        }

        try:
            if msg.image:
                msg_info['image_url'] = msg.image.url
                if hasattr(msg.image, 'path'):
                    msg_info['file_exists'] = os.path.exists(msg.image.path)
        except Exception as e:
            msg_info['error'] = str(e)

        debug_info['recent_messages'].append(msg_info)

    return JsonResponse(debug_info, indent=2)
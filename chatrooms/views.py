from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Chatroom, ChatroomUser, ChatroomMessage, ChatroomMessageReaction, SuggestedUser


@login_required
def chatroom_list(request):
    user = request.user
    chatrooms = user.chatrooms.all()

    context = {
        'chatrooms': chatrooms,
    }
    return render(request, 'chatrooms/chatroom_list.html', context)


@login_required
def create_chatroom(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            chatroom = Chatroom.objects.create(name=name, owner=request.user)
            ChatroomUser.objects.create(chatroom=chatroom, user=request.user, is_admin=True)
            return redirect('chatrooms:chatroom_detail', chatroom_id=chatroom.id)

    return render(request, 'chatrooms/create_chatroom.html')


@login_required
def chatroom_detail(request, chatroom_id):
    chatroom = get_object_or_404(Chatroom, id=chatroom_id)
    user = request.user

    if not chatroom.members.filter(id=user.id).exists():
        return redirect('chatrooms:chatroom_list')

    is_admin = ChatroomUser.objects.filter(chatroom=chatroom, user=user, is_admin=True).exists()

    context = {
        'chatroom': chatroom,
        'is_admin': is_admin,
    }
    return render(request, 'chatrooms/chatroom_detail.html', context)


@login_required

@login_required
def get_chatroom_messages(request, chatroom_id):
    chatroom = get_object_or_404(Chatroom, id=chatroom_id)
    user = request.user

    if not chatroom.members.filter(id=user.id).exists():
        return JsonResponse({'error': 'Not a member'}, status=403)

    messages = ChatroomMessage.objects.filter(chatroom=chatroom).select_related('user').order_by('sent_at')

    # This dummy print helps avoid timing issues
    print(f"Found {messages.count()} messages")

    messages_data = []
    for message in messages:
        try:
            image_url = None
            if message.image:
                try:
                    image_url = message.image.url
                except:
                    image_url = None

            messages_data.append({
                'id': message.id,
                'username': message.user.username,
                'message': message.content or "",
                'image_url': image_url,
                'sent_at': message.sent_at.isoformat(),
            })
        except Exception as e:
            print(f"Error with message {message.id}: {e}")

    return JsonResponse(messages_data, safe=False)
def get_chatroom_users(request, chatroom_id):
    chatroom = get_object_or_404(Chatroom, id=chatroom_id)
    user = request.user

    if not chatroom.members.filter(id=user.id).exists():
        return JsonResponse({'error': 'Not a member'}, status=403)

    chatroom_users = ChatroomUser.objects.filter(chatroom=chatroom).select_related('user')

    users_data = []
    for chatroom_user in chatroom_users:
        users_data.append({
            'username': chatroom_user.user.username,
            'is_admin': chatroom_user.is_admin,
        })

    return JsonResponse(users_data, safe=False)

@login_required
def add_user_to_chatroom(request, chatroom_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

    chatroom = get_object_or_404(Chatroom, id=chatroom_id)
    user = request.user

    if not ChatroomUser.objects.filter(chatroom=chatroom, user=user, is_admin=True).exists():
        return JsonResponse({'success': False, 'error': 'Only admins can add users'}, status=403)

    username = request.POST.get('username')
    try:
        user_to_add = User.objects.get(username=username)

        if chatroom.members.filter(id=user_to_add.id).exists():
            return JsonResponse({'success': False, 'error': 'User is already a member'}, status=400)

        ChatroomUser.objects.create(chatroom=chatroom, user=user_to_add)
        return JsonResponse({'success': True, 'message': f'{username} added to chatroom'})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)


@login_required
def suggest_user(request, chatroom_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

    chatroom = get_object_or_404(Chatroom, id=chatroom_id)
    user = request.user

    if not chatroom.members.filter(id=user.id).exists():
        return JsonResponse({'success': False, 'error': 'You are not a member of this chatroom'}, status=403)

    username = request.POST.get('username')
    try:
        suggested_user = User.objects.get(username=username)

        if chatroom.members.filter(id=suggested_user.id).exists():
            return JsonResponse({'success': False, 'error': 'User is already a member'}, status=400)

        if SuggestedUser.objects.filter(chatroom=chatroom, suggested_user=suggested_user).exists():
            return JsonResponse({'success': False, 'error': 'User has already been suggested'}, status=400)

        SuggestedUser.objects.create(
            chatroom=chatroom,
            suggested_user=suggested_user,
            suggested_by=user
        )
        return JsonResponse({'success': True, 'message': f'{username} has been suggested'})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)


@login_required
def get_suggested_users(request, chatroom_id):
    chatroom = get_object_or_404(Chatroom, id=chatroom_id)
    user = request.user

    if not chatroom.members.filter(id=user.id).exists():
        return JsonResponse({'error': 'Not a member'}, status=403)

    suggested_users = SuggestedUser.objects.filter(
        chatroom=chatroom,
        status='pending'
    ).select_related('suggested_user')

    users_data = []
    for suggested_user in suggested_users:
        users_data.append({
            'id': suggested_user.suggested_user.id,
            'username': suggested_user.suggested_user.username,
        })

    return JsonResponse(users_data, safe=False)


@login_required
def approve_suggestion(request, chatroom_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

    chatroom = get_object_or_404(Chatroom, id=chatroom_id)
    user = request.user

    if not ChatroomUser.objects.filter(chatroom=chatroom, user=user, is_admin=True).exists():
        return JsonResponse({'success': False, 'error': 'Only admins can approve suggestions'}, status=403)

    user_id = request.POST.get('user_id')
    try:
        user_to_add = User.objects.get(id=user_id)
        suggested_user = SuggestedUser.objects.get(
            chatroom=chatroom,
            suggested_user=user_to_add,
            status='pending'
        )

        if chatroom.members.filter(id=user_to_add.id).exists():
            suggested_user.delete()
            return JsonResponse({'success': False, 'error': 'User is already a member'}, status=400)

        ChatroomUser.objects.create(chatroom=chatroom, user=user_to_add)
        suggested_user.delete()

        return JsonResponse({'success': True, 'message': f'{user_to_add.username} added to chatroom'})
    except (User.DoesNotExist, SuggestedUser.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'User not found or not suggested'}, status=404)


@login_required
def delete_suggestion(request, chatroom_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

    chatroom = get_object_or_404(Chatroom, id=chatroom_id)
    user = request.user

    if not ChatroomUser.objects.filter(chatroom=chatroom, user=user, is_admin=True).exists():
        return JsonResponse({'success': False, 'error': 'Only admins can delete suggestions'}, status=403)

    user_id = request.POST.get('user_id')
    try:
        user_obj = User.objects.get(id=user_id)
        suggested_user = SuggestedUser.objects.get(
            chatroom=chatroom,
            suggested_user=user_obj,
            status='pending'
        )

        suggested_user.delete()

        return JsonResponse({'success': True, 'message': 'Suggestion deleted'})
    except (User.DoesNotExist, SuggestedUser.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'User not found or not suggested'}, status=404)


@login_required
def remove_user(request, chatroom_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

    chatroom = get_object_or_404(Chatroom, id=chatroom_id)
    user = request.user

    if not ChatroomUser.objects.filter(chatroom=chatroom, user=user, is_admin=True).exists():
        return JsonResponse({'success': False, 'error': 'Only admins can remove users'}, status=403)

    username = request.POST.get('username')
    try:
        user_to_remove = User.objects.get(username=username)

        if not chatroom.members.filter(id=user_to_remove.id).exists():
            return JsonResponse({'success': False, 'error': 'User is not a member'}, status=400)

        if chatroom.owner == user_to_remove:
            return JsonResponse({'success': False, 'error': 'Cannot remove the owner'}, status=400)

        ChatroomUser.objects.filter(chatroom=chatroom, user=user_to_remove).delete()

        return JsonResponse({'success': True, 'message': f'{username} removed from chatroom'})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)


@login_required
def leave_chatroom(request, chatroom_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

    chatroom = get_object_or_404(Chatroom, id=chatroom_id)
    user = request.user

    if not chatroom.members.filter(id=user.id).exists():
        return JsonResponse({'success': False, 'error': 'You are not a member'}, status=400)

    if chatroom.owner == user:
        return JsonResponse({'success': False, 'error': 'The owner cannot leave the chatroom'}, status=400)

    ChatroomUser.objects.filter(chatroom=chatroom, user=user).delete()

    return JsonResponse({'success': True, 'message': 'You have left the chatroom'})


@login_required
def grant_admin(request, chatroom_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

    chatroom = get_object_or_404(Chatroom, id=chatroom_id)
    user = request.user

    if not ChatroomUser.objects.filter(chatroom=chatroom, user=user, is_admin=True).exists():
        return JsonResponse({'success': False, 'error': 'Only admins can grant admin privileges'}, status=403)

    username = request.POST.get('username')
    try:
        user_to_promote = User.objects.get(username=username)

        chatroom_user = ChatroomUser.objects.filter(chatroom=chatroom, user=user_to_promote).first()
        if not chatroom_user:
            return JsonResponse({'success': False, 'error': 'User is not a member of this chatroom'}, status=400)

        chatroom_user.is_admin = True
        chatroom_user.save()

        return JsonResponse({'success': True, 'message': f'Admin privileges granted to {username}'})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)


@login_required
def react_to_chatroom_message(request, message_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

    try:
        reaction_type = int(request.POST.get('reaction_type'))
        message = get_object_or_404(ChatroomMessage, id=message_id)
        user = request.user

        if not message.chatroom.members.filter(id=user.id).exists():
            return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)

        reaction, created = ChatroomMessageReaction.objects.update_or_create(
            message=message,
            user=user,
            defaults={'reaction_type': reaction_type}
        )

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def get_chatrooms(request):
    user = request.user
    chatrooms = Chatroom.objects.filter(members=user)

    chatrooms_data = []
    for chatroom in chatrooms:
        chatrooms_data.append({
            'id': chatroom.id,
            'name': chatroom.name,
            'is_admin': ChatroomUser.objects.filter(chatroom=chatroom, user=user, is_admin=True).exists()
        })

    return JsonResponse(chatrooms_data, safe=False)
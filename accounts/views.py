from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from .models import UnverifiedUser
from django.contrib.auth import authenticate, update_session_auth_hash
import uuid
from django.core.mail import send_mail
from django.conf import settings


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')

            verification_code = str(uuid.uuid4())

            unverified_user = UnverifiedUser(
                username=username,
                email=email,
                password=password,
                verification_code=verification_code
            )

            if 'image' in request.FILES:
                unverified_user.image = request.FILES['image']

            unverified_user.save()

            verification_url = f"{request.scheme}://{request.get_host()}/accounts/verify-email/?code={verification_code}"
            send_mail(
                'Verify your Obscura Messenger account',
                f'Click the link to verify your email: {verification_url}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            messages.success(request,
                             f'Account created for {username}! Please check your email to verify your account.')
            return redirect('index')
    else:
        form = UserRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your account has been updated!')
            return redirect('accounts:profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'accounts/profile.html', context)


def verify_email(request):
    if request.method == 'GET':
        code = request.GET.get('code')
        if code:
            try:
                unverified_user = UnverifiedUser.objects.get(verification_code=code)


                user = User.objects.create_user(
                    username=unverified_user.username,
                    email=unverified_user.email,
                    password=unverified_user.password
                )


                user.profile.is_verified = True
                if unverified_user.image:
                    user.profile.image = unverified_user.image
                user.profile.save()

                unverified_user.delete()

                messages.success(request, 'Your email has been verified. You can now log in.')
                return redirect('accounts:email_verified')
            except UnverifiedUser.DoesNotExist:
                messages.error(request, 'Invalid verification code.')

        return redirect('index')


def email_verified(request):
    return render(request, 'accounts/email_verified.html')


@login_required
def update_username(request):
    if request.method == 'POST':
        new_username = request.POST.get('new_username')
        password = request.POST.get('password_for_username')

        user = authenticate(username=request.user.username, password=password)

        if user is not None:
            if User.objects.filter(username=new_username).exclude(pk=request.user.pk).exists():
                messages.error(request, 'Username is already taken.')
            else:
                user.username = new_username
                user.save()
                messages.success(request, 'Your username has been updated.')
        else:
            messages.error(request, 'Password is incorrect.')

        return redirect('accounts:profile')


@login_required
def update_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_new_password = request.POST.get('confirm_new_password')

        user = authenticate(username=request.user.username, password=current_password)

        if user is not None:
            if new_password == confirm_new_password:
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password has been updated.')
            else:
                messages.error(request, 'New passwords do not match.')
        else:
            messages.error(request, 'Current password is incorrect.')

        return redirect('accounts:profile')


@login_required
def update_profile_picture(request):
    if request.method == 'POST':
        if 'profile_picture' in request.FILES:
            profile_picture = request.FILES['profile_picture']
            request.user.profile.image = profile_picture
            request.user.profile.save()
            messages.success(request, 'Your profile picture has been updated.')

        return redirect('accounts:profile')


def user_profile(request, username):
    try:
        user = User.objects.get(username=username)
        return render(request, 'accounts/user_profile.html', {'profile_user': user})
    except User.DoesNotExist:
        messages.error(request, 'User does not exist.')
        return redirect('index')


@login_required
def toggle_dark_mode(request):
    if request.method == 'POST':
        dark_mode = request.session.get('dark_mode', False)
        request.session['dark_mode'] = not dark_mode
        request.session.modified = True
        return JsonResponse({'dark_mode': not dark_mode, 'success': True})

    return JsonResponse({'error': 'Invalid request method'}, status=400)
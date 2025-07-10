from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .api_views import login_api

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='index'), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('email-verified/', views.email_verified, name='email_verified'),
    path('profile/update/username/', views.update_username, name='update_username'),
    path('profile/update/password/', views.update_password, name='update_password'),
    path('profile/update/picture/', views.update_profile_picture, name='update_profile_picture'),
    path('<str:username>/', views.user_profile, name='user_profile'),
    path("api/login/", login_api, name="login_api"),
]
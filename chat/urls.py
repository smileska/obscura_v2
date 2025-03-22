from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('upload-image/', views.upload_image, name='upload_image'),
    path('<str:username>/', views.chat_view, name='chat_view'),
    path('<str:username>/messages/', views.get_messages, name='get_messages'),
    path('message/<int:message_id>/react/', views.react_to_message, name='react_to_message'),
    path('search-users/', views.search_users, name='search_users'),
]
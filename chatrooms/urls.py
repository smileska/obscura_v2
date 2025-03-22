from django.urls import path
from . import views

app_name = 'chatrooms'

urlpatterns = [
    path('', views.chatroom_list, name='chatroom_list'),
    path('create/', views.create_chatroom, name='create_chatroom'),
    path('<int:chatroom_id>/', views.chatroom_detail, name='chatroom_detail'),
    path('<int:chatroom_id>/messages/', views.get_chatroom_messages, name='get_chatroom_messages'),
    path('<int:chatroom_id>/users/', views.get_chatroom_users, name='get_chatroom_users'),
    path('<int:chatroom_id>/add-user/', views.add_user_to_chatroom, name='add_user_to_chatroom'),
    path('<int:chatroom_id>/suggest-user/', views.suggest_user, name='suggest_user'),
    path('<int:chatroom_id>/suggested-users/', views.get_suggested_users, name='get_suggested_users'),
    path('<int:chatroom_id>/approve-suggestion/', views.approve_suggestion, name='approve_suggestion'),
    path('<int:chatroom_id>/delete-suggestion/', views.delete_suggestion, name='delete_suggestion'),
    path('<int:chatroom_id>/remove-user/', views.remove_user, name='remove_user'),
    path('<int:chatroom_id>/leave/', views.leave_chatroom, name='leave_chatroom'),
    path('<int:chatroom_id>/grant-admin/', views.grant_admin, name='grant_admin'),
    path('message/<int:message_id>/react/', views.react_to_chatroom_message, name='react_to_message'),
    path('get-chatrooms/', views.get_chatrooms, name='get_chatrooms'),
]
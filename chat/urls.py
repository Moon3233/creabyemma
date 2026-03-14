from django.urls import path
from . import views

urlpatterns = [
    path('conversation/', views.chat_guest_conversation, name='chat-guest-conversation'),
    path('guest-info/', views.chat_guest_update_info, name='chat-guest-update-info'),
    path('admin/conversations/', views.chat_admin_conversations, name='chat-admin-conversations'),
    path('admin/mark-all-read/', views.chat_admin_mark_all_read, name='chat-admin-mark-all-read'),
    path(
        'admin/conversations/<int:conversation_id>/messages/',
        views.chat_admin_conversation_messages,
        name='chat-admin-conversation-messages',
    ),
    path(
        'admin/conversations/<int:conversation_id>/mark-read/',
        views.chat_admin_mark_read,
        name='chat-admin-mark-read',
    ),
    path(
        'admin/conversations/<int:conversation_id>/block/',
        views.chat_admin_conversation_block,
        name='chat-admin-conversation-block',
    ),
    path(
        'admin/conversations/<int:conversation_id>/unblock/',
        views.chat_admin_conversation_unblock,
        name='chat-admin-conversation-unblock',
    ),
    path(
        'admin/conversations/<int:conversation_id>/',
        views.chat_admin_conversation_delete,
        name='chat-admin-conversation-delete',
    ),
    path('admin/unread-count/', views.chat_admin_unread_count, name='chat-admin-unread-count'),
]

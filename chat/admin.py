from django.contrib import admin
from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('created_at',)
    ordering = ('created_at',)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'guest_token', 'guest_email', 'guest_first_name', 'guest_last_name', 'is_blocked', 'updated_at')
    list_filter = ('is_blocked',)
    search_fields = ('guest_email', 'guest_first_name', 'guest_last_name', 'guest_token')
    inlines = [MessageInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender_type', 'content_short', 'created_at', 'is_read_by_admin')
    list_filter = ('sender_type', 'is_read_by_admin')

    def content_short(self, obj):
        return (obj.content[:60] + '…') if len(obj.content) > 60 else obj.content
    content_short.short_description = 'Contenu'

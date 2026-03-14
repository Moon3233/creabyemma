"""
WebSocket consumer pour le chat en temps réel.
Visiteurs : ws/chat/<guest_token>/ (pas d'auth).
Admin : ws/chat/admin/ (auth par session cookie).
"""
import json
import re
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser


class ChatConsumer(AsyncWebsocketConsumer):
    GROUP_ADMIN = "chat_admin"

    async def connect(self):
        self.scope["user"] = self.scope.get("user") or AnonymousUser()
        self.guest_token = None
        self.is_admin = False
        path = self.scope.get("path", "")
        kwargs = self.scope.get("url_route", {}).get("kwargs", {})

        if path.rstrip("/").endswith("/admin"):
            user = self.scope["user"]
            if not user or not user.is_authenticated:
                await self.close(4001)
                return
            if not (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)):
                await self.close(4003)
                return
            self.is_admin = True
            self.channel_group = self.GROUP_ADMIN
        else:
            self.guest_token = kwargs.get("guest_token")
            if not self.guest_token or not re.match(r"^[a-f0-9-]{36}$", self.guest_token, re.I):
                await self.close(4002)
                return
            self.channel_group = f"chat_guest_{self.guest_token}"

        await self.channel_layer.group_add(self.channel_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "channel_group"):
            await self.channel_layer.group_discard(self.channel_group, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"type": "error", "message": "JSON invalide"}))
            return

        msg_type = data.get("type", "")

        if msg_type == "guest_message":
            if not self.guest_token:
                return
            content = (data.get("content") or "").strip()
            if not content:
                await self.send(text_data=json.dumps({"type": "error", "message": "Message vide"}))
                return
            if len(content) > 2000:
                await self.send(text_data=json.dumps({"type": "error", "message": "Message trop long"}))
                return
            result = await self._save_guest_message(content)
            if result.get("error"):
                await self.send(text_data=json.dumps({"type": "error", "message": result["error"]}))
                return
            await self.channel_layer.group_send(
                self.GROUP_ADMIN,
                {
                    "type": "chat_new_message",
                    "message": result["message"],
                    "conversation_id": result["conversation_id"],
                },
            )
            await self.send(text_data=json.dumps({
                "type": "message_sent",
                "message": result["message"],
            }))

        elif msg_type == "admin_message":
            if not self.is_admin:
                return
            content = (data.get("content") or "").strip()
            conversation_id = data.get("conversation_id")
            if not content or not conversation_id:
                await self.send(text_data=json.dumps({"type": "error", "message": "Données manquantes"}))
                return
            if len(content) > 2000:
                await self.send(text_data=json.dumps({"type": "error", "message": "Message trop long"}))
                return
            result = await self._save_admin_message(int(conversation_id), content)
            if result.get("error"):
                await self.send(text_data=json.dumps({"type": "error", "message": result["error"]}))
                return
            guest_token = result.get("guest_token")
            if guest_token:
                await self.channel_layer.group_send(
                    f"chat_guest_{guest_token}",
                    {
                        "type": "chat_new_message",
                        "message": result["message"],
                        "conversation_id": result["conversation_id"],
                    },
                )
            await self.send(text_data=json.dumps({
                "type": "message_sent",
                "message": result["message"],
            }))

        elif msg_type == "admin_update_guest_info":
            if not self.is_admin:
                return
            conversation_id = data.get("conversation_id")
            info = data.get("info", {})
            if conversation_id:
                await self._update_guest_info(int(conversation_id), info)

        elif msg_type == "ping":
            await self.send(text_data=json.dumps({"type": "pong"}))

    async def chat_new_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "new_message",
            "message": event["message"],
            "conversation_id": event["conversation_id"],
        }))

    async def chat_guest_info_updated(self, event):
        await self.send(text_data=json.dumps({
            "type": "guest_info_updated",
            "conversation_id": event["conversation_id"],
            "guest_email": event.get("guest_email"),
            "guest_phone": event.get("guest_phone"),
            "guest_first_name": event.get("guest_first_name"),
            "guest_last_name": event.get("guest_last_name"),
        }))

    def _guest_label(self, conv):
        parts = [conv.guest_first_name, conv.guest_last_name]
        if any(parts):
            return " ".join(p for p in parts if p).strip()
        if conv.guest_email:
            return conv.guest_email
        if conv.guest_phone:
            return conv.guest_phone
        return str(conv.guest_token)[:8] + "…"

    @database_sync_to_async
    def _save_guest_message(self, content):
        from .models import Conversation, Message
        import uuid as uuid_mod
        try:
            token_uuid = uuid_mod.UUID(self.guest_token)
        except ValueError:
            return {"error": "Token invalide"}
        conv, _ = Conversation.objects.get_or_create(guest_token=token_uuid)
        if conv.is_blocked:
            return {"error": "Vous avez été bloqué et ne pouvez plus envoyer de messages."}
        msg = Message.objects.create(
            conversation=conv,
            sender_type=Message.SenderType.GUEST,
            content=content[:2000],
        )
        return {
            "message": {
                "id": msg.id,
                "conversation_id": conv.id,
                "sender_type": "guest",
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
            },
            "conversation_id": conv.id,
            "guest_label": self._guest_label(conv),
        }

    @database_sync_to_async
    def _save_admin_message(self, conversation_id, content):
        from .models import Conversation, Message
        try:
            conv = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return {"error": "Conversation introuvable"}
        msg = Message.objects.create(
            conversation=conv,
            sender_type=Message.SenderType.ADMIN,
            user=self.scope["user"],
            content=content[:2000],
        )
        return {
            "message": {
                "id": msg.id,
                "conversation_id": conv.id,
                "sender_type": "admin",
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
            },
            "conversation_id": conv.id,
            "guest_token": str(conv.guest_token),
        }

    @database_sync_to_async
    def _update_guest_info(self, conversation_id, info):
        from .models import Conversation
        try:
            conv = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return
        if "email" in info:
            conv.guest_email = info["email"] or None
        if "phone" in info:
            conv.guest_phone = info["phone"] or None
        if "first_name" in info:
            conv.guest_first_name = info["first_name"] or None
        if "last_name" in info:
            conv.guest_last_name = info["last_name"] or None
        conv.save(update_fields=["guest_email", "guest_phone", "guest_first_name", "guest_last_name", "updated_at"])

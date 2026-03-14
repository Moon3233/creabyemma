"""
Vues API pour le chat (sans DRF : JsonResponse).
"""
import json
import uuid
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Conversation, Message


def _require_staff(view_func):
    """Décorateur : requiert utilisateur connecté staff ou superuser. Retourne 401/403 en JSON."""
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Non authentifié'}, status=401)
        if not (request.user.is_staff or request.user.is_superuser):
            return JsonResponse({'error': 'Accès réservé aux administrateurs'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapped


@require_http_methods(['GET'])
def chat_guest_conversation(request):
    """
    GET /api/chat/conversation/?token=<uuid>
    """
    token_str = request.GET.get('token')
    if not token_str:
        return JsonResponse({'error': 'Token manquant'}, status=400)
    try:
        token_uuid = uuid.UUID(token_str)
    except ValueError:
        return JsonResponse({'error': 'Token invalide'}, status=400)

    conv = Conversation.objects.filter(guest_token=token_uuid).first()
    if conv is None:
        return JsonResponse({
            'conversation': {
                'id': None,
                'guest_token': str(token_uuid),
                'guest_email': None,
                'guest_phone': None,
                'guest_first_name': None,
                'guest_last_name': None,
                'created_at': None,
                'updated_at': None,
            },
            'messages': [],
            'is_new': True,
        })

    messages = list(
        conv.messages.order_by('created_at').values('id', 'sender_type', 'content', 'created_at')
    )
    for m in messages:
        m['created_at'] = m['created_at'].isoformat()

    return JsonResponse({
        'conversation': {
            'id': conv.id,
            'guest_token': str(conv.guest_token),
            'guest_email': conv.guest_email,
            'guest_phone': conv.guest_phone,
            'guest_first_name': conv.guest_first_name,
            'guest_last_name': conv.guest_last_name,
            'created_at': conv.created_at.isoformat(),
            'updated_at': conv.updated_at.isoformat(),
        },
        'messages': messages,
        'is_new': False,
    })


@require_http_methods(['POST'])
@csrf_exempt
def chat_guest_update_info(request):
    """
    POST /api/chat/guest-info/
    Body JSON: { "token": "<uuid>", "email": "...", "phone": "...", "first_name": "...", "last_name": "..." }
    """
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalide'}, status=400)
    token_str = data.get('token')
    if not token_str:
        return JsonResponse({'error': 'Token manquant'}, status=400)
    try:
        token_uuid = uuid.UUID(token_str)
    except ValueError:
        return JsonResponse({'error': 'Token invalide'}, status=400)
    try:
        conv = Conversation.objects.get(guest_token=token_uuid)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation introuvable'}, status=404)

    for field, key in [
        ('guest_email', 'email'),
        ('guest_phone', 'phone'),
        ('guest_first_name', 'first_name'),
        ('guest_last_name', 'last_name'),
    ]:
        if key in data:
            val = data.get(key)
            setattr(conv, field, (val or '').strip() or None)
    conv.save(update_fields=['guest_email', 'guest_phone', 'guest_first_name', 'guest_last_name', 'updated_at'])

    return JsonResponse({
        'conversation': {
            'id': conv.id,
            'guest_email': conv.guest_email,
            'guest_phone': conv.guest_phone,
            'guest_first_name': conv.guest_first_name,
            'guest_last_name': conv.guest_last_name,
        },
    })


@require_http_methods(['GET'])
@_require_staff
def chat_admin_conversations(request):
    """GET /api/chat/admin/conversations/"""
    convs = Conversation.objects.annotate(
        unread_count=Count('messages', filter=Q(messages__sender_type='guest', messages__is_read_by_admin=False)),
    ).order_by('-updated_at')

    result = []
    for c in convs:
        last_msg = c.messages.order_by('-created_at').first()
        result.append({
            'id': c.id,
            'guest_token': str(c.guest_token),
            'guest_email': c.guest_email,
            'guest_phone': c.guest_phone,
            'guest_first_name': c.guest_first_name,
            'guest_last_name': c.guest_last_name,
            'is_blocked': c.is_blocked,
            'created_at': c.created_at.isoformat(),
            'updated_at': c.updated_at.isoformat(),
            'last_message': {
                'content': last_msg.content[:100] if last_msg else None,
                'created_at': last_msg.created_at.isoformat() if last_msg else None,
                'sender_type': last_msg.sender_type if last_msg else None,
            } if last_msg else None,
            'unread_count': c.unread_count,
        })
    return JsonResponse({'conversations': result})


@require_http_methods(['GET'])
@_require_staff
def chat_admin_conversation_messages(request, conversation_id):
    """GET /api/chat/admin/conversations/<id>/messages/"""
    try:
        conv = Conversation.objects.get(id=conversation_id)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation introuvable'}, status=404)
    messages = list(
        conv.messages.order_by('created_at').values(
            'id', 'sender_type', 'content', 'created_at', 'is_read_by_admin'
        )
    )
    for m in messages:
        m['created_at'] = m['created_at'].isoformat()
    return JsonResponse({
        'conversation': {
            'id': conv.id,
            'guest_token': str(conv.guest_token),
            'guest_email': conv.guest_email,
            'guest_phone': conv.guest_phone,
            'guest_first_name': conv.guest_first_name,
            'guest_last_name': conv.guest_last_name,
        },
        'messages': messages,
    })


@require_http_methods(['POST'])
@_require_staff
def chat_admin_mark_read(request, conversation_id):
    """POST /api/chat/admin/conversations/<id>/mark-read/"""
    try:
        conv = Conversation.objects.get(id=conversation_id)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation introuvable'}, status=404)
    updated = conv.messages.filter(sender_type='guest', is_read_by_admin=False).update(is_read_by_admin=True)
    return JsonResponse({'marked': updated})


@require_http_methods(['POST'])
@_require_staff
def chat_admin_mark_all_read(request):
    """POST /api/chat/admin/mark-all-read/"""
    updated = Message.objects.filter(sender_type='guest', is_read_by_admin=False).update(is_read_by_admin=True)
    return JsonResponse({'marked': updated})


@require_http_methods(['GET'])
@_require_staff
def chat_admin_unread_count(request):
    """GET /api/chat/admin/unread-count/"""
    count = Message.objects.filter(sender_type='guest', is_read_by_admin=False).count()
    return JsonResponse({'unread_count': count})


@require_http_methods(['POST'])
@_require_staff
def chat_admin_conversation_block(request, conversation_id):
    """POST /api/chat/admin/conversations/<id>/block/"""
    try:
        conv = Conversation.objects.get(id=conversation_id)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation introuvable'}, status=404)
    conv.is_blocked = True
    conv.save(update_fields=['is_blocked', 'updated_at'])
    return JsonResponse({'blocked': True})


@require_http_methods(['POST'])
@_require_staff
def chat_admin_conversation_unblock(request, conversation_id):
    """POST /api/chat/admin/conversations/<id>/unblock/"""
    try:
        conv = Conversation.objects.get(id=conversation_id)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation introuvable'}, status=404)
    conv.is_blocked = False
    conv.save(update_fields=['is_blocked', 'updated_at'])
    return JsonResponse({'blocked': False})


@require_http_methods(['DELETE'])
@_require_staff
def chat_admin_conversation_delete(request, conversation_id):
    """DELETE /api/chat/admin/conversations/<id>/"""
    try:
        conv = Conversation.objects.get(id=conversation_id)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation introuvable'}, status=404)
    conv.delete()
    return JsonResponse({'deleted': True})

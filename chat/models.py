"""
Modèles pour le chat visiteur / admin (sans connexion pour les visiteurs).
"""
from django.db import models
from django.conf import settings


class Conversation(models.Model):
    """
    Conversation entre un visiteur anonyme (identifié par token) et l'admin.
    """
    guest_token = models.UUIDField(
        unique=True,
        db_index=True,
        verbose_name='Token visiteur',
        help_text='UUID généré côté client, stocké en localStorage',
    )
    guest_email = models.EmailField(blank=True, null=True, verbose_name='Email visiteur')
    guest_phone = models.CharField(max_length=17, blank=True, null=True, verbose_name='Téléphone visiteur')
    guest_first_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Prénom visiteur')
    guest_last_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Nom visiteur')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Date de modification')
    is_blocked = models.BooleanField(
        default=False,
        verbose_name='Bloqué',
        help_text='Si True, le visiteur ne peut plus envoyer de messages',
    )

    class Meta:
        verbose_name = 'Conversation chat'
        verbose_name_plural = 'Conversations chat'
        ordering = ['-updated_at']

    def __str__(self):
        label = (
            self.guest_first_name or self.guest_last_name
            or self.guest_email
            or str(self.guest_token)[:8]
        )
        return f"Conversation {label}"


class Message(models.Model):
    """Message dans une conversation chat."""
    class SenderType(models.TextChoices):
        GUEST = 'guest', 'Visiteur'
        ADMIN = 'admin', 'Administrateur'

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Conversation',
    )
    sender_type = models.CharField(
        max_length=10,
        choices=SenderType.choices,
        verbose_name='Expéditeur',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_messages',
        verbose_name='Utilisateur (admin)',
        help_text='Rempli uniquement si sender_type=admin',
    )
    content = models.TextField(verbose_name='Contenu')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'envoi")
    is_read_by_admin = models.BooleanField(
        default=False,
        verbose_name='Lu par l\'admin',
        help_text='Pour les messages guest : marqué lu quand l\'admin les voit',
    )

    class Meta:
        verbose_name = 'Message chat'
        verbose_name_plural = 'Messages chat'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.get_sender_type_display()} - {self.content[:50]}"

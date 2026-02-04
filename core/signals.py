from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Notification


@receiver(post_save, sender=Notification)
def email_notification(sender, instance, created, **kwargs):
    if not created:
        return

    recipient = instance.recipient
    if not recipient or not recipient.email:
        return

    subject = f"SIMS Notification: {instance.verb}"
    actor_name = instance.actor.get_full_name() or instance.actor.username if instance.actor else "System"
    link = instance.link or ""

    body_lines = [
        f"Hello {recipient.get_full_name() or recipient.username},",
        "",
        instance.verb,
        f"Actor: {actor_name}",
    ]
    if instance.description:
        body_lines.append(f"Details: {instance.description}")
    if link:
        body_lines.extend(["", f"Open: {link}"])
    body_lines.extend(["", "— SIMS"])

    if not settings.DEFAULT_FROM_EMAIL or not settings.EMAIL_HOST_USER:
        return

    send_mail(
        subject=subject,
        message="\n".join(body_lines),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient.email],
        fail_silently=True,
    )

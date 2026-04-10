from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .activity import log_system_activity
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

    # Prepare HTML content
    context = {
        'verb': instance.verb,
        'actor_name': actor_name,
        'full_link': link,
    }
    html_message = render_to_string('emails/notification.html', context)
    plain_message = strip_tags(html_message)

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient.email],
        html_message=html_message,
        fail_silently=True,
    )


@receiver(user_logged_in)
def log_user_logged_in(sender, request, user, **kwargs):
    log_system_activity(
        user=user,
        event_type='auth',
        action='User logged in',
        description='Successful sign-in to the system.',
        request=request,
        status_code=200,
    )


@receiver(user_logged_out)
def log_user_logged_out(sender, request, user, **kwargs):
    if not user:
        return
    log_system_activity(
        user=user,
        event_type='auth',
        action='User logged out',
        description='Signed out of the system.',
        request=request,
        status_code=200,
    )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    username = (credentials or {}).get('username', '')
    log_system_activity(
        username=username,
        event_type='security',
        action='Failed login attempt',
        description='Authentication failed for supplied credentials.',
        request=request,
        status_code=401,
    )

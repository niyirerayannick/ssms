from .models import Notification


def notifications(request):
    """Provide notification data for navbar."""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}

    items = Notification.objects.filter(recipient=user).order_by('-created_at')
    return {
        'notification_unread_count': items.filter(is_read=False).count(),
        'notification_items': items[:5],
    }

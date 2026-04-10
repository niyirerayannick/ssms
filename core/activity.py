from django.db import DatabaseError, OperationalError

from .models import SystemActivityLog


def get_client_ip(request):
    """Return the best-effort client IP address for the current request."""
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_system_activity(
    *,
    user=None,
    username='',
    event_type=SystemActivityLog.EVENT_ACTION,
    action='',
    description='',
    request=None,
    path='',
    method='',
    status_code=None,
    metadata=None,
):
    """Persist an audit record without breaking the user request on failure."""
    try:
        SystemActivityLog.objects.create(
            user=user if getattr(user, 'is_authenticated', False) else None,
            username=username or (user.username if getattr(user, 'username', None) else ''),
            event_type=event_type,
            action=action or 'System activity',
            description=description or '',
            path=path or (((getattr(request, 'path', '') or '')[:255]) if request else ''),
            method=method or ((getattr(request, 'method', '') or '') if request else ''),
            status_code=status_code,
            ip_address=get_client_ip(request) if request else None,
            user_agent=(request.META.get('HTTP_USER_AGENT', '')[:255] if request else ''),
            metadata=metadata or {},
        )
    except (DatabaseError, OperationalError):
        return


def set_audit_context(request, *, action, description='', event_type=SystemActivityLog.EVENT_ACTION, metadata=None):
    """Attach audit metadata to a request so middleware can persist it once."""
    request._audit_action = action
    request._audit_description = description
    request._audit_event_type = event_type
    request._audit_metadata = metadata or {}

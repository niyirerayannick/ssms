from .activity import log_system_activity
from .models import SystemActivityLog


class SystemActivityLogMiddleware:
    """Capture successful authenticated actions in a central audit trail."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self._log_request(request, response)
        return response

    def _log_request(self, request, response):
        if getattr(request, '_skip_system_activity_log', False):
            return
        if response.status_code >= 400:
            return
        if not getattr(request, 'user', None) or not request.user.is_authenticated:
            return

        explicit_action = getattr(request, '_audit_action', '')
        should_log_method = request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}
        is_download = request.method == 'GET' and (
            'export' in request.path
            or 'download' in request.path
            or response.has_header('Content-Disposition')
        )
        if not (explicit_action or should_log_method or is_download):
            return

        event_type = getattr(request, '_audit_event_type', None) or self._infer_event_type(request, is_download)
        action = explicit_action or self._infer_action_label(request, is_download)
        description = getattr(request, '_audit_description', '') or self._infer_description(request)
        metadata = getattr(request, '_audit_metadata', {})

        log_system_activity(
            user=request.user,
            event_type=event_type,
            action=action,
            description=description,
            request=request,
            status_code=response.status_code,
            metadata=metadata,
        )

    def _infer_event_type(self, request, is_download):
        if is_download:
            return SystemActivityLog.EVENT_EXPORT
        if any(token in request.path for token in ('login', 'logout')):
            return SystemActivityLog.EVENT_AUTH
        return SystemActivityLog.EVENT_ACTION

    def _infer_action_label(self, request, is_download):
        match = getattr(request, 'resolver_match', None)
        route_name = match.url_name.replace('_', ' ').title() if match and match.url_name else 'Request'

        if is_download:
            return f'Export {route_name}'
        if request.method == 'DELETE':
            return f'Delete via {route_name}'
        if request.method in {'PUT', 'PATCH'}:
            return f'Update via {route_name}'
        if request.method == 'POST':
            return f'Submit via {route_name}'
        return route_name

    def _infer_description(self, request):
        match = getattr(request, 'resolver_match', None)
        view_name = match.view_name if match and match.view_name else request.path
        return f'{request.method} {view_name}'


import json
import uuid
from django.utils import timezone
from .models import AuditLog

# Fields that must never appear in audit logs
_SENSITIVE_FIELDS = frozenset({
    'password', 'token', 'access_token', 'refresh_token', 'secret',
    'passport_series', 'passport_number', 'passport_issued_by',
    'snils', 'insurance_policy',
})


def _scrub(obj, depth=0):
    if depth > 5:
        return obj
    if isinstance(obj, dict):
        return {
            k: '***' if k in _SENSITIVE_FIELDS else _scrub(v, depth + 1)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_scrub(item, depth + 1) for item in obj]
    return obj


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in ('POST', 'PUT', 'PATCH') and request.body:
            try:
                request._cached_body = request.body.decode('utf-8')
            except Exception:
                request._cached_body = None

        response = self.get_response(request)
        self._log_audit(request, response)
        return response

    def _log_audit(self, request, response):
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return

        user = request.user if request.user.is_authenticated else None

        entity_type = None
        entity_id = None
        path_parts = request.path.split('/')

        if len(path_parts) >= 3:
            segment = path_parts[2].rstrip('s')
            known = {'patient', 'preparation', 'template', 'iol-calculation', 'feedback', 'media'}
            if segment in known:
                entity_type = segment
                if len(path_parts) >= 4 and path_parts[3]:
                    try:
                        entity_id = uuid.UUID(path_parts[3])
                    except ValueError:
                        pass

        action = f"{request.method} {request.path}"

        if request.method in ('POST', 'PUT', 'PATCH'):
            cached = getattr(request, '_cached_body', None)
            if cached:
                try:
                    body = _scrub(json.loads(cached))
                    body_str = json.dumps(body, ensure_ascii=False)[:500]
                    action += f" | Body: {body_str}"
                except (json.JSONDecodeError, Exception):
                    pass

        if request.method != 'GET' or response.status_code >= 400:
            AuditLog.objects.create(
                user=user,
                action=action[:1000],
                entity_type=entity_type,
                entity_id=entity_id,
            )

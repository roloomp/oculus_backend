import json
import uuid
from django.utils import timezone
from .models import AuditLog


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in ['POST', 'PUT', 'PATCH'] and request.body:
            try:
                body = request.body.decode('utf-8')
                request._cached_body = body  # Сохраняем в кэш
            except:
                request._cached_body = None

        response = self.get_response(request)

        self.log_audit(request, response)

        return response

    def log_audit(self, request, response):
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return

        user = request.user if request.user.is_authenticated else None

        entity_type = None
        entity_id = None

        path_parts = request.path.split('/')
        if len(path_parts) >= 3:
            if path_parts[2] in ['patients', 'preparations', 'templates', 'iol-calculations', 'feedback', 'media']:
                entity_type = path_parts[2].rstrip('s')
                if len(path_parts) >= 4 and path_parts[3]:
                    try:
                        entity_id = uuid.UUID(path_parts[3])
                    except ValueError:
                        pass

        action = f"{request.method} {request.path}"

        if request.method in ['POST', 'PUT', 'PATCH'] and hasattr(request, '_cached_body') and request._cached_body:
            try:
                body = json.loads(request._cached_body)
                if 'password' in body:
                    body['password'] = '***'
                if 'token' in body:
                    body['token'] = '***'
                action += f" | Data: {json.dumps(body, ensure_ascii=False)}"
            except:
                pass

        if request.method != 'GET' or response.status_code >= 400:
            AuditLog.objects.create(
                user=user,
                action=action[:1000],
                entity_type=entity_type,
                entity_id=entity_id
            )
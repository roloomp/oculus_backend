from rest_framework.permissions import BasePermission, IsAuthenticated


class IsMedicalStaff(BasePermission):
    """Allows access to doctors, surgeons and admins only."""
    message = 'Доступ разрешен только медицинскому персоналу.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in ('district_doctor', 'surgeon', 'admin')
        )


class IsSurgeon(BasePermission):
    """Allows access to surgeons and admins only."""
    message = 'Доступ разрешен только хирургам.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in ('surgeon', 'admin')
        )


class IsAdmin(BasePermission):
    """Allows access to admins only."""
    message = 'Доступ разрешен только администраторам.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'admin'
        )


class IsAdminOrReadOnly(BasePermission):
    """Read-only for medical staff; write access for admins only."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return request.user.role in ('district_doctor', 'surgeon', 'admin')
        return request.user.role == 'admin'

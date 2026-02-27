from rest_framework.permissions import BasePermission, IsAuthenticated


class IsMedicalStaff(BasePermission):
    message = 'Доступ разрешен только медицинскому персоналу.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in ('district_doctor', 'surgeon', 'admin')
        )


class IsSurgeon(BasePermission):
    message = 'Доступ разрешен только хирургам.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in ('surgeon', 'admin')
        )


class IsAdmin(BasePermission):
    message = 'Доступ разрешен только администраторам.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'admin'
        )


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return request.user.role in ('district_doctor', 'surgeon', 'admin')
        return request.user.role == 'admin'


class IsPatientOwner(BasePermission):
    message = 'Вы можете просматривать только свои данные.'
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'patient'
        )

    def has_object_permission(self, request, view, obj):
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            return False
        return (
            request.user.linked_patient_id is not None and
            str(obj.pk) == str(request.user.linked_patient_id)
        )

class _EitherPermission(BasePermission):
    def __init__(self, perm_a: BasePermission, perm_b: BasePermission):
        self.perm_a = perm_a
        self.perm_b = perm_b

    def has_permission(self, request, view):
        return (
            self.perm_a.has_permission(request, view) or
            self.perm_b.has_permission(request, view)
        )

    def has_object_permission(self, request, view, obj):
        if self.perm_a.has_permission(request, view):
            return True
        return self.perm_b.has_object_permission(request, view, obj)

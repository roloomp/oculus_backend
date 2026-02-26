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


class IsPatientOwner(BasePermission):
    """
    Allows a patient-role user to read their own Patient record.
    Used together with IsMedicalStaff via OR logic in get_permissions().
    Relies on User.linked_patient FK added to the User model.
    """
    message = 'Вы можете просматривать только свои данные.'

    def has_permission(self, request, view):
        # Patient-role users pass view-level check; object check enforces ownership
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'patient'
        )

    def has_object_permission(self, request, view, obj):
        # Only allow read methods for patients
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            return False
        # obj is a Patient instance; user must have this Patient linked
        return (
            request.user.linked_patient_id is not None and
            str(obj.pk) == str(request.user.linked_patient_id)
        )

class _EitherPermission(BasePermission):
    """
    Passes if EITHER of two permission instances passes — both at view level
    and at object level. Used so patients can read their own record while
    medical staff retain full access.
    """
    def __init__(self, perm_a: BasePermission, perm_b: BasePermission):
        self.perm_a = perm_a
        self.perm_b = perm_b

    def has_permission(self, request, view):
        return (
            self.perm_a.has_permission(request, view) or
            self.perm_b.has_permission(request, view)
        )

    def has_object_permission(self, request, view, obj):
        # If perm_a grants view-level access (medical staff), allow object too
        if self.perm_a.has_permission(request, view):
            return True
        # Otherwise fall through to perm_b object check (patient owner)
        return self.perm_b.has_object_permission(request, view, obj)

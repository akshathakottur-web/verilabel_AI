from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    message = 'Only an Admin can do this.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == 'admin')


class IsInspectorOrAdmin(BasePermission):
    message = 'Only an Inspector or an Admin can do this.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role in ('inspector', 'admin'))
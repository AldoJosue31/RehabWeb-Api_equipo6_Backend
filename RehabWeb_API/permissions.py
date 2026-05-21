"""
Custom permissions for RehabWeb_API.

Define your custom permission classes here.
"""

from rest_framework import permissions
from RehabWeb_API.roles import get_request_role, user_has_role


class HasSelectedRole(permissions.BasePermission):
    message = 'El usuario no tiene permiso para usar el rol seleccionado.'

    def has_permission(self, request, view):
        selected_role = get_request_role(request)
        if not selected_role:
            return True

        return user_has_role(request.user, selected_role)

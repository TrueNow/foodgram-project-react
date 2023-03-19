from rest_framework import permissions


class UserPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action in ('me', 'set_password', 'subscriptions', 'subscribe'):
            return request.user.is_authenticated
        elif view.action in ('create',):
            return request.user.is_anonymous
        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_anonymous:
            return False

        if view.action in ('subscribe',):
            return obj != request.user
        return True

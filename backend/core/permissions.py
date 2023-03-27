from rest_framework import permissions

AllowAny = permissions.AllowAny
IsAuthenticated = permissions.IsAuthenticated


class IsOwnerOrAdminOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj):
        return bool(
            request.method in permissions.SAFE_METHODS
            or request.user.is_staff
            or request.user == obj.author
        )

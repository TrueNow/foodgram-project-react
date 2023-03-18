from rest_framework import permissions


AllowAny = permissions.AllowAny


class RecipePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action in (
                'create', 'update', 'partial_update', 'destroy',
                'favorite', 'shopping_cart', 'download_shopping_cart'
        ):
            return request.user.is_authenticated
        return request.user.is_anonymous

    def has_object_permission(self, request, view, obj):
        if request.user.is_anonymous:
            return False

        if view.action in ('update', 'partial_update', 'destroy'):
            return obj.author == request.user
        return False

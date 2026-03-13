from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Allow write access only to the object itself (for user profile)."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj == request.user

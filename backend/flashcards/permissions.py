from rest_framework.permissions import BasePermission


class IsCuratorOrAdmin(BasePermission):
    """
    Custom permission to only allow curators and admins to edit flashcards.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_curator() or request.user.is_admin())
        )


class IsAdminOnly(BasePermission):
    """
    Custom permission to only allow admins.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_admin()
        )

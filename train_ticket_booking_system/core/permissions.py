from rest_framework.permissions import BasePermission

class isAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 1

class isUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 0
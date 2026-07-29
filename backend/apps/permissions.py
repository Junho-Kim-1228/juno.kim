from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsVerifiedUserOrReadOnly(BasePermission):
    """Public reads are allowed; writes require a logged-in, verified email account."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.email_verified)


class IsOwnerOrStaffOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True

        owner = getattr(obj, "owner", None)
        author = getattr(obj, "author", None)
        return request.user in (owner, author)


class IsStaffOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_staff

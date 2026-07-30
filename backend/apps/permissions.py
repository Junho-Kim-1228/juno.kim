from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsActiveAuthenticated(BasePermission):
    """Authenticated requests from disabled accounts are rejected immediately."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active)


class IsVerifiedUserOrReadOnly(BasePermission):
    """Public reads are allowed; writes require a logged-in, verified email account."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.email_verified
        )


class IsVerifiedUserOrStaffOrReadOnly(BasePermission):
    """Public reads are allowed; writes require staff or a verified email account."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and (request.user.is_staff or request.user.email_verified)
        )


class IsOwnerOrStaffOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if not request.user.is_authenticated or not request.user.is_active:
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
        return request.user.is_authenticated and request.user.is_active and request.user.is_staff

class StaffContentAdminMixin:
    """Give active staff users full content-model permissions in Django Admin."""

    @staticmethod
    def _is_active_staff(request):
        return request.user.is_active and request.user.is_staff

    def has_module_permission(self, request):
        return self._is_active_staff(request)

    def has_view_permission(self, request, obj=None):
        return self._is_active_staff(request)

    def has_add_permission(self, request):
        return self._is_active_staff(request)

    def has_change_permission(self, request, obj=None):
        return self._is_active_staff(request)

    def has_delete_permission(self, request, obj=None):
        return self._is_active_staff(request)

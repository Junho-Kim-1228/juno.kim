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

    def save_model(self, request, obj, form, change):
        from apps.users.models import AuditLog, write_audit_log

        before_status = getattr(obj, "status", None)
        before_visibility = getattr(obj, "is_visible", getattr(obj, "is_active", None))
        super().save_model(request, obj, form, change)
        if change and ("status" in form.changed_data or "is_visible" in form.changed_data or "is_active" in form.changed_data):
            action = AuditLog.Action.CONTENT_STATUS_CHANGED
            if obj._meta.model_name == "comment":
                action = AuditLog.Action.COMMENT_MODERATED
            elif obj._meta.model_name == "guestbookentry":
                action = AuditLog.Action.GUESTBOOK_MODERATED
            write_audit_log(action=action, actor=request.user, request=request, obj=obj, details={"changed": [field for field in ("status", "is_visible", "is_active") if field in form.changed_data]})

    def delete_model(self, request, obj):
        from apps.users.models import AuditLog, write_audit_log

        action = AuditLog.Action.CONTENT_DELETED
        if obj._meta.model_name == "comment":
            action = AuditLog.Action.COMMENT_MODERATED
        elif obj._meta.model_name == "guestbookentry":
            action = AuditLog.Action.GUESTBOOK_MODERATED
        write_audit_log(action=action, actor=request.user, request=request, obj=obj, details={"operation": "delete"})
        super().delete_model(request, obj)

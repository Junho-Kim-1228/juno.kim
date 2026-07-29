from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone

from .models import AuditLog, ImpersonationReport, Profile, User, write_audit_log


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ("username", "email", "is_staff", "is_active")
    search_fields = ("username", "email")
    ordering = ("username",)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("연락처", {"fields": ("email",)}),
    )


    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change:
            changed = [field for field in ("is_active", "is_staff", "is_superuser", "groups", "user_permissions") if field in form.changed_data]
            if changed:
                write_audit_log(action=AuditLog.Action.USER_PERMISSION_CHANGED, actor=request.user, target_user=obj, request=request, details={"fields": changed})


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "updated_at")
    search_fields = ("user__username", "user__email", "display_name")

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "actor", "target_user", "object_type", "object_id", "ip_address")
    list_filter = ("action", "created_at")
    search_fields = ("actor__username", "target_user__username", "object_type", "object_id", "ip_address")
    readonly_fields = ("actor", "target_user", "action", "object_type", "object_id", "ip_address", "details", "created_at")

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ImpersonationReport)
class ImpersonationReportAdmin(admin.ModelAdmin):
    list_display = ("created_at", "reporter", "target", "status")
    list_filter = ("status", "created_at")
    search_fields = ("reporter__username", "comment__author__username", "guestbook_entry__author__username", "reason")
    readonly_fields = ("reporter", "comment", "guestbook_entry", "reason", "created_at", "reviewed_at")
    actions = ("hide_reported_content", "deactivate_reported_authors")

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_staff

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_add_permission(self, request):
        return False

    @admin.display(description="Reported item")
    def target(self, obj):
        return obj.comment or obj.guestbook_entry

    @admin.action(description="Hide reported content")
    def hide_reported_content(self, request, queryset):
        for report in queryset.select_related("comment", "guestbook_entry"):
            if report.comment:
                report.comment.is_active = False
                report.comment.save(update_fields=("is_active", "updated_at"))
            elif report.guestbook_entry:
                report.guestbook_entry.is_visible = False
                report.guestbook_entry.save(update_fields=("is_visible",))
            report.status = ImpersonationReport.Status.REVIEWED
            report.reviewed_at = timezone.now()
            report.save(update_fields=("status", "reviewed_at"))

    @admin.action(description="Deactivate reported authors (superuser only)")
    def deactivate_reported_authors(self, request, queryset):
        if not request.user.is_superuser:
            self.message_user(request, "Only superusers can deactivate accounts.", level="ERROR")
            return
        for report in queryset.select_related("comment__author", "guestbook_entry__author"):
            target = report.comment or report.guestbook_entry
            if target and target.author:
                target.author.is_active = False
                target.author.save(update_fields=("is_active",))
            report.status = ImpersonationReport.Status.REVIEWED
            report.reviewed_at = timezone.now()
            report.save(update_fields=("status", "reviewed_at"))

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            actions.pop("deactivate_reported_authors", None)
        return actions

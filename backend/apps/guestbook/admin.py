from django.contrib import admin
from django.utils import timezone

from apps.admin_mixins import StaffContentAdminMixin

from .models import GuestbookEntry, TodayStatus


@admin.register(GuestbookEntry)
class GuestbookEntryAdmin(StaffContentAdminMixin, admin.ModelAdmin):
    list_display = ("short_message", "name", "author", "has_reply", "is_visible", "created_at")
    list_filter = ("is_visible", "created_at")
    list_editable = ("is_visible",)
    search_fields = ("name", "message", "staff_reply", "author__username", "author__email")
    readonly_fields = ("author", "name", "message", "staff_replied_by", "staff_replied_at", "created_at")
    list_select_related = ("author", "staff_replied_by")

    @admin.display(description="메시지")
    def short_message(self, obj):
        return obj.message[:60]

    @admin.display(description="운영자 답장", boolean=True)
    def has_reply(self, obj):
        return bool(obj.staff_reply)

    def save_model(self, request, obj, form, change):
        if "staff_reply" in form.changed_data:
            obj.staff_reply = obj.staff_reply.strip()
            obj.staff_replied_by = request.user if obj.staff_reply else None
            obj.staff_replied_at = timezone.now() if obj.staff_reply else None
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return False


@admin.register(TodayStatus)
class TodayStatusAdmin(StaffContentAdminMixin, admin.ModelAdmin):
    list_display = ("doing", "mood", "listening", "updated_at")
    search_fields = ("doing", "mood", "listening")
    readonly_fields = ("updated_at",)

from django.contrib import admin

from apps.admin_mixins import StaffContentAdminMixin

from .models import GuestbookEntry


@admin.register(GuestbookEntry)
class GuestbookEntryAdmin(StaffContentAdminMixin, admin.ModelAdmin):
    list_display = ("short_message", "name", "author", "is_visible", "created_at")
    list_filter = ("is_visible", "created_at")
    list_editable = ("is_visible",)
    search_fields = ("name", "message", "author__username", "author__email")
    readonly_fields = ("author", "name", "message", "created_at")
    list_select_related = ("author",)

    @admin.display(description="메시지")
    def short_message(self, obj):
        return obj.message[:60]

    def has_add_permission(self, request):
        return False

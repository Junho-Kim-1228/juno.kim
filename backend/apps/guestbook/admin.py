from django.contrib import admin

from .models import GuestbookEntry


@admin.register(GuestbookEntry)
class GuestbookEntryAdmin(admin.ModelAdmin):
    list_display = ("short_message", "name", "is_visible", "created_at")
    list_filter = ("is_visible", "created_at")
    list_editable = ("is_visible",)
    search_fields = ("name", "message")
    readonly_fields = ("created_at",)

    @admin.display(description="메시지")
    def short_message(self, obj):
        return obj.message[:60]

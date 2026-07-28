from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "owner",
        "status",
        "is_featured",
        "published_at",
        "updated_at",
    )
    list_filter = ("status", "is_featured", "created_at", "updated_at")
    search_fields = ("title", "summary", "description", "owner__username", "owner__email")
    readonly_fields = ("slug", "published_at", "created_at", "updated_at")
    date_hierarchy = "created_at"
    list_select_related = ("owner",)

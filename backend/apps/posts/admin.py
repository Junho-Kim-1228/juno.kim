from django.contrib import admin

from apps.admin_mixins import StaffContentAdminMixin

from .models import Category, Post, Tag


@admin.register(Category)
class CategoryAdmin(StaffContentAdminMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "ordering")
    list_editable = ("ordering",)
    search_fields = ("name", "description")
    readonly_fields = ("slug",)


@admin.register(Tag)
class TagAdmin(StaffContentAdminMixin, admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    readonly_fields = ("slug",)


@admin.register(Post)
class PostAdmin(StaffContentAdminMixin, admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "category",
        "status",
        "is_featured",
        "published_at",
        "updated_at",
    )
    list_filter = ("status", "is_featured", "category", "tags", "created_at")
    search_fields = ("title", "excerpt", "content", "author__username", "author__email")
    readonly_fields = ("slug", "published_at", "created_at", "updated_at")
    filter_horizontal = ("tags",)
    date_hierarchy = "created_at"
    list_select_related = ("author", "category")

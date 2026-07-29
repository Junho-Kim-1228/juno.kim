from django.contrib import admin

from apps.admin_mixins import StaffContentAdminMixin

from .models import Category, ContentImage, Post, Tag


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


@admin.register(ContentImage)
class ContentImageAdmin(StaffContentAdminMixin, admin.ModelAdmin):
    list_display = ("id", "uploader", "created_at")
    search_fields = ("uploader__username", "uploader__email", "image")
    readonly_fields = ("created_at",)
    list_select_related = ("uploader",)


@admin.register(Post)
class PostAdmin(StaffContentAdminMixin, admin.ModelAdmin):
    list_display = (
        "title",
        "kind",
        "author",
        "category",
        "status",
        "is_featured",
        "published_at",
        "updated_at",
    )
    list_filter = ("kind", "status", "is_featured", "category", "tags", "created_at")
    search_fields = ("title", "excerpt", "content", "author__username", "author__email")
    readonly_fields = ("slug", "published_at", "created_at", "updated_at")
    filter_horizontal = ("tags",)
    date_hierarchy = "created_at"
    list_select_related = ("author", "category")

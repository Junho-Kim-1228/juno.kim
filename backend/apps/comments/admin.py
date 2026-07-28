from django.contrib import admin

from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("short_content", "post", "author", "parent", "is_active", "created_at")
    list_filter = ("is_active", "created_at", "updated_at")
    search_fields = ("content", "post__title", "author__username", "author__email")
    list_editable = ("is_active",)
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("post", "author", "parent")

    @admin.display(description="내용")
    def short_content(self, obj):
        return obj.content[:60]

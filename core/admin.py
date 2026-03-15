from django.contrib import admin

from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("nickname", "created_at", "short_message")
    search_fields = ("nickname", "message")
    ordering = ("-created_at",)

    @staticmethod
    def short_message(obj: Comment) -> str:
        return obj.message[:60]


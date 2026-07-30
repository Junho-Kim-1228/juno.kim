from django.contrib import admin

from .models import ReactionBestScore, ReactionChallenge


@admin.register(ReactionBestScore)
class ReactionBestScoreAdmin(admin.ModelAdmin):
    list_display = ("user", "reaction_ms", "achieved_at")
    search_fields = ("user__username", "user__email")
    ordering = ("reaction_ms", "achieved_at")


@admin.register(ReactionChallenge)
class ReactionChallengeAdmin(admin.ModelAdmin):
    list_display = ("user", "ready_at", "expires_at", "used_at", "created_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("id", "user", "ready_at", "expires_at", "used_at", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

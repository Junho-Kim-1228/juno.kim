import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class ReactionChallenge(models.Model):
    """A short-lived, single-use server-timed reaction-game attempt."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reaction_challenges")
    ready_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=("user", "expires_at"))]


class ReactionBestScore(models.Model):
    """Each account owns exactly one best reaction time on the public leaderboard."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reaction_best_score")
    reaction_ms = models.PositiveIntegerField(validators=[MinValueValidator(100)])
    achieved_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("reaction_ms", "achieved_at", "pk")


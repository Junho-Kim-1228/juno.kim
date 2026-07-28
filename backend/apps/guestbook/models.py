from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models


class GuestbookEntry(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="guestbook_entries",
        verbose_name="작성자",
    )
    name = models.CharField("이름", max_length=40)
    message = models.TextField(
        "메시지",
        max_length=500,
        validators=[MinLengthValidator(1)],
    )
    is_visible = models.BooleanField("공개", default=True)
    created_at = models.DateTimeField("작성일", auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "방문록 글"
        verbose_name_plural = "방문록 글"

    def __str__(self):
        return f"{self.name}: {self.message[:30]}"

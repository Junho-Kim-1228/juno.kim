from django.conf import settings
from django.core.exceptions import ValidationError
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
    staff_reply = models.TextField("운영자 답장", max_length=500, blank=True)
    staff_replied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="guestbook_staff_replies",
        verbose_name="답장 작성자",
    )
    staff_replied_at = models.DateTimeField("답장 작성일", null=True, blank=True)
    is_visible = models.BooleanField("공개", default=True)
    created_at = models.DateTimeField("작성일", auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "방문록 글"
        verbose_name_plural = "방문록 글"

    def __str__(self):
        return f"{self.name}: {self.message[:30]}"


class TodayStatus(models.Model):
    mood = models.CharField("오늘 기분", max_length=40, blank=True)
    doing = models.CharField("하는 중", max_length=120, blank=True)
    listening = models.CharField("듣는 중", max_length=120, blank=True)
    updated_at = models.DateTimeField("수정일", auto_now=True)

    class Meta:
        ordering = ("-updated_at", "-id")
        verbose_name = "오늘의 김준호"
        verbose_name_plural = "오늘의 김준호"

    def clean(self):
        if not any(value.strip() for value in (self.mood, self.doing, self.listening)):
            raise ValidationError("기분, 하는 중, 듣는 중 가운데 하나는 입력해 주세요.")

    def __str__(self):
        return self.doing or self.mood or self.listening

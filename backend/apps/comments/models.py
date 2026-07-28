from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models


class Comment(models.Model):
    post = models.ForeignKey(
        "posts.Post",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
    )
    content = models.TextField(
        "내용",
        max_length=3000,
        validators=[MinLengthValidator(1)],
    )
    is_active = models.BooleanField("공개", default=True)
    created_at = models.DateTimeField("생성일", auto_now_add=True)
    updated_at = models.DateTimeField("수정일", auto_now=True)

    class Meta:
        ordering = ("created_at",)

    def clean(self):
        if self.parent_id and self.parent.post_id != self.post_id:
            raise ValidationError({"parent": "부모 댓글은 같은 게시글에 있어야 합니다."})
        if self.parent_id and self.parent.parent_id:
            raise ValidationError({"parent": "대댓글에는 다시 답글을 달 수 없습니다."})

    def __str__(self):
        return f"{self.author} - {self.post}"

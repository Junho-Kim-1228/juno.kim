from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone

from apps.model_utils import build_unique_slug, validate_image_size


def validate_technologies(value):
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ValidationError("기술 스택은 비어 있지 않은 문자열 목록이어야 합니다.")


class Project(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "초안"
        PUBLISHED = "published", "공개"
        ARCHIVED = "archived", "보관"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    title = models.CharField("제목", max_length=200)
    slug = models.SlugField("슬러그", max_length=220, unique=True, allow_unicode=True)
    summary = models.CharField("요약", max_length=300)
    description = models.TextField("설명")
    technologies = models.JSONField(
        "기술 스택",
        default=list,
        blank=True,
        validators=[validate_technologies],
    )
    repository_url = models.URLField("저장소 URL", blank=True)
    live_url = models.URLField("서비스 URL", blank=True)
    thumbnail = models.ImageField(
        "대표 이미지",
        upload_to="projects/%Y/%m/",
        blank=True,
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
            validate_image_size,
        ],
    )
    status = models.CharField(
        "상태",
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    is_featured = models.BooleanField("대표 프로젝트", default=False)
    started_on = models.DateField("시작일", null=True, blank=True)
    ended_on = models.DateField("종료일", null=True, blank=True)
    published_at = models.DateTimeField("공개일", null=True, blank=True)
    created_at = models.DateTimeField("생성일", auto_now_add=True)
    updated_at = models.DateTimeField("수정일", auto_now=True)

    class Meta:
        ordering = ("-is_featured", "-published_at", "-created_at")

    def clean(self):
        if self.started_on and self.ended_on and self.ended_on < self.started_on:
            raise ValidationError({"ended_on": "종료일은 시작일보다 빠를 수 없습니다."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(self, self.title)
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

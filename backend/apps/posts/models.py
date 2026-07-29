from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone

from apps.model_utils import build_unique_slug, validate_image_size


class Category(models.Model):
    name = models.CharField("이름", max_length=80, unique=True)
    slug = models.SlugField("슬러그", max_length=100, unique=True, allow_unicode=True)
    description = models.CharField("설명", max_length=250, blank=True)
    ordering = models.PositiveSmallIntegerField("정렬 순서", default=0)

    class Meta:
        ordering = ("ordering", "name")
        verbose_name_plural = "categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(self, self.name, max_length=100)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField("이름", max_length=50, unique=True)
    slug = models.SlugField("슬러그", max_length=70, unique=True, allow_unicode=True)

    class Meta:
        ordering = ("name",)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(self, self.name, max_length=70)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Post(models.Model):
    class Kind(models.TextChoices):
        BOARD = "board", "게시판 글"
        TECHNICAL = "technical", "기술 기록"

    class Status(models.TextChoices):
        DRAFT = "draft", "임시저장"
        PUBLISHED = "published", "공개"
        PRIVATE = "private", "비공개"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    kind = models.CharField(
        "게시 위치",
        max_length=16,
        choices=Kind.choices,
        default=Kind.BOARD,
    )
    title = models.CharField("제목", max_length=220)
    slug = models.SlugField("슬러그", max_length=240, unique=True, allow_unicode=True)
    excerpt = models.CharField("요약", max_length=320)
    content = models.TextField("본문")
    cover_image = models.ImageField(
        "대표 이미지",
        upload_to="posts/%Y/%m/",
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
    is_featured = models.BooleanField("공지 게시글", default=False)
    published_at = models.DateTimeField("공개일", null=True, blank=True)
    created_at = models.DateTimeField("생성일", auto_now_add=True)
    updated_at = models.DateTimeField("수정일", auto_now=True)

    class Meta:
        ordering = ("-is_featured", "-published_at", "-created_at")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(self, self.title, max_length=240)
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

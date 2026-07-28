from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models


def validate_avatar_size(file):
    max_size = 5 * 1024 * 1024
    if file.size > max_size:
        raise ValidationError("프로필 이미지는 5MB 이하여야 합니다.")


class User(AbstractUser):
    """로그인, 권한, 계정 식별 정보를 관리합니다."""

    email = models.EmailField("이메일", unique=True)

    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username


class Profile(models.Model):
    """사용자에게 공개되는 선택적 프로필 정보를 관리합니다."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField("표시 이름", max_length=50, blank=True)
    bio = models.TextField("소개", blank=True)
    avatar = models.ImageField(
        "프로필 이미지",
        upload_to="profiles/%Y/%m/",
        blank=True,
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
            validate_avatar_size,
        ],
    )
    website_url = models.URLField("웹사이트", blank=True)
    github_url = models.URLField("GitHub", blank=True)
    created_at = models.DateTimeField("생성일", auto_now_add=True)
    updated_at = models.DateTimeField("수정일", auto_now=True)

    def __str__(self):
        return f"{self.user.username} profile"

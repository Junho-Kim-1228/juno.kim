from django.core.exceptions import ValidationError
from django.utils.text import slugify


def validate_image_size(file):
    max_size = 10 * 1024 * 1024
    if file.size > max_size:
        raise ValidationError("이미지는 10MB 이하여야 합니다.")


def validate_content_image_size(file):
    max_size = 5 * 1024 * 1024
    if file.size > max_size:
        raise ValidationError("본문 이미지는 5MB 이하여야 합니다.")


def build_unique_slug(instance, value, *, max_length=220):
    base = slugify(value, allow_unicode=True) or "item"
    base = base[:max_length].strip("-") or "item"
    slug = base
    queryset = instance.__class__.objects.exclude(pk=instance.pk)
    sequence = 2

    while queryset.filter(slug=slug).exists():
        suffix = f"-{sequence}"
        slug = f"{base[: max_length - len(suffix)].rstrip('-')}{suffix}"
        sequence += 1

    return slug

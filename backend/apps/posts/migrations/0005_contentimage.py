import apps.model_utils
import apps.posts.models
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("posts", "0004_post_visibility_statuses"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ContentImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "image",
                    models.ImageField(
                        upload_to=apps.posts.models.content_image_upload_to,
                        validators=[
                            django.core.validators.FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
                            apps.model_utils.validate_content_image_size,
                        ],
                        verbose_name="이미지",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="생성일")),
                (
                    "uploader",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="content_images",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]

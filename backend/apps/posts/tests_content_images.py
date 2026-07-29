from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User

from .models import ContentImage


def make_image_file(name="body.png", *, extra_bytes=0):
    buffer = BytesIO()
    Image.new("RGB", (24, 24), "#247565").save(buffer, format="PNG")
    payload = buffer.getvalue() + (b"0" * extra_bytes)
    return SimpleUploadedFile(name, payload, content_type="image/png")


@override_settings(
    FILE_UPLOAD_MAX_MEMORY_SIZE=6 * 1024 * 1024,
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.memory.InMemoryStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class ContentImageUploadTests(APITestCase):
    def setUp(self):
        self.verified_user = User.objects.create_user(
            username="image_writer",
            email="image-writer@example.com",
            password="StrongTemporary!2026",
            email_verified=True,
        )
        self.unverified_user = User.objects.create_user(
            username="unverified_image_writer",
            email="unverified-image@example.com",
            password="StrongTemporary!2026",
        )
        self.staff = User.objects.create_user(
            username="image_editor",
            email="image-editor@example.com",
            password="StrongTemporary!2026",
            is_staff=True,
        )

    def test_verified_user_can_upload_a_valid_content_image(self):
        self.client.force_authenticate(self.verified_user)

        response = self.client.post(
            "/api/v1/content-images/",
            {"image": make_image_file()},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content_image = ContentImage.objects.get()
        self.assertEqual(content_image.uploader, self.verified_user)
        self.assertTrue(content_image.image.name.startswith("content/"))
        self.assertNotIn("body.png", content_image.image.name)
        self.assertEqual(response.data["url"], content_image.image.url)

    def test_staff_can_upload_without_email_verification(self):
        self.client.force_authenticate(self.staff)

        response = self.client.post(
            "/api/v1/content-images/",
            {"image": make_image_file("staff.png")},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_anonymous_and_unverified_users_cannot_upload(self):
        anonymous = self.client.post(
            "/api/v1/content-images/",
            {"image": make_image_file()},
            format="multipart",
        )
        self.client.force_authenticate(self.unverified_user)
        unverified = self.client.post(
            "/api/v1/content-images/",
            {"image": make_image_file()},
            format="multipart",
        )

        self.assertEqual(anonymous.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(unverified.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(ContentImage.objects.exists())

    def test_invalid_and_oversized_files_are_rejected(self):
        self.client.force_authenticate(self.verified_user)

        invalid = self.client.post(
            "/api/v1/content-images/",
            {"image": SimpleUploadedFile("fake.png", b"not-an-image", content_type="image/png")},
            format="multipart",
        )
        oversized = self.client.post(
            "/api/v1/content-images/",
            {"image": make_image_file(extra_bytes=5 * 1024 * 1024)},
            format="multipart",
        )

        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(oversized.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(ContentImage.objects.exists())

from django.test import TestCase
from django.urls import reverse

from .models import Comment


class HomeViewTests(TestCase):
    def test_home_page_renders(self) -> None:
        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "김준호")

    def test_valid_comment_creates_row(self) -> None:
        response = self.client.post(
            reverse("core:home"),
            {
                "nickname": "테스터",
                "message": "이제 진짜 Django 사이트다.",
            },
        )

        self.assertRedirects(response, reverse("core:home"))
        self.assertTrue(
            Comment.objects.filter(
                nickname="테스터",
                message="이제 진짜 Django 사이트다.",
            ).exists()
        )


from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.users.models import User

from .models import GuestbookEntry


class GuestbookAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)
        response = self.client.get("/api/v1/auth/csrf/")
        self.csrf_headers = {"HTTP_X_CSRFTOKEN": response.data["csrfToken"]}
        self.user = User.objects.create_user(
            username="guestbook-writer",
            email="guestbook@example.com",
            password="StrongTemporary!2026",
        )
        self.user.profile.display_name = "로그인 사용자"
        self.user.profile.save(update_fields=("display_name", "updated_at"))

    def test_public_list_excludes_hidden_entries(self):
        GuestbookEntry.objects.create(name="보이는 사람", message="안녕하세요")
        GuestbookEntry.objects.create(name="숨긴 사람", message="숨김", is_visible=False)

        response = self.client.get("/api/v1/guestbook/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "보이는 사람")

    def test_authenticated_user_can_write_with_profile_name(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            "/api/v1/guestbook/",
            {"name": "다른 이름", "message": " 반갑습니다. "},
            format="json",
            **self.csrf_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        entry = GuestbookEntry.objects.get()
        self.assertEqual(entry.name, "로그인 사용자")
        self.assertEqual(entry.message, "반갑습니다.")

    def test_anonymous_visitor_cannot_write(self):
        response = self.client.post(
            "/api/v1/guestbook/",
            {"message": "로그인하지 않은 글"},
            format="json",
            **self.csrf_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(GuestbookEntry.objects.exists())

    def test_write_requires_csrf_token(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_authenticate(self.user)
        response = client.post(
            "/api/v1/guestbook/",
            {"message": "토큰 없음"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

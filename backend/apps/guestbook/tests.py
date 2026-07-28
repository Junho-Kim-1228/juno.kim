from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import GuestbookEntry


class GuestbookAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)
        response = self.client.get("/api/v1/auth/csrf/")
        self.csrf_headers = {"HTTP_X_CSRFTOKEN": response.data["csrfToken"]}

    def test_public_list_excludes_hidden_entries(self):
        GuestbookEntry.objects.create(name="보이는 사람", message="안녕하세요")
        GuestbookEntry.objects.create(name="숨긴 사람", message="숨김", is_visible=False)

        response = self.client.get("/api/v1/guestbook/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "보이는 사람")

    def test_anonymous_visitor_can_write_with_csrf_token(self):
        response = self.client.post(
            "/api/v1/guestbook/",
            {"name": " 방문자 ", "message": " 반갑습니다. "},
            format="json",
            **self.csrf_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        entry = GuestbookEntry.objects.get()
        self.assertEqual(entry.name, "방문자")
        self.assertEqual(entry.message, "반갑습니다.")

    def test_write_requires_csrf_token(self):
        response = APIClient(enforce_csrf_checks=True).post(
            "/api/v1/guestbook/",
            {"name": "방문자", "message": "토큰 없음"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

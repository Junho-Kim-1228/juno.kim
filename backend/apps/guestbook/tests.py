from django.contrib.admin.sites import AdminSite
from django.core.cache import cache
from django.test import RequestFactory, TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.users.models import User

from .admin import GuestbookEntryAdmin
from .models import GuestbookEntry


class GuestbookAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient(enforce_csrf_checks=True)
        response = self.client.get("/api/v1/auth/csrf/")
        self.csrf_headers = {"HTTP_X_CSRFTOKEN": response.data["csrfToken"]}
        self.user = User.objects.create_user(
            username="guestbook_writer",
            email="guestbook@example.com",
            password="StrongTemporary!2026",
        )
        self.user.email_verified = True
        self.user.save(update_fields=("email_verified",))
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
        self.assertEqual(entry.author, self.user)
        self.assertEqual(entry.name, "로그인 사용자")
        self.assertEqual(entry.message, "반갑습니다.")

    def test_legacy_entry_without_author_remains_readable(self):
        entry = GuestbookEntry.objects.create(name="기존 방문자", message="기존 메시지")

        response = self.client.get("/api/v1/guestbook/")

        self.assertIsNone(entry.author)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["name"], "기존 방문자")

    def test_blank_or_overlong_message_is_rejected(self):
        self.client.force_authenticate(self.user)

        blank = self.client.post(
            "/api/v1/guestbook/",
            {"message": "   "},
            format="json",
            **self.csrf_headers,
        )
        overlong = self.client.post(
            "/api/v1/guestbook/",
            {"message": "x" * 501},
            format="json",
            **self.csrf_headers,
        )

        self.assertEqual(blank.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(overlong.status_code, status.HTTP_400_BAD_REQUEST)

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


class GuestbookAdminPermissionTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.model_admin = GuestbookEntryAdmin(GuestbookEntry, AdminSite())
        self.member = User.objects.create_user(
            username="guestbook_member",
            email="guestbook-member@example.com",
            password="StrongTemporary!2026",
        )
        self.staff = User.objects.create_user(
            username="guestbook_editor",
            email="guestbook-staff@example.com",
            password="StrongTemporary!2026",
            is_staff=True,
        )

    def request_for(self, user):
        request = self.factory.get("/admin/guestbook/guestbookentry/")
        request.user = user
        return request

    def test_active_staff_can_manage_but_not_create_guestbook_entries(self):
        request = self.request_for(self.staff)

        self.assertTrue(self.model_admin.has_module_permission(request))
        self.assertTrue(self.model_admin.has_view_permission(request))
        self.assertTrue(self.model_admin.has_change_permission(request))
        self.assertTrue(self.model_admin.has_delete_permission(request))
        self.assertFalse(self.model_admin.has_add_permission(request))

    def test_member_has_no_guestbook_admin_permissions(self):
        request = self.request_for(self.member)

        self.assertFalse(self.model_admin.has_module_permission(request))
        self.assertFalse(self.model_admin.has_view_permission(request))
        self.assertFalse(self.model_admin.has_change_permission(request))
        self.assertFalse(self.model_admin.has_delete_permission(request))

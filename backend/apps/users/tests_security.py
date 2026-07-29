from django.contrib import admin
from django.core.cache import cache
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.guestbook.models import GuestbookEntry
from apps.posts.models import Post

from .models import EmailVerificationToken, User


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class EmailVerificationAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient(enforce_csrf_checks=True)
        self.csrf = self.client.get("/api/v1/auth/csrf/").data["csrfToken"]
        self.headers = {"HTTP_X_CSRFTOKEN": self.csrf}

    def test_registration_normalizes_email_and_one_time_token_verifies_user(self):
        response = self.client.post("/api/v1/auth/register/", {"username": "verify-user", "email": "Verify@Example.COM", "password": "StrongTemporary!2026"}, format="json", **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="verify-user")
        self.assertEqual(user.email, "verify@example.com")
        self.assertFalse(user.email_verified)
        self.assertEqual(len(mail.outbox), 1)

        raw_token, _ = EmailVerificationToken.issue_for(user)
        verified = self.client.post("/api/v1/auth/verify-email/", {"token": raw_token}, format="json", **self.headers)
        reused = self.client.post("/api/v1/auth/verify-email/", {"token": raw_token}, format="json", **self.headers)
        user.refresh_from_db()
        self.assertEqual(verified.status_code, status.HTTP_200_OK)
        self.assertEqual(reused.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(user.email_verified)

    def test_unverified_user_cannot_write_comment_or_guestbook(self):
        author = User.objects.create_user(username="post-author", email="post-author@example.com", password="StrongTemporary!2026")
        author.email_verified = True
        author.save(update_fields=("email_verified",))
        post = Post.objects.create(author=author, title="Published", excerpt="excerpt", content="content", status=Post.Status.PUBLISHED)
        member = User.objects.create_user(username="unverified", email="unverified@example.com", password="StrongTemporary!2026")
        self.client.force_authenticate(member)
        comment = self.client.post("/api/v1/comments/", {"post_slug": post.slug, "content": "blocked"}, format="json")
        guestbook = self.client.post("/api/v1/guestbook/", {"message": "blocked"}, format="json", **self.headers)
        self.assertEqual(comment.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(guestbook.status_code, status.HTTP_403_FORBIDDEN)

    def test_guestbook_account_rate_limit_returns_429(self):
        member = User.objects.create_user(username="rate-user", email="rate@example.com", password="StrongTemporary!2026")
        member.email_verified = True
        member.save(update_fields=("email_verified",))
        self.client.force_authenticate(member)
        responses = [self.client.post("/api/v1/guestbook/", {"message": f"entry {index}"}, format="json", **self.headers) for index in range(4)]
        self.assertEqual([response.status_code for response in responses[:3]], [status.HTTP_201_CREATED] * 3)
        self.assertEqual(responses[3].status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_guestbook_ip_rate_limit_is_independent_from_account_limit(self):
        first = User.objects.create_user(username="ip-first", email="ip-first@example.com", password="StrongTemporary!2026")
        second = User.objects.create_user(username="ip-second", email="ip-second@example.com", password="StrongTemporary!2026")
        for user in (first, second):
            user.email_verified = True
            user.save(update_fields=("email_verified",))
        responses = []
        for user in (first, second):
            self.client.force_authenticate(user)
            responses.extend(self.client.post("/api/v1/guestbook/", {"message": f"{user.username}-{index}"}, format="json", **self.headers) for index in range(3))
        self.assertEqual([response.status_code for response in responses[:5]], [status.HTTP_201_CREATED] * 5)
        self.assertEqual(responses[5].status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class SecurityAdminAndTokenTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(username="root-user", email="root@example.com", password="StrongTemporary!2026")
        self.staff = User.objects.create_user(username="content-staff", email="staff@example.com", password="StrongTemporary!2026", is_staff=True)
        self.member = User.objects.create_user(username="member", email="member@example.com", password="StrongTemporary!2026")

    def test_content_staff_cannot_access_user_management_but_superuser_can(self):
        request = type("Request", (), {"user": self.staff})()
        super_request = type("Request", (), {"user": self.superuser})()
        user_admin = admin.site._registry[User]
        self.assertFalse(user_admin.has_module_permission(request))
        self.assertFalse(user_admin.has_change_permission(request, self.member))
        self.assertTrue(user_admin.has_module_permission(super_request))
        self.assertTrue(user_admin.has_change_permission(super_request, self.member))

    def test_sensitive_account_change_blacklists_outstanding_refresh_tokens(self):
        refresh = RefreshToken.for_user(self.member)
        outstanding = OutstandingToken.objects.get(jti=refresh["jti"])
        self.member.is_staff = True
        self.member.save(update_fields=("is_staff",))
        self.assertTrue(BlacklistedToken.objects.filter(token=outstanding).exists())

    def test_unverified_staff_is_sent_to_mfa_enrollment_before_admin(self):
        client = self.client
        client.force_login(self.staff)
        response = client.get("/admin/", follow=False)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("/admin/mfa/setup/", response["Location"])
        enrollment = client.get(response["Location"])
        self.assertEqual(enrollment.status_code, status.HTTP_200_OK)
        self.assertContains(enrollment, "Manual key")

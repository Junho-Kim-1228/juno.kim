from django.contrib import admin
from django.core.cache import cache
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.guestbook.models import GuestbookEntry
from apps.posts.models import Post

from .models import EmailVerificationToken, ImpersonationReport, User


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class EmailVerificationAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient(enforce_csrf_checks=True)
        self.csrf = self.client.get("/api/v1/auth/csrf/").data["csrfToken"]
        self.headers = {"HTTP_X_CSRFTOKEN": self.csrf}

    def test_registration_normalizes_email_and_one_time_token_verifies_user(self):
        response = self.client.post("/api/v1/auth/register/", {"username": "verify_user", "email": "Verify@Example.COM", "password": "StrongTemporary!2026"}, format="json", **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="verify_user")
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
        author = User.objects.create_user(username="post_author", email="post-author@example.com", password="StrongTemporary!2026")
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
        member = User.objects.create_user(username="rate_user", email="rate@example.com", password="StrongTemporary!2026")
        member.email_verified = True
        member.save(update_fields=("email_verified",))
        self.client.force_authenticate(member)
        responses = [self.client.post("/api/v1/guestbook/", {"message": f"entry {index}"}, format="json", **self.headers) for index in range(4)]
        self.assertEqual([response.status_code for response in responses[:3]], [status.HTTP_201_CREATED] * 3)
        self.assertEqual(responses[3].status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_reserved_and_confusable_username_or_display_name_is_rejected(self):
        for username in ("juno", "Juno", "ｊｕｎｏ", "juno_kim", "admin", "official", "juno_kim_official"):
            response = self.client.post("/api/v1/auth/register/", {"username": username, "email": f"{username.encode('unicode_escape').decode()}@example.com", "password": "StrongTemporary!2026"}, format="json", **self.headers)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        member = User.objects.create_user(username="normal_user", email="normal@example.com", password="StrongTemporary!2026")
        self.client.force_authenticate(member)
        for display_name in ("김준호", "Juno Kim", "Ｊｕｎｏ", "관리자", "Admin", "Official", "Juno Kim Official"):
            response = self.client.patch("/api/v1/auth/profile/", {"display_name": display_name}, format="json", **self.headers)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_manager_rejects_reserved_username(self):
        with self.assertRaises(ValidationError):
            User.objects.create_user(username="administrator", email="administrator@example.com", password="StrongTemporary!2026")
        safe_user = User.objects.create_user(username="stafford", email="stafford@example.com", password="StrongTemporary!2026")
        self.assertEqual(safe_user.username, "stafford")

    def test_verified_user_can_report_impersonation_and_report_is_admin_registered(self):
        author = User.objects.create_user(username="reported_user", email="reported@example.com", password="StrongTemporary!2026")
        author.email_verified = True
        author.save(update_fields=("email_verified",))
        post = Post.objects.create(author=author, title="Published", excerpt="excerpt", content="content", status=Post.Status.PUBLISHED)
        comment = post.comments.create(author=author, content="comment")
        guestbook_entry = GuestbookEntry.objects.create(author=author, name="reported_user", message="guestbook")
        reporter = User.objects.create_user(username="reporter_user", email="reporter@example.com", password="StrongTemporary!2026")
        reporter.email_verified = True
        reporter.save(update_fields=("email_verified",))
        self.client.force_authenticate(reporter)
        response = self.client.post("/api/v1/reports/impersonation/", {"target_type": "comment", "target_id": comment.id, "reason": "looks misleading"}, format="json", **self.headers)
        guestbook_response = self.client.post("/api/v1/reports/impersonation/", {"target_type": "guestbook", "target_id": guestbook_entry.id, "reason": "looks misleading"}, format="json", **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(guestbook_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ImpersonationReport.objects.filter(comment=comment, reporter=reporter).exists())
        self.assertTrue(ImpersonationReport.objects.filter(guestbook_entry=guestbook_entry, reporter=reporter).exists())
        self.assertIn(ImpersonationReport, admin.site._registry)

        duplicate = self.client.post("/api/v1/reports/impersonation/", {"target_type": "comment", "target_id": comment.id, "reason": "duplicate"}, format="json", **self.headers)
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ImpersonationReport.objects.filter(comment=comment, reporter=reporter).count(), 1)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ImpersonationReport.objects.create(reporter=reporter, comment=comment, reason="race")

    def test_reports_hide_non_public_content_and_require_a_reason(self):
        author = User.objects.create_user(username="hidden_author", email="hidden-author@example.com", password="StrongTemporary!2026")
        reporter = User.objects.create_user(username="hidden_reporter", email="hidden-reporter@example.com", password="StrongTemporary!2026")
        for user in (author, reporter):
            user.email_verified = True
            user.save(update_fields=("email_verified",))
        published = Post.objects.create(author=author, title="Published", excerpt="excerpt", content="content", status=Post.Status.PUBLISHED)
        draft = Post.objects.create(author=author, title="Draft", excerpt="excerpt", content="content")
        hidden_comment = published.comments.create(author=author, content="hidden", is_active=False)
        draft_comment = draft.comments.create(author=author, content="draft")
        hidden_entry = GuestbookEntry.objects.create(author=author, name="hidden_author", message="hidden", is_visible=False)
        self.client.force_authenticate(reporter)

        for target_type, target_id in (("comment", hidden_comment.id), ("comment", draft_comment.id), ("guestbook", hidden_entry.id)):
            response = self.client.post("/api/v1/reports/impersonation/", {"target_type": target_type, "target_id": target_id, "reason": "hidden"}, format="json", **self.headers)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        empty_reason = self.client.post("/api/v1/reports/impersonation/", {"target_type": "comment", "target_id": hidden_comment.id, "reason": "   "}, format="json", **self.headers)
        self.assertEqual(empty_reason.status_code, status.HTTP_400_BAD_REQUEST)

    def test_report_account_rate_limit_returns_429(self):
        author = User.objects.create_user(username="report_rate_author", email="report-rate-author@example.com", password="StrongTemporary!2026")
        reporter = User.objects.create_user(username="report_rate_user", email="report-rate-user@example.com", password="StrongTemporary!2026")
        for user in (author, reporter):
            user.email_verified = True
            user.save(update_fields=("email_verified",))
        post = Post.objects.create(author=author, title="Published", excerpt="excerpt", content="content", status=Post.Status.PUBLISHED)
        comments = [post.comments.create(author=author, content=f"comment {index}") for index in range(11)]
        self.client.force_authenticate(reporter)
        responses = [
            self.client.post("/api/v1/reports/impersonation/", {"target_type": "comment", "target_id": comment.id, "reason": "report"}, format="json", **self.headers)
            for comment in comments
        ]
        self.assertEqual([response.status_code for response in responses[:10]], [status.HTTP_201_CREATED] * 10)
        self.assertEqual(responses[10].status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_identity_conflict_command_is_read_only(self):
        legacy = User(username="legacy-admin", email="legacy-admin@example.com", password="not-used")
        User.objects.bulk_create([legacy])
        output = []

        class Capture:
            def write(self, message, ending="\n"):
                output.append(message)

            def flush(self):
                return None

        call_command("check_identity_conflicts", stdout=Capture())
        legacy.refresh_from_db()
        self.assertEqual(legacy.username, "legacy-admin")
        self.assertTrue(any("legacy-admin" in message for message in output))

    def test_guestbook_ip_rate_limit_is_independent_from_account_limit(self):
        first = User.objects.create_user(username="ip_first", email="ip-first@example.com", password="StrongTemporary!2026")
        second = User.objects.create_user(username="ip_second", email="ip-second@example.com", password="StrongTemporary!2026")
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
        self.superuser = User.objects.create_superuser(username="root_user", email="root@example.com", password="StrongTemporary!2026")
        self.staff = User.objects.create_user(username="content_editor", email="staff@example.com", password="StrongTemporary!2026", is_staff=True)
        self.member = User.objects.create_user(username="member", email="member@example.com", password="StrongTemporary!2026")

    def test_content_staff_cannot_access_user_management_but_superuser_can(self):
        request = type("Request", (), {"user": self.staff})()
        super_request = type("Request", (), {"user": self.superuser})()
        user_admin = admin.site._registry[User]
        self.assertFalse(user_admin.has_module_permission(request))
        self.assertFalse(user_admin.has_change_permission(request, self.member))
        self.assertTrue(user_admin.has_module_permission(super_request))
        self.assertTrue(user_admin.has_change_permission(super_request, self.member))

    def test_operator_badge_flag_is_only_true_for_staff(self):
        from .serializers import UserSummarySerializer

        self.assertFalse(UserSummarySerializer(self.member).data["is_staff"])
        self.assertTrue(UserSummarySerializer(self.staff).data["is_staff"])

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
        self.assertContains(enrollment, "관리자 MFA QR 코드")
        self.assertContains(enrollment, "QR 코드를 스캔할 수 없나요?")
        self.assertContains(enrollment, "새 QR 코드 만들기")

        second_view = client.get(response["Location"])
        self.assertNotContains(second_view, "수동 키는 이 화면에서 한 번만 표시됩니다")

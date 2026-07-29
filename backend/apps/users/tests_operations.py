from unittest.mock import patch

from django.contrib import admin
from django.core import mail
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.plugins.otp_totp.models import TOTPDevice

from .email import send_verification_email
from .models import AuditLog, OperationalEvent, User


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class OperationalEventTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="reader_one",
            email="reader-one@example.com",
            password="StrongTemporary!2026",
            is_staff=True,
        )
        self.member = User.objects.create_user(
            username="reader_two",
            email="reader-two@example.com",
            password="StrongTemporary!2026",
        )

    def test_successful_verification_email_creates_redacted_event(self):
        send_verification_email(self.member)

        event = AuditLog.objects.get(action=AuditLog.Action.VERIFICATION_EMAIL_SENT)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(event.target_user, self.member)
        self.assertEqual(event.details, {"result": "sent"})
        self.assertNotIn(self.member.email, str(event.details))

    @patch("apps.users.email.send_mail", side_effect=RuntimeError("provider response contains user@example.com"))
    def test_failed_verification_email_records_only_exception_type(self, _send_mail):
        with self.assertRaises(RuntimeError):
            send_verification_email(self.member)

        event = AuditLog.objects.get(action=AuditLog.Action.VERIFICATION_EMAIL_FAILED)
        self.assertEqual(
            event.details,
            {"result": "failed", "error_type": "RuntimeError"},
        )
        self.assertNotIn("user@example.com", str(event.details))

    def test_staff_admin_is_read_only_and_excludes_security_audit_rows(self):
        operation = AuditLog.objects.create(
            action=AuditLog.Action.VERIFICATION_EMAIL_FAILED,
            target_user=self.member,
            details={
                "result": "failed",
                "error_type": "TimeoutError",
                "ip_address": "203.0.113.1",
            },
        )
        AuditLog.objects.create(
            action=AuditLog.Action.USER_PERMISSION_CHANGED,
            target_user=self.member,
            details={"fields": ["is_staff"]},
        )

        request = RequestFactory().get("/admin/users/operationalevent/")
        request.user = self.staff
        model_admin = admin.site._registry[OperationalEvent]

        self.assertTrue(model_admin.has_module_permission(request))
        self.assertTrue(model_admin.has_view_permission(request))
        self.assertIsNone(model_admin.date_hierarchy)
        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_change_permission(request, operation))
        self.assertFalse(model_admin.has_delete_permission(request, operation))
        self.assertEqual(list(model_admin.get_queryset(request)), [operation])
        self.assertNotIn("203.0.113.1", model_admin.safe_details(operation))

    def test_regular_member_cannot_view_operational_events(self):
        request = RequestFactory().get("/admin/users/operationalevent/")
        request.user = self.member
        model_admin = admin.site._registry[OperationalEvent]

        self.assertFalse(model_admin.has_module_permission(request))
        self.assertFalse(model_admin.has_view_permission(request))

    def test_verified_staff_can_render_operational_event_changelist(self):
        AuditLog.objects.create(
            action=AuditLog.Action.VERIFICATION_EMAIL_FAILED,
            target_user=self.member,
            details={"result": "failed", "error_type": "TimeoutError"},
        )
        device = TOTPDevice.objects.create(
            user=self.staff,
            name="Admin test device",
            confirmed=True,
        )
        self.client.force_login(self.staff)
        session = self.client.session
        session[DEVICE_ID_SESSION_KEY] = device.persistent_id
        session.save()

        response = self.client.get(
            reverse("admin:users_operationalevent_changelist")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "TimeoutError")

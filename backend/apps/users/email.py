import logging

from django.conf import settings
from django.core.mail import send_mail

from .models import AuditLog, EmailVerificationToken, write_audit_log


logger = logging.getLogger(__name__)


def _record_delivery_event(user, action, details):
    """Audit delivery state without allowing audit failure to block email delivery."""
    try:
        write_audit_log(
            action=action,
            target_user=user,
            details=details,
        )
    except Exception as exc:
        logger.error(
            "operational_event_write_failed component=verification_email user_id=%s error_type=%s",
            user.pk,
            type(exc).__name__,
        )


def send_verification_email(user):
    """Issue a replacement one-time link and send it without persisting the raw value."""
    raw_token, _ = EmailVerificationToken.issue_for(user)
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={raw_token}"
    try:
        send_mail(
            subject="Verify your juno.kim email address",
            message=(
                "Verify your email to enable comments and guestbook entries.\n\n"
                f"{verify_url}\n\n"
                f"This link expires in {settings.EMAIL_VERIFICATION_TOKEN_TTL_HOURS} hours and can only be used once."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as exc:
        _record_delivery_event(
            user,
            AuditLog.Action.VERIFICATION_EMAIL_FAILED,
            {"result": "failed", "error_type": type(exc).__name__},
        )
        raise

    _record_delivery_event(
        user,
        AuditLog.Action.VERIFICATION_EMAIL_SENT,
        {"result": "sent"},
    )
    logger.info("verification_email_sent user_id=%s", user.pk)

import logging

from django.conf import settings
from django.core.mail import send_mail

from .models import EmailVerificationToken


logger = logging.getLogger(__name__)


def send_verification_email(user):
    """Issue a replacement one-time link and send it without persisting the raw value."""
    raw_token, _ = EmailVerificationToken.issue_for(user)
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={raw_token}"
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
    logger.info("verification_email_sent user_id=%s", user.pk)

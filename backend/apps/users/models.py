import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models
from django.db import transaction
from django.utils import timezone

from .identity import validate_display_name, validate_username


def validate_avatar_size(file):
    max_size = 5 * 1024 * 1024
    if file.size > max_size:
        raise ValidationError("프로필 이미지는 5MB 이하여야 합니다.")


class User(AbstractUser):
    """로그인, 권한, 계정 식별 정보를 관리합니다."""

    email = models.EmailField("이메일", unique=True)

    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[RegexValidator(r"^[a-z0-9_]+$", "username은 영문 소문자, 숫자, 밑줄만 사용할 수 있습니다.")],
    )
    email_verified = models.BooleanField("email verified", default=False)
    email_verified_at = models.DateTimeField("email verified at", null=True, blank=True)

    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        self.username = self.username.strip()
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        validate_username(self.username)


class Profile(models.Model):
    """사용자에게 공개되는 선택적 프로필 정보를 관리합니다."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField("표시 이름", max_length=50, blank=True)
    bio = models.TextField("소개", blank=True)
    avatar = models.ImageField(
        "프로필 이미지",
        upload_to="profiles/%Y/%m/",
        blank=True,
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
            validate_avatar_size,
        ],
    )
    website_url = models.URLField("웹사이트", blank=True)
    github_url = models.URLField("GitHub", blank=True)
    created_at = models.DateTimeField("생성일", auto_now_add=True)
    updated_at = models.DateTimeField("수정일", auto_now=True)

    def __str__(self):
        return f"{self.user.username} profile"

    def clean(self):
        super().clean()
        validate_display_name(self.display_name)


class ImpersonationReport(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        REVIEWED = "reviewed", "Reviewed"
        DISMISSED = "dismissed", "Dismissed"

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="impersonation_reports")
    comment = models.ForeignKey("comments.Comment", null=True, blank=True, on_delete=models.CASCADE, related_name="impersonation_reports")
    guestbook_entry = models.ForeignKey("guestbook.GuestbookEntry", null=True, blank=True, on_delete=models.CASCADE, related_name="impersonation_reports")
    reason = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(
                condition=(models.Q(comment__isnull=False, guestbook_entry__isnull=True) | models.Q(comment__isnull=True, guestbook_entry__isnull=False)),
                name="impersonation_report_has_one_target",
            ),
        ]
        verbose_name = "Impersonation report"
        verbose_name_plural = "Impersonation reports"

    def __str__(self):
        return f"{self.reporter} report #{self.pk}"


class EmailVerificationToken(models.Model):
    """One-time email verification token. Only its SHA-256 digest is persisted."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="email_verification_tokens")
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    @classmethod
    def issue_for(cls, user):
        raw_token = secrets.token_urlsafe(32)
        now = timezone.now()
        cls.objects.filter(user=user, used_at__isnull=True).update(used_at=now)
        record = cls.objects.create(
            user=user,
            token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
            expires_at=now + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_TTL_HOURS),
        )
        return raw_token, record

    @classmethod
    def consume(cls, raw_token):
        digest = hashlib.sha256(raw_token.encode()).hexdigest()
        with transaction.atomic():
            record = cls.objects.select_for_update().select_related("user").filter(token_hash=digest, used_at__isnull=True).first()
            if not record or record.expires_at <= timezone.now():
                return None
            record.used_at = timezone.now()
            record.save(update_fields=("used_at",))
            return record


class AuditLog(models.Model):
    class Action(models.TextChoices):
        USER_PERMISSION_CHANGED = "user_permission_changed", "User permission changed"
        USER_ACTIVATION_CHANGED = "user_activation_changed", "User activation changed"
        CONTENT_STATUS_CHANGED = "content_status_changed", "Content status changed"
        CONTENT_DELETED = "content_deleted", "Content deleted"
        COMMENT_MODERATED = "comment_moderated", "Comment moderated"
        GUESTBOOK_MODERATED = "guestbook_moderated", "Guestbook moderated"
        MFA_ENROLLED = "mfa_enrolled", "MFA enrolled"
        MFA_REMOVED = "mfa_removed", "MFA removed"
        LOGIN_FAILED = "login_failed", "Login failed"
        LOGIN_LOCKED = "login_locked", "Login locked"

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_actions")
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_targets")
    action = models.CharField(max_length=64, choices=Action.choices)
    object_type = models.CharField(max_length=80, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Audit log"
        verbose_name_plural = "Audit logs"


def write_audit_log(*, action, actor=None, target_user=None, request=None, obj=None, details=None):
    """Persist only non-secret metadata for sensitive events."""
    from .security import get_client_ip

    return AuditLog.objects.create(
        action=action,
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        target_user=target_user,
        ip_address=get_client_ip(request) or None if request else None,
        object_type=obj._meta.label if obj is not None else "",
        object_id=str(obj.pk) if obj is not None and obj.pk else "",
        details=details or {},
    )

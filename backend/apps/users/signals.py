from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_login_failed
from django.db.models.signals import m2m_changed, post_delete, post_save, pre_save
from django.dispatch import receiver
from axes.signals import user_locked_out

from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from .models import AuditLog, Profile, User, write_audit_log
from django_otp.plugins.otp_totp.models import TOTPDevice


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


def revoke_refresh_tokens(user):
    """Blacklist every currently outstanding refresh token for a changed account."""
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)


@receiver(pre_save, sender=User)
def remember_security_relevant_user_fields(sender, instance, **kwargs):
    if not instance.pk:
        instance._security_before_save = None
        return
    instance._security_before_save = sender.objects.filter(pk=instance.pk).values(
        "is_active", "is_staff", "is_superuser", "password"
    ).first()


@receiver(post_save, sender=User)
def revoke_tokens_after_sensitive_user_change(sender, instance, created, **kwargs):
    previous = getattr(instance, "_security_before_save", None)
    if created or not previous:
        return
    changed = [
        field for field in ("is_active", "is_staff", "is_superuser", "password")
        if previous[field] != getattr(instance, field)
    ]
    if not changed:
        return
    revoke_refresh_tokens(instance)
    action = (
        AuditLog.Action.USER_ACTIVATION_CHANGED
        if changed == ["is_active"]
        else AuditLog.Action.USER_PERMISSION_CHANGED
    )
    write_audit_log(action=action, target_user=instance, details={"fields": changed})


@receiver(m2m_changed, sender=User.groups.through)
@receiver(m2m_changed, sender=User.user_permissions.through)
def revoke_tokens_after_permission_m2m_change(sender, instance, action, reverse, **kwargs):
    if action not in {"post_add", "post_remove", "post_clear"}:
        return
    if reverse:
        for user in kwargs.get("model").objects.filter(pk__in=kwargs.get("pk_set") or []):
            revoke_refresh_tokens(user)
            write_audit_log(action=AuditLog.Action.USER_PERMISSION_CHANGED, target_user=user, details={"relation": sender._meta.db_table})
        return
    revoke_refresh_tokens(instance)
    write_audit_log(action=AuditLog.Action.USER_PERMISSION_CHANGED, target_user=instance, details={"relation": sender._meta.db_table})


@receiver(user_login_failed)
def audit_login_failure(sender, credentials, request, **kwargs):
    # Do not store a password or other credentials in audit details.
    write_audit_log(
        action=AuditLog.Action.LOGIN_FAILED,
        request=request,
        details={"username": str(credentials.get("username", ""))[:150]},
    )


@receiver(user_locked_out)
def audit_login_lockout(sender, request, username=None, ip_address=None, **kwargs):
    write_audit_log(
        action=AuditLog.Action.LOGIN_LOCKED,
        request=request,
        details={"username": str(username or "")[:150], "ip_address": ip_address or ""},
    )


@receiver(post_delete, sender=TOTPDevice)
def audit_mfa_removal(sender, instance, **kwargs):
    write_audit_log(action=AuditLog.Action.MFA_REMOVED, target_user=instance.user, details={"device": instance.name})

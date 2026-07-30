"""Small, shared security helpers. Values such as credentials and tokens never belong here."""

from datetime import timedelta
from math import ceil

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from rest_framework.throttling import SimpleRateThrottle


RATE_LIMIT_STRIKE_RESET = timedelta(days=7)
RATE_LIMIT_STRIKE_DEDUPLICATION = timedelta(hours=1)
RATE_LIMIT_TEMPORARY_BLOCKS = {
    1: timedelta(hours=1),
    2: timedelta(hours=24),
}


def get_client_ip(request):
    """Nginx replaces this header with the direct client address before proxying."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


class AccountRateThrottle(SimpleRateThrottle):
    """Rate limit authenticated writes per account, independently from IP limits."""

    cache = cache
    scope = ""

    def get_cache_key(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return None
        return self.cache_format % {"scope": self.scope, "ident": f"user-{request.user.pk}"}


class IPRateThrottle(SimpleRateThrottle):
    """Rate limit writes per client IP, including users with different accounts."""

    cache = cache
    scope = ""

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": f"ip-{get_client_ip(request)}"}


class AccountHourlyModelThrottle(AccountRateThrottle):
    """Use both request history and shared database state for hourly limits."""

    scope = ""

    def get_queryset(self, user):
        raise NotImplementedError

    def allow_request(self, request, view):
        if not request.user or not request.user.is_authenticated or request.user.is_staff:
            return True
        now = timezone.now()
        if request.user.write_blocked_until and request.user.write_blocked_until > now:
            self._restriction_wait = ceil((request.user.write_blocked_until - now).total_seconds())
            return False

        request_allowed = super().allow_request(request, view)
        cutoff = now - timedelta(seconds=self.duration)
        database_allowed = self.get_queryset(request.user).filter(created_at__gte=cutoff).count() < self.num_requests
        if request_allowed and database_allowed:
            return True

        restriction = enforce_progressive_write_block(request.user, self.scope)
        blocked_until = restriction["blocked_until"]
        self._restriction_wait = (
            ceil((blocked_until - now).total_seconds())
            if blocked_until and blocked_until > now
            else None
        )
        return False

    def wait(self):
        if hasattr(self, "_restriction_wait"):
            return self._restriction_wait
        return super().wait()


def enforce_progressive_write_block(user, scope, *, now=None):
    """Apply one strike per rolling hour and escalate 1h -> 24h -> manual release."""
    from .models import AuditLog, User, write_audit_log

    now = now or timezone.now()
    with transaction.atomic():
        member = User.objects.select_for_update().get(pk=user.pk)

        if member.is_staff:
            return {
                "strike_count": member.rate_limit_strikes,
                "blocked_until": None,
                "permanent": False,
                "recorded": False,
            }
        if not member.is_active:
            return {
                "strike_count": member.rate_limit_strikes,
                "blocked_until": None,
                "permanent": True,
                "recorded": False,
            }
        if member.write_blocked_until and member.write_blocked_until > now:
            return {
                "strike_count": member.rate_limit_strikes,
                "blocked_until": member.write_blocked_until,
                "permanent": not member.is_active,
                "recorded": False,
            }
        if (
            member.last_rate_limit_strike_at
            and member.last_rate_limit_strike_at > now - RATE_LIMIT_STRIKE_DEDUPLICATION
        ):
            return {
                "strike_count": member.rate_limit_strikes,
                "blocked_until": member.write_blocked_until,
                "permanent": not member.is_active,
                "recorded": False,
            }

        if (
            not member.last_rate_limit_strike_at
            or member.last_rate_limit_strike_at <= now - RATE_LIMIT_STRIKE_RESET
        ):
            strike_count = 1
        else:
            strike_count = member.rate_limit_strikes + 1

        member.rate_limit_strikes = strike_count
        member.last_rate_limit_strike_at = now
        member.auto_blocked_at = None
        update_fields = [
            "rate_limit_strikes",
            "last_rate_limit_strike_at",
            "auto_blocked_at",
        ]

        block_duration = RATE_LIMIT_TEMPORARY_BLOCKS.get(strike_count)
        if block_duration:
            member.write_blocked_until = now + block_duration
            update_fields.append("write_blocked_until")
            stage = "one_hour" if strike_count == 1 else "one_day"
        else:
            member.write_blocked_until = None
            member.auto_blocked_at = now
            member.is_active = False
            update_fields.extend(("write_blocked_until", "is_active"))
            stage = "manual_release"

        member.save(update_fields=update_fields)
        write_audit_log(
            action=AuditLog.Action.RATE_LIMIT_ENFORCED,
            target_user=member,
            details={
                "result": "blocked",
                "scope": scope,
                "stage": stage,
                "strike_count": strike_count,
            },
        )
        return {
            "strike_count": strike_count,
            "blocked_until": member.write_blocked_until,
            "permanent": not member.is_active,
            "recorded": True,
        }


class CommentAccountThrottle(AccountRateThrottle):
    scope = "comment_user"


class CommentIPThrottle(IPRateThrottle):
    scope = "comment_ip"


class GuestbookAccountThrottle(AccountRateThrottle):
    scope = "guestbook_user"


class GuestbookIPThrottle(IPRateThrottle):
    scope = "guestbook_ip"


class PostAccountHourlyThrottle(AccountHourlyModelThrottle):
    scope = "post_user_hour"

    def get_queryset(self, user):
        from apps.posts.models import Post

        return Post.objects.filter(author=user)


class CommentAccountHourlyThrottle(AccountHourlyModelThrottle):
    scope = "comment_user_hour"

    def get_queryset(self, user):
        from apps.comments.models import Comment

        return Comment.objects.filter(author=user)


class GuestbookAccountHourlyThrottle(AccountHourlyModelThrottle):
    scope = "guestbook_user_hour"

    def get_queryset(self, user):
        from apps.guestbook.models import GuestbookEntry

        return GuestbookEntry.objects.filter(author=user)


class ContentImageAccountHourlyThrottle(AccountHourlyModelThrottle):
    scope = "content_image_user_hour"

    def get_queryset(self, user):
        from apps.posts.models import ContentImage

        return ContentImage.objects.filter(uploader=user)


class RegistrationIPBurstThrottle(IPRateThrottle):
    scope = "registration_ip_burst"


class RegistrationIPHourlyThrottle(IPRateThrottle):
    scope = "registration_ip_hour"


class RegistrationIPDailyThrottle(IPRateThrottle):
    scope = "registration_ip_day"


class VerificationResendAccountBurstThrottle(AccountRateThrottle):
    scope = "verification_resend_user_burst"


class VerificationResendAccountThrottle(AccountRateThrottle):
    scope = "verification_resend_user"


class VerificationResendAccountDailyThrottle(AccountRateThrottle):
    scope = "verification_resend_user_day"


class VerificationResendIPThrottle(IPRateThrottle):
    scope = "verification_resend_ip"


class VerificationResendIPDailyThrottle(IPRateThrottle):
    scope = "verification_resend_ip_day"


class ImpersonationReportAccountThrottle(AccountRateThrottle):
    scope = "impersonation_report_user"


class ImpersonationReportIPThrottle(IPRateThrottle):
    scope = "impersonation_report_ip"

"""Small, shared security helpers. Values such as credentials and tokens never belong here."""

from django.core.cache import cache
from rest_framework.throttling import SimpleRateThrottle


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


class CommentAccountThrottle(AccountRateThrottle):
    scope = "comment_user"


class CommentIPThrottle(IPRateThrottle):
    scope = "comment_ip"


class GuestbookAccountThrottle(AccountRateThrottle):
    scope = "guestbook_user"


class GuestbookIPThrottle(IPRateThrottle):
    scope = "guestbook_ip"


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

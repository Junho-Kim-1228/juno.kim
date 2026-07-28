from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403


DEBUG = False

if not SECRET_KEY or len(SECRET_KEY) < 50 or SECRET_KEY.startswith("django-insecure-"):  # noqa: F405
    raise ImproperlyConfigured("운영 환경의 강력한 SECRET_KEY를 설정해야 합니다.")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])  # noqa: F405
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("운영 환경의 ALLOWED_HOSTS를 설정해야 합니다.")

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405
if not CSRF_TRUSTED_ORIGINS:
    raise ImproperlyConfigured("운영 환경의 CSRF_TRUSTED_ORIGINS를 설정해야 합니다.")

EXPECTED_ORIGIN = "https://juno.kim"
if set(CORS_ALLOWED_ORIGINS) != {EXPECTED_ORIGIN}:  # noqa: F405
    raise ImproperlyConfigured("운영 CORS는 https://juno.kim만 허용해야 합니다.")
if set(CSRF_TRUSTED_ORIGINS) != {EXPECTED_ORIGIN}:
    raise ImproperlyConfigured("운영 CSRF 신뢰 출처는 https://juno.kim만 허용해야 합니다.")
if ADMIN_URL != "admin/":  # noqa: F405
    raise ImproperlyConfigured("ADMIN_URL은 Nginx 프록시 경로인 admin/과 일치해야 합니다.")

SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
JWT_REFRESH_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)  # noqa: F405
if SECURE_HSTS_SECONDS < 31536000:
    raise ImproperlyConfigured("운영 SECURE_HSTS_SECONDS는 31536000 이상이어야 합니다.")
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(  # noqa: F405
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=False,
)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)  # noqa: F405

from .base import *  # noqa: F403


DEBUG = env.bool("DEBUG", default=True)  # noqa: F405
SECRET_KEY = env.str(  # noqa: F405
    "SECRET_KEY",
    default="django-insecure-local-development-only-change-before-production",
)
ALLOWED_HOSTS = env.list(  # noqa: F405
    "ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1"],
)

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
JWT_REFRESH_COOKIE_SECURE = False

TEST_DATABASE_URL = env.str("TEST_DATABASE_URL", default="")  # noqa: F405
if TEST_DATABASE_URL:
    DATABASES = {"default": env.db_url_config(TEST_DATABASE_URL)}  # noqa: F405

from django.urls import path

from .views import (
    CsrfTokenView,
    LoginView,
    LogoutView,
    MeView,
    ProfileView,
    RefreshView,
    RegistrationView,
    ResendVerificationEmailView,
    ImpersonationReportCreateView,
    VerifyEmailView,
)


urlpatterns = [
    path("auth/csrf/", CsrfTokenView.as_view(), name="csrf-token"),
    path("auth/register/", RegistrationView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", RefreshView.as_view(), name="token-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("auth/resend-verification/", ResendVerificationEmailView.as_view(), name="resend-verification"),
    path("reports/impersonation/", ImpersonationReportCreateView.as_view(), name="impersonation-report"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("auth/profile/", ProfileView.as_view(), name="profile"),
]

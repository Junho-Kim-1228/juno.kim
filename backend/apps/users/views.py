import logging

from django.conf import settings
from django.contrib.auth import authenticate
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .cookies import delete_refresh_cookie, set_refresh_cookie
from .email import send_verification_email
from .models import EmailVerificationToken, ImpersonationReport
from apps.permissions import IsActiveAuthenticated, IsVerifiedUserOrReadOnly
from .security import (
    ImpersonationReportAccountThrottle,
    ImpersonationReportIPThrottle,
    RegistrationIPBurstThrottle,
    RegistrationIPDailyThrottle,
    RegistrationIPHourlyThrottle,
    VerificationResendAccountBurstThrottle,
    VerificationResendAccountDailyThrottle,
    VerificationResendAccountThrottle,
    VerificationResendIPDailyThrottle,
    VerificationResendIPThrottle,
)
from .serializers import (
    LoginSerializer,
    PasswordChangeSerializer,
    ProfileSerializer,
    RegistrationSerializer,
    UserSerializer,
)


logger = logging.getLogger(__name__)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfTokenView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response({"csrfToken": get_token(request)})


@method_decorator(csrf_protect, name="dispatch")
class RegistrationView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = RegistrationSerializer
    throttle_classes = (
        RegistrationIPBurstThrottle,
        RegistrationIPHourlyThrottle,
        RegistrationIPDailyThrottle,
    )

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = self.get_queryset().get(username=response.data["username"])
        try:
            send_verification_email(user)
            sent = True
        except Exception as exc:
            # Never expose mail-provider details or a verification token to the client.
            logger.warning(
                "verification_email_send_failed context=registration user_id=%s error_type=%s",
                user.pk,
                type(exc).__name__,
            )
            sent = False
        data = UserSerializer(user, context=self.get_serializer_context()).data
        data["verification_email_sent"] = sent
        return Response(data, status=201)

    def get_queryset(self):
        from .models import User

        return User.objects.select_related("profile")


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request=request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if user is None or not user.is_active:
            return Response(
                {"detail": "아이디 또는 비밀번호가 올바르지 않습니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        response = Response(
            {
                "access": str(refresh.access_token),
                "user": UserSerializer(user, context={"request": request}).data,
            }
        )
        set_refresh_cookie(response, str(refresh))
        return response


@method_decorator(csrf_protect, name="dispatch")
class RefreshView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth"

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
        if not refresh_token:
            return Response(
                {"detail": "Refresh Token이 없습니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        rotated_refresh = data.pop("refresh", None)
        response = Response(data)
        if rotated_refresh:
            set_refresh_cookie(response, rotated_refresh)
        return response


@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass
        response = Response(status=status.HTTP_204_NO_CONTENT)
        delete_refresh_cookie(response)
        return response


@method_decorator(csrf_protect, name="dispatch")
class PasswordChangeView(APIView):
    permission_classes = (IsActiveAuthenticated,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth"

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=("password",))

        # Saving the password revokes all existing refresh tokens through the
        # user security signal. Issue one new token only for this device.
        refresh = RefreshToken.for_user(request.user)
        response = Response(
            {
                "access": str(refresh.access_token),
                "detail": "비밀번호를 변경했습니다.",
            }
        )
        set_refresh_cookie(response, str(refresh))
        return response


@method_decorator(csrf_protect, name="dispatch")
class VerifyEmailView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth"

    def post(self, request):
        raw_token = str(request.data.get("token", ""))
        record = EmailVerificationToken.consume(raw_token)
        if not record:
            return Response({"detail": "This verification link is invalid, expired, or already used."}, status=status.HTTP_400_BAD_REQUEST)
        user = record.user
        user.email_verified = True
        from django.utils import timezone
        user.email_verified_at = timezone.now()
        user.save(update_fields=("email_verified", "email_verified_at"))
        return Response({"detail": "Email verified."})


@method_decorator(csrf_protect, name="dispatch")
class ResendVerificationEmailView(APIView):
    permission_classes = (IsActiveAuthenticated,)
    throttle_classes = (
        VerificationResendAccountBurstThrottle,
        VerificationResendAccountThrottle,
        VerificationResendAccountDailyThrottle,
        VerificationResendIPThrottle,
        VerificationResendIPDailyThrottle,
    )

    def post(self, request):
        if request.user.email_verified:
            return Response({"detail": "Email is already verified."})
        try:
            send_verification_email(request.user)
        except Exception as exc:
            logger.warning(
                "verification_email_send_failed context=resend user_id=%s error_type=%s",
                request.user.pk,
                type(exc).__name__,
            )
            return Response({"detail": "Unable to send verification email right now. Please try again later."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({"detail": "Verification email sent."})


@method_decorator(csrf_protect, name="dispatch")
class ImpersonationReportCreateView(APIView):
    permission_classes = (IsVerifiedUserOrReadOnly,)
    throttle_classes = (ImpersonationReportAccountThrottle, ImpersonationReportIPThrottle)

    def post(self, request):
        target_type = str(request.data.get("target_type", ""))
        try:
            target_id = int(request.data.get("target_id"))
        except (TypeError, ValueError):
            return Response({"detail": "Invalid report target."}, status=status.HTTP_400_BAD_REQUEST)
        reason = str(request.data.get("reason", "")).strip()
        if not reason or len(reason) > 500:
            return Response({"detail": "Report reason must be between 1 and 500 characters."}, status=status.HTTP_400_BAD_REQUEST)

        if target_type == "comment":
            from apps.comments.models import Comment

            target = Comment.objects.filter(
                pk=target_id,
                is_active=True,
                post__status="published",
            ).first()
            if not target:
                return Response({"detail": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)
            if target.author_id == request.user.id:
                return Response({"detail": "You cannot report your own content."}, status=status.HTTP_400_BAD_REQUEST)
            report, created = ImpersonationReport.objects.get_or_create(
                reporter=request.user,
                comment=target,
                defaults={"reason": reason},
            )
            if not created:
                return Response({"detail": "You have already reported this item."}, status=status.HTTP_400_BAD_REQUEST)
        elif target_type == "guestbook":
            from apps.guestbook.models import GuestbookEntry

            target = GuestbookEntry.objects.filter(pk=target_id, is_visible=True).first()
            if not target:
                return Response({"detail": "Guestbook entry not found."}, status=status.HTTP_404_NOT_FOUND)
            if target.author_id == request.user.id:
                return Response({"detail": "You cannot report your own content."}, status=status.HTTP_400_BAD_REQUEST)
            report, created = ImpersonationReport.objects.get_or_create(
                reporter=request.user,
                guestbook_entry=target,
                defaults={"reason": reason},
            )
            if not created:
                return Response({"detail": "You have already reported this item."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"detail": "Invalid report target."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"id": report.id, "detail": "Report received."}, status=status.HTTP_201_CREATED)


class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsActiveAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        old_email = self.request.user.email
        user = serializer.save()
        if user.email != old_email:
            try:
                send_verification_email(user)
            except Exception as exc:
                logger.warning(
                    "verification_email_send_failed context=email_change user_id=%s error_type=%s",
                    user.pk,
                    type(exc).__name__,
                )


class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsActiveAuthenticated,)
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user.profile

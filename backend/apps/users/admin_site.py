from base64 import b64encode

import qrcode
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect
from django_otp import login as otp_login
from django_otp.plugins.otp_totp.models import TOTPDevice
from qrcode.image.svg import SvgPathImage

from .models import AuditLog, write_audit_log


def qr_data_uri(provisioning_uri):
    """Render the provisioning URI as an in-memory SVG; never write the secret to disk."""
    image = qrcode.make(provisioning_uri, image_factory=SvgPathImage)
    encoded_svg = b64encode(image.to_string()).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded_svg}"


class SecureAdminSite(admin.AdminSite):
    """Require a verified TOTP device before any Django Admin view is usable."""

    def has_permission(self, request):
        return super().has_permission(request) and request.user.is_verified()

    def admin_view(self, view, cacheable=False):
        protected_view = super().admin_view(view, cacheable=cacheable)

        def wrapped(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.is_active and request.user.is_staff and not request.user.is_verified():
                return redirect(reverse("admin:mfa_setup"))
            return protected_view(request, *args, **kwargs)

        return wrapped

    def get_urls(self):
        return [path("mfa/setup/", self.mfa_setup_view, name="mfa_setup")] + super().get_urls()

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def mfa_setup_view(self, request):
        if not request.user.is_active or not request.user.is_staff:
            raise PermissionDenied

        device = TOTPDevice.objects.filter(user=request.user).order_by("id").first()
        error = ""
        if request.method == "POST":
            if request.POST.get("action") == "reset" and device and not device.confirmed:
                device.delete()
                return redirect(reverse("admin:mfa_setup"))

            token = request.POST.get("token", "").replace(" ", "")
            if device and token and device.verify_token(token):
                if not device.confirmed:
                    device.confirmed = True
                    device.save(update_fields=("confirmed",))
                    write_audit_log(action=AuditLog.Action.MFA_ENROLLED, actor=request.user, target_user=request.user, request=request)
                otp_login(request, device)
                return redirect(reverse("admin:index"))
            error = "인증 코드가 올바르지 않습니다. 앱의 현재 6자리 코드를 다시 입력해 주세요."

        if device is None:
            device = TOTPDevice.objects.create(user=request.user, name="Django Admin", confirmed=False)

        csrf_input = format_html('<input type="hidden" name="csrfmiddlewaretoken" value="{}">', get_token(request))
        if device.confirmed:
            setup_content = format_html("<p>인증 앱에 표시되는 현재 6자리 코드를 입력해 주세요.</p>")
        else:
            manual_session_key = f"admin_mfa_manual_key_seen_{device.pk}"
            show_manual_key = not request.session.get(manual_session_key, False)
            if show_manual_key:
                request.session[manual_session_key] = True
            manual_content = format_html(
                "<details><summary>QR 코드를 스캔할 수 없나요?</summary>"
                "<p>수동 키는 이 화면에서 한 번만 표시됩니다. 다른 사람에게 공유하지 마세요.</p><code>{}</code></details>",
                device.key,
            ) if show_manual_key else format_html("<p class='muted'>수동 키는 이미 표시되었습니다. 필요하면 아래에서 새 QR 코드를 만드세요.</p>")
            setup_content = format_html(
                "<p>인증 앱(Google 또는 Microsoft Authenticator 등)으로 아래 QR 코드를 스캔해 주세요.</p>"
                "<img class='mfa-qr' src='{}' alt='관리자 MFA QR 코드'><p>스캔한 뒤 앱에 표시되는 6자리 코드를 입력하면 등록됩니다.</p>{}"
                "<form method='post' class='reset-form'>{}<input type='hidden' name='action' value='reset'><button type='submit'>새 QR 코드 만들기</button></form>",
                qr_data_uri(device.config_url),
                manual_content,
                csrf_input,
            )

        page = format_html(
            "<!doctype html><html><head><meta charset='utf-8'><title>관리자 2단계 인증</title>"
            "<style>body{{margin:0;background:#faf8f3;color:#302e2a;font-family:'Malgun Gothic','맑은 고딕',sans-serif;line-height:1.6}}"
            "main{{max-width:32rem;margin:4rem auto;padding:2rem;background:#fffdf8;border:1px solid #e7dfd3;border-radius:8px}}"
            "h1{{margin-top:0;font-size:1.55rem}} .mfa-qr{{display:block;width:220px;height:220px;margin:1.25rem 0;border:10px solid white}}"
            "details{{margin:1.25rem 0;padding:1rem;background:#f3eee5}} code{{display:block;margin-top:.75rem;overflow-wrap:anywhere}}"
            "input{{padding:.55rem;border:1px solid #bdb5a8}} button{{padding:.55rem .8rem;border:1px solid #247565;background:#247565;color:white;border-radius:4px;cursor:pointer}}"
            ".reset-form{{margin:1rem 0}} .reset-form button{{background:transparent;color:#247565;border:1px solid #247565}} .error{{color:#b42318}}</style>"
            "</head><body><main><h1>관리자 2단계 인증</h1>{}<form method='post'>{}"
            "<label>인증 코드 <input name='token' inputmode='numeric' autocomplete='one-time-code' required autofocus></label>"
            "<button type='submit'>확인</button></form><p class='error'>{}</p></main></body></html>",
            setup_content,
            csrf_input,
            error,
        )
        return HttpResponse(page)


# Preserve existing model registrations while applying the MFA gate to /admin/.
admin.site.__class__ = SecureAdminSite

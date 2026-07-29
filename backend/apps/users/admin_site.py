from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import escape, format_html
from django.utils.decorators import method_decorator
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect
from django_otp import login as otp_login
from django_otp.plugins.otp_totp.models import TOTPDevice

from .models import AuditLog, write_audit_log


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
            token = request.POST.get("token", "").replace(" ", "")
            if device and token and device.verify_token(token):
                if not device.confirmed:
                    device.confirmed = True
                    device.save(update_fields=("confirmed",))
                    write_audit_log(action=AuditLog.Action.MFA_ENROLLED, actor=request.user, target_user=request.user, request=request)
                otp_login(request, device)
                return redirect(reverse("admin:index"))
            error = "The authentication code is invalid. Please try again."

        if device is None:
            device = TOTPDevice.objects.create(user=request.user, name="Django Admin", confirmed=False)

        if device.confirmed:
            setup_hint = "Enter a code from your authenticator app to continue."
            provisioning = ""
        else:
            setup_hint = "Add this account to an authenticator app, then enter its current code. Keep the secret private."
            provisioning = format_html("<p><strong>Manual key:</strong> <code>{}</code></p><p>Issuer/account URI: <code>{}</code></p>", device.key, device.config_url)
        csrf_input = format_html('<input type="hidden" name="csrfmiddlewaretoken" value="{}">', get_token(request))
        page = format_html(
            "<!doctype html><html><head><meta charset='utf-8'><title>Admin MFA</title></head><body>"
            "<main style='max-width:34rem;margin:4rem auto;font-family:sans-serif'><h1>Admin MFA</h1><p>{}</p>{}"
            "<form method='post'>{}<label>Authentication code <input name='token' inputmode='numeric' autocomplete='one-time-code' required autofocus></label>"
            "<button type='submit'>Verify</button></form><p style='color:#b00'>{}</p></main></body></html>",
            setup_hint, provisioning, csrf_input, error,
        )
        return HttpResponse(page)


# Preserve existing model registrations while applying the MFA gate to /admin/.
admin.site.__class__ = SecureAdminSite

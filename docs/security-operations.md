# Security operations

## Roles

- Member: can read public content and, after email verification, write a guestbook entry and manage only their own comments.
- Content staff (`is_staff=True`, `is_superuser=False`): can manage content, comments, and guestbook visibility in Django Admin. They cannot see or edit users, passwords, groups, or permissions.
- Superuser: is the only role that can manage users and assign or revoke staff/superuser privileges.

## Email verification

New accounts are normal, unverified users. They can sign in but cannot write comments or guestbook entries until they use the one-time link sent to their email. Links expire after `EMAIL_VERIFICATION_TOKEN_TTL_HOURS` (24 by default); a resend invalidates the prior unused link.

Production mail settings belong only in `/etc/juno-kim/juno-kim.env`:

```dotenv
FRONTEND_URL=https://juno.kim
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=mail-account
EMAIL_HOST_PASSWORD=mail-provider-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@juno.kim
EMAIL_VERIFICATION_TOKEN_TTL_HOURS=24
```

After changing those values, deploy normally or restart only `juno-kim.service`. Do not put SMTP credentials in GitHub, source files, or chat logs.

## Identity and impersonation reports

Public authors are displayed as `display name (@username)`. Only staff accounts receive the server-provided **사이트 운영자** badge. Usernames and display names that contain the operator's identity or authority terms (such as `admin`, `official`, `운영자`, or `juno kim`) are rejected.

Verified members can report publicly visible comments and guestbook entries. A member can report each item only once; reports are rate-limited to 10 per hour per account and 20 per hour per IP. A report never automatically hides content or disables an account.

Before deploying an identity-policy change, run this read-only check from the backend directory:

```bash
python manage.py check_identity_conflicts --strict
```

It reports only record IDs and public usernames/display names, changes no data, and exits non-zero if an existing account conflicts with the current policy. Resolve each result manually before tightening the policy further.

## Admin MFA

Every staff account must register a TOTP authenticator before Admin pages become available. After the username/password step, Admin redirects to `/admin/mfa/setup/`. Scan the displayed QR code with an authenticator app, then enter the current six-digit code. The manual key is a collapsed fallback and is shown only once per enrollment session; it is never written to this repository or audit log. If a QR or key is exposed, use **새 QR 코드 만들기** before completing enrollment.

For the first superuser, use a server console only after confirming the operator's identity:

```bash
cd /var/www/juno-kim/backend
sudo -u juno-kim /var/www/juno-kim/backend/.venv/bin/python manage.py createsuperuser
```

If an administrator loses their device, a verified superuser should remove only that user's `TOTPDevice` through the Django shell after identity verification. The affected user can then sign in and enroll again. Never copy a TOTP key or recovery code into tickets, source control, or messages.

## Login protection and audit records

django-axes locks repeated login failures using the combined username and client IP after 5 failures for 30 minutes. Nginx also limits `/admin/login/` to 5 requests/minute per IP. Wait for the cooldown or have a verified superuser clear the relevant Axes attempt in Django Admin; do not weaken the global policy for a single account.

Audit logs are read-only and visible only to superusers at `/admin/`. They include privilege changes, account activation changes, moderation, content state changes/deletions, MFA enrollment, and login failures/lockouts. Passwords, JWTs, refresh tokens, and TOTP secrets are never recorded.

## Token revocation

Logout blacklists the current refresh token. Any account deactivation, password change, staff/superuser change, group change, or user-permission change blacklists all outstanding refresh tokens for that user. Access tokens remain limited to 15 minutes, and every protected API request reloads current user permissions.

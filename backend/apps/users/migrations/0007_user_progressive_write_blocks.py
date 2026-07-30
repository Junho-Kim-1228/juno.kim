from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0006_operationalevent_alter_auditlog_action"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="auto_blocked_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="automatically blocked at"),
        ),
        migrations.AddField(
            model_name="user",
            name="last_rate_limit_strike_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="last rate limit strike at"),
        ),
        migrations.AddField(
            model_name="user",
            name="rate_limit_strikes",
            field=models.PositiveSmallIntegerField(default=0, verbose_name="rate limit strikes"),
        ),
        migrations.AddField(
            model_name="user",
            name="write_blocked_until",
            field=models.DateTimeField(blank=True, null=True, verbose_name="write blocked until"),
        ),
        migrations.AlterField(
            model_name="auditlog",
            name="action",
            field=models.CharField(
                choices=[
                    ("user_permission_changed", "User permission changed"),
                    ("user_activation_changed", "User activation changed"),
                    ("content_status_changed", "Content status changed"),
                    ("content_deleted", "Content deleted"),
                    ("comment_moderated", "Comment moderated"),
                    ("guestbook_moderated", "Guestbook moderated"),
                    ("mfa_enrolled", "MFA enrolled"),
                    ("mfa_removed", "MFA removed"),
                    ("login_failed", "Login failed"),
                    ("login_locked", "Login locked"),
                    ("verification_email_sent", "Verification email sent"),
                    ("verification_email_failed", "Verification email failed"),
                    ("rate_limit_enforced", "Rate limit enforced"),
                ],
                max_length=64,
            ),
        ),
    ]

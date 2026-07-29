from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0005_alter_user_managers"),
    ]

    operations = [
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
                ],
                max_length=64,
            ),
        ),
        migrations.CreateModel(
            name="OperationalEvent",
            fields=[],
            options={
                "verbose_name": "운영 기록",
                "verbose_name_plural": "운영 기록",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("users.auditlog",),
        ),
    ]

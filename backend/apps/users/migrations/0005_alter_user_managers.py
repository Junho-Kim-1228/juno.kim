import apps.users.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_impersonation_report_duplicate_guards"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="user",
            managers=[("objects", apps.users.models.SecureUserManager())],
        ),
    ]

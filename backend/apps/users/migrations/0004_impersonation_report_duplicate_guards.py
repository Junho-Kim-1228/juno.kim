from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_alter_user_username_impersonationreport"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="impersonationreport",
            constraint=models.UniqueConstraint(
                condition=models.Q(("comment__isnull", False)),
                fields=("reporter", "comment"),
                name="unique_reporter_comment_impersonation_report",
            ),
        ),
        migrations.AddConstraint(
            model_name="impersonationreport",
            constraint=models.UniqueConstraint(
                condition=models.Q(("guestbook_entry__isnull", False)),
                fields=("reporter", "guestbook_entry"),
                name="unique_reporter_guestbook_impersonation_report",
            ),
        ),
    ]

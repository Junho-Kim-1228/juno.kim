from django.db import migrations, models


def archived_to_private(apps, schema_editor):
    Post = apps.get_model("posts", "Post")
    Post.objects.filter(status="archived").update(status="private")


def private_to_archived(apps, schema_editor):
    Post = apps.get_model("posts", "Post")
    Post.objects.filter(status="private").update(status="archived")


class Migration(migrations.Migration):
    dependencies = [
        ("posts", "0003_post_kind"),
    ]

    operations = [
        migrations.RunPython(archived_to_private, private_to_archived),
        migrations.AlterField(
            model_name="post",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "임시저장"),
                    ("published", "공개"),
                    ("private", "비공개"),
                ],
                default="draft",
                max_length=16,
                verbose_name="상태",
            ),
        ),
    ]

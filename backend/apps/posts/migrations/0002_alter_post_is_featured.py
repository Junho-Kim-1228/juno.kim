from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("posts", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="post",
            name="is_featured",
            field=models.BooleanField(default=False, verbose_name="공지 게시글"),
        ),
    ]

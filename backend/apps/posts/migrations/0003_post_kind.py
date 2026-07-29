from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("posts", "0002_alter_post_is_featured"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="kind",
            field=models.CharField(
                choices=[("board", "게시판 글"), ("technical", "기술 기록")],
                default="board",
                max_length=16,
                verbose_name="게시 위치",
            ),
        ),
    ]

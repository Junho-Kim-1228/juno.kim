from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("guestbook", "0002_guestbookentry_author"),
    ]

    operations = [
        migrations.AddField(
            model_name="guestbookentry",
            name="staff_reply",
            field=models.TextField(blank=True, max_length=500, verbose_name="운영자 답장"),
        ),
        migrations.AddField(
            model_name="guestbookentry",
            name="staff_replied_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="답장 작성일"),
        ),
        migrations.AddField(
            model_name="guestbookentry",
            name="staff_replied_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="guestbook_staff_replies",
                to=settings.AUTH_USER_MODEL,
                verbose_name="답장 작성자",
            ),
        ),
        migrations.CreateModel(
            name="TodayStatus",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("mood", models.CharField(blank=True, max_length=40, verbose_name="오늘 기분")),
                ("doing", models.CharField(blank=True, max_length=120, verbose_name="하는 중")),
                ("listening", models.CharField(blank=True, max_length=120, verbose_name="듣는 중")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="수정일")),
            ],
            options={
                "verbose_name": "오늘의 김준호",
                "verbose_name_plural": "오늘의 김준호",
                "ordering": ("-updated_at", "-id"),
            },
        ),
    ]

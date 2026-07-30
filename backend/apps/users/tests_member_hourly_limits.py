from datetime import timedelta
from io import BytesIO
from unittest.mock import patch

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from apps.comments.models import Comment
from apps.guestbook.models import GuestbookEntry
from apps.posts.models import Post

from .models import AuditLog, User
from .security import (
    CommentAccountHourlyThrottle,
    ContentImageAccountHourlyThrottle,
    GuestbookAccountHourlyThrottle,
    PostAccountHourlyThrottle,
    enforce_progressive_write_block,
)


def make_image_file(name):
    buffer = BytesIO()
    Image.new("RGB", (24, 24), "#247565").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.memory.InMemoryStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
)
class MemberHourlyWriteLimitTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.member = User.objects.create_user(
            username="limited_member",
            email="limited-member@example.com",
            password="StrongTemporary!2026",
            email_verified=True,
        )
        self.staff = User.objects.create_user(
            username="content_editor",
            email="unlimited-staff@example.com",
            password="StrongTemporary!2026",
            is_staff=True,
            email_verified=True,
        )
        self.post = Post.objects.create(
            author=self.staff,
            title="Comment target",
            excerpt="excerpt",
            content="content",
            status=Post.Status.PUBLISHED,
        )

    def create_post(self, index):
        return self.client.post(
            "/api/v1/posts/",
            {
                "title": f"Post {index}",
                "excerpt": "excerpt",
                "content": "content",
                "status": Post.Status.PUBLISHED,
            },
            format="json",
        )

    def create_comment(self, index):
        return self.client.post(
            "/api/v1/comments/",
            {"post_slug": self.post.slug, "content": f"Comment {index}"},
            format="json",
        )

    def create_guestbook_entry(self, index):
        return self.client.post(
            "/api/v1/guestbook/",
            {"message": f"Guestbook {index}"},
            format="json",
        )

    def upload_image(self, index):
        return self.client.post(
            "/api/v1/content-images/",
            {"image": make_image_file(f"image-{index}.png")},
            format="multipart",
        )

    def assert_member_limit(self, create, throttle_class):
        self.client.force_authenticate(self.member)
        with patch.object(throttle_class, "rate", "2/hour", create=True):
            self.assertEqual(create(0).status_code, status.HTTP_201_CREATED)
            self.assertEqual(create(1).status_code, status.HTTP_201_CREATED)
            self.assertEqual(create(2).status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.member.refresh_from_db()
        self.assertEqual(self.member.rate_limit_strikes, 1)
        self.assertGreater(self.member.write_blocked_until, timezone.now())
        self.assertTrue(self.member.is_active)

    def assert_staff_bypass(self, create):
        cache.clear()
        self.client.force_authenticate(self.staff)
        self.assertEqual(
            [create(index).status_code for index in range(3)],
            [status.HTTP_201_CREATED] * 3,
        )

    def test_member_post_daily_limit_and_staff_bypass(self):
        self.assert_member_limit(self.create_post, PostAccountHourlyThrottle)
        self.assert_staff_bypass(self.create_post)

    def test_member_comment_daily_limit_and_staff_bypass(self):
        self.assert_member_limit(self.create_comment, CommentAccountHourlyThrottle)
        self.assert_staff_bypass(self.create_comment)

    def test_member_guestbook_daily_limit_and_staff_bypass(self):
        self.assert_member_limit(self.create_guestbook_entry, GuestbookAccountHourlyThrottle)
        self.assert_staff_bypass(self.create_guestbook_entry)

    def test_member_image_daily_limit_and_staff_bypass(self):
        self.assert_member_limit(self.upload_image, ContentImageAccountHourlyThrottle)
        self.assert_staff_bypass(self.upload_image)

    def test_production_hourly_limits_match_policy(self):
        rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
        self.assertEqual(rates["post_user_hour"], "5/hour")
        self.assertEqual(rates["comment_user_hour"], "20/hour")
        self.assertEqual(rates["guestbook_user_hour"], "5/hour")
        self.assertEqual(rates["content_image_user_hour"], "5/hour")


class InactiveMemberContentVisibilityTests(APITestCase):
    def setUp(self):
        self.member = User.objects.create_user(
            username="disabled_member",
            email="disabled-member@example.com",
            password="StrongTemporary!2026",
            email_verified=True,
        )
        self.post = Post.objects.create(
            author=self.member,
            title="Hidden after deactivation",
            excerpt="excerpt",
            content="content",
            status=Post.Status.PUBLISHED,
        )
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.member,
            content="hidden comment",
        )
        self.entry = GuestbookEntry.objects.create(
            author=self.member,
            name=self.member.username,
            message="hidden guestbook entry",
        )

    def test_deactivated_members_public_content_is_hidden(self):
        self.member.is_active = False
        self.member.save(update_fields=("is_active",))

        posts = self.client.get("/api/v1/posts/")
        comments = self.client.get("/api/v1/comments/", {"post": self.post.slug})
        guestbook = self.client.get("/api/v1/guestbook/")

        self.assertEqual(posts.status_code, status.HTTP_200_OK)
        self.assertEqual(comments.status_code, status.HTTP_200_OK)
        self.assertEqual(guestbook.status_code, status.HTTP_200_OK)
        self.assertEqual(posts.data["count"], 0)
        self.assertEqual(comments.data["count"], 0)
        self.assertEqual(guestbook.data["count"], 0)


class ProgressiveWriteBlockTests(APITestCase):
    def setUp(self):
        self.member = User.objects.create_user(
            username="progressive_member",
            email="progressive-member@example.com",
            password="StrongTemporary!2026",
            email_verified=True,
        )

    def test_three_distinct_hourly_breaches_escalate_to_manual_release(self):
        first_at = timezone.now()

        first = enforce_progressive_write_block(self.member, "post_user_hour", now=first_at)
        self.member.refresh_from_db()
        self.assertTrue(first["recorded"])
        self.assertEqual(self.member.rate_limit_strikes, 1)
        self.assertEqual(self.member.write_blocked_until, first_at + timedelta(hours=1))
        self.assertTrue(self.member.is_active)

        duplicate = enforce_progressive_write_block(
            self.member,
            "comment_user_hour",
            now=first_at + timedelta(minutes=30),
        )
        self.member.refresh_from_db()
        self.assertFalse(duplicate["recorded"])
        self.assertEqual(self.member.rate_limit_strikes, 1)

        second_at = first_at + timedelta(hours=2)
        second = enforce_progressive_write_block(self.member, "guestbook_user_hour", now=second_at)
        self.member.refresh_from_db()
        self.assertTrue(second["recorded"])
        self.assertEqual(self.member.rate_limit_strikes, 2)
        self.assertEqual(self.member.write_blocked_until, second_at + timedelta(hours=24))
        self.assertTrue(self.member.is_active)

        third_at = first_at + timedelta(hours=27)
        third = enforce_progressive_write_block(self.member, "content_image_user_hour", now=third_at)
        self.member.refresh_from_db()
        self.assertTrue(third["recorded"])
        self.assertEqual(self.member.rate_limit_strikes, 3)
        self.assertIsNone(self.member.write_blocked_until)
        self.assertEqual(self.member.auto_blocked_at, third_at)
        self.assertFalse(self.member.is_active)
        self.assertEqual(
            AuditLog.objects.filter(
                action=AuditLog.Action.RATE_LIMIT_ENFORCED,
                target_user=self.member,
            ).count(),
            3,
        )

    def test_strikes_reset_after_seven_quiet_days(self):
        first_at = timezone.now()
        enforce_progressive_write_block(self.member, "post_user_hour", now=first_at)

        after_reset = enforce_progressive_write_block(
            self.member,
            "post_user_hour",
            now=first_at + timedelta(days=8),
        )
        self.member.refresh_from_db()

        self.assertTrue(after_reset["recorded"])
        self.assertEqual(self.member.rate_limit_strikes, 1)
        self.assertTrue(self.member.is_active)

    def test_temporary_block_applies_across_all_limited_write_types(self):
        enforce_progressive_write_block(self.member, "post_user_hour")
        self.member.refresh_from_db()
        self.client.force_authenticate(self.member)

        response = self.client.post(
            "/api/v1/guestbook/",
            {"message": "blocked during the shared cooldown"},
            format="json",
        )
        self.member.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(self.member.rate_limit_strikes, 1)

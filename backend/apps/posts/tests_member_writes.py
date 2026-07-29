from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User

from .models import Category, Post, Tag


class VerifiedMemberPostWriteTests(APITestCase):
    def setUp(self):
        self.member = User.objects.create_user(
            username="verified_writer",
            email="verified-writer@example.com",
            password="StrongTemporary!2026",
            email_verified=True,
        )
        self.other = User.objects.create_user(
            username="other_writer",
            email="other-writer@example.com",
            password="StrongTemporary!2026",
            email_verified=True,
        )
        self.category = Category.objects.create(name="Daily")
        self.tag = Tag.objects.create(name="Story")
        self.other_post = Post.objects.create(
            author=self.other,
            title="Other Post",
            excerpt="excerpt",
            content="content",
            status=Post.Status.PUBLISHED,
        )

    def test_verified_member_can_create_and_edit_own_post_without_moderator_flags(self):
        self.client.force_authenticate(self.member)

        created = self.client.post(
            "/api/v1/posts/",
            {
                "title": "Member Post",
                "excerpt": "excerpt",
                "content": "content",
                "category_id": self.category.id,
                "tag_ids": [self.tag.id],
                "status": Post.Status.ARCHIVED,
                "is_featured": True,
            },
            format="json",
        )

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(slug=created.data["slug"])
        self.assertEqual(post.author, self.member)
        self.assertEqual(post.status, Post.Status.PUBLISHED)
        self.assertFalse(post.is_featured)

        own_update = self.client.patch(
            f"/api/v1/posts/{post.slug}/",
            {
                "title": "Edited Member Post",
                "status": Post.Status.ARCHIVED,
                "is_featured": True,
            },
            format="json",
        )
        other_update = self.client.patch(
            f"/api/v1/posts/{self.other_post.slug}/",
            {"title": "Unauthorized Edit"},
            format="json",
        )

        self.assertEqual(own_update.status_code, status.HTTP_200_OK)
        self.assertEqual(other_update.status_code, status.HTTP_403_FORBIDDEN)
        post.refresh_from_db()
        self.assertEqual(post.title, "Edited Member Post")
        self.assertEqual(post.status, Post.Status.PUBLISHED)
        self.assertFalse(post.is_featured)

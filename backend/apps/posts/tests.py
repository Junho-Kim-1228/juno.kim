from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User

from .models import Category, Post, Tag


class PostAPITests(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username="post-author",
            email="post-author@example.com",
            password="StrongTemporary!2026",
        )
        self.category = Category.objects.create(name="Django")
        self.tag = Tag.objects.create(name="API")
        self.published = Post.objects.create(
            author=self.author,
            category=self.category,
            title="Published Post",
            excerpt="excerpt",
            content="content",
            status=Post.Status.PUBLISHED,
        )
        self.published.tags.add(self.tag)
        self.draft = Post.objects.create(
            author=self.author,
            title="Draft Post",
            excerpt="excerpt",
            content="content",
        )

    def test_anonymous_user_only_sees_published_posts(self):
        response = self.client.get("/api/v1/posts/")
        slugs = {item["slug"] for item in response.data["results"]}

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.published.slug, slugs)
        self.assertNotIn(self.draft.slug, slugs)

    def test_non_staff_user_cannot_create_category(self):
        self.client.force_authenticate(self.author)
        response = self.client.post("/api/v1/categories/", {"name": "Security"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

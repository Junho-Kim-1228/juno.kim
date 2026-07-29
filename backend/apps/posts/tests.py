from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User

from .models import Category, Post, Tag


class PostAPITests(APITestCase):
    def setUp(self):
        self.member = User.objects.create_user(
            username="post_member",
            email="post-member@example.com",
            password="StrongTemporary!2026",
        )
        self.staff = User.objects.create_user(
            username="post_editor",
            email="post-staff@example.com",
            password="StrongTemporary!2026",
            is_staff=True,
        )
        self.category = Category.objects.create(name="Django")
        self.tag = Tag.objects.create(name="API")
        self.published = Post.objects.create(
            author=self.staff,
            category=self.category,
            title="Published Post",
            excerpt="excerpt",
            content="content",
            status=Post.Status.PUBLISHED,
        )
        self.published.tags.add(self.tag)
        self.draft = Post.objects.create(
            author=self.member,
            title="Draft Post",
            excerpt="excerpt",
            content="content",
        )
        self.archived = Post.objects.create(
            author=self.staff,
            title="Archived Post",
            excerpt="excerpt",
            content="content",
            status=Post.Status.ARCHIVED,
        )

    def test_anonymous_user_only_sees_published_posts(self):
        response = self.client.get("/api/v1/posts/")
        slugs = {item["slug"] for item in response.data["results"]}

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.published.slug, slugs)
        self.assertNotIn(self.draft.slug, slugs)
        self.assertNotIn(self.archived.slug, slugs)

    def test_anonymous_user_can_filter_published_posts_by_category(self):
        other_category = Category.objects.create(name="Daily")
        Post.objects.create(
            author=self.staff,
            category=other_category,
            title="Daily Post",
            excerpt="excerpt",
            content="content",
            status=Post.Status.PUBLISHED,
        )

        response = self.client.get("/api/v1/posts/", {"category": self.category.slug})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {item["slug"] for item in response.data["results"]},
            {self.published.slug},
        )

    def test_anonymous_user_can_filter_board_and_technical_posts(self):
        technical = Post.objects.create(
            author=self.staff,
            kind=Post.Kind.TECHNICAL,
            title="Technical Post",
            excerpt="excerpt",
            content="content",
            status=Post.Status.PUBLISHED,
        )

        board_response = self.client.get("/api/v1/posts/", {"kind": Post.Kind.BOARD})
        technical_response = self.client.get("/api/v1/posts/", {"kind": Post.Kind.TECHNICAL})

        self.assertIn(self.published.slug, {item["slug"] for item in board_response.data["results"]})
        self.assertNotIn(technical.slug, {item["slug"] for item in board_response.data["results"]})
        self.assertEqual(
            {item["slug"] for item in technical_response.data["results"]},
            {technical.slug},
        )

    def test_member_cannot_create_or_modify_post(self):
        self.client.force_authenticate(self.member)
        created = self.client.post(
            "/api/v1/posts/",
            {
                "title": "Unauthorized Post",
                "excerpt": "excerpt",
                "content": "content",
                "status": Post.Status.PUBLISHED,
                "is_featured": True,
            },
            format="json",
        )
        updated = self.client.patch(
            f"/api/v1/posts/{self.published.slug}/",
            {"status": Post.Status.ARCHIVED, "is_featured": True},
            format="json",
        )

        self.assertEqual(created.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(updated.status_code, status.HTTP_403_FORBIDDEN)
        self.published.refresh_from_db()
        self.assertEqual(self.published.status, Post.Status.PUBLISHED)
        self.assertFalse(self.published.is_featured)

    def test_member_cannot_see_own_draft(self):
        self.client.force_authenticate(self.member)

        listing = self.client.get("/api/v1/posts/")
        detail = self.client.get(f"/api/v1/posts/{self.draft.slug}/")

        slugs = {item["slug"] for item in listing.data["results"]}
        self.assertNotIn(self.draft.slug, slugs)
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_can_see_non_public_posts_and_create_and_modify(self):
        self.client.force_authenticate(self.staff)

        listing = self.client.get("/api/v1/posts/")
        slugs = {item["slug"] for item in listing.data["results"]}
        created = self.client.post(
            "/api/v1/posts/",
            {
                "title": "Staff Post",
                "excerpt": "excerpt",
                "content": "content",
                "category_id": self.category.id,
                "tag_ids": [self.tag.id],
                "kind": Post.Kind.TECHNICAL,
                "status": Post.Status.PUBLISHED,
                "is_featured": True,
            },
            format="json",
        )
        updated = self.client.patch(
            f"/api/v1/posts/{self.draft.slug}/",
            {"status": Post.Status.PUBLISHED},
            format="json",
        )

        self.assertIn(self.draft.slug, slugs)
        self.assertIn(self.archived.slug, slugs)
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        post = Post.objects.get(slug=created.data["slug"])
        self.assertEqual(post.author, self.staff)
        self.assertEqual(post.kind, Post.Kind.TECHNICAL)
        self.assertTrue(post.is_featured)

    def test_staff_can_remove_existing_cover_image(self):
        self.published.cover_image = "posts/2026/07/existing.jpg"
        self.published.save(update_fields=("cover_image",))
        self.client.force_authenticate(self.staff)

        response = self.client.patch(
            f"/api/v1/posts/{self.published.slug}/",
            {"remove_cover_image": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.published.refresh_from_db()
        self.assertFalse(self.published.cover_image)
        self.assertIsNone(response.data["cover_image"])

    def test_only_staff_can_change_categories_and_tags(self):
        self.client.force_authenticate(self.member)
        member_category = self.client.post(
            "/api/v1/categories/",
            {"name": "Security"},
            format="json",
        )
        member_tag = self.client.post(
            "/api/v1/tags/",
            {"name": "React"},
            format="json",
        )

        self.client.force_authenticate(self.staff)
        staff_category = self.client.post(
            "/api/v1/categories/",
            {"name": "Security"},
            format="json",
        )
        staff_tag = self.client.post(
            "/api/v1/tags/",
            {"name": "React"},
            format="json",
        )

        self.assertEqual(member_category.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(member_tag.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(staff_category.status_code, status.HTTP_201_CREATED)
        self.assertEqual(staff_tag.status_code, status.HTTP_201_CREATED)

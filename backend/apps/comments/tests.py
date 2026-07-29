from rest_framework import status
from rest_framework.test import APITestCase

from apps.posts.models import Post
from apps.users.models import User

from .models import Comment


class CommentAPITests(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username="article-author",
            email="article-author@example.com",
            password="StrongTemporary!2026",
        )
        self.commenter = User.objects.create_user(
            username="commenter",
            email="commenter@example.com",
            password="StrongTemporary!2026",
        )
        self.other = User.objects.create_user(
            username="comment-other",
            email="comment-other@example.com",
            password="StrongTemporary!2026",
        )
        for user in (self.author, self.commenter, self.other):
            user.email_verified = True
            user.save(update_fields=("email_verified",))
        self.post = Post.objects.create(
            author=self.author,
            title="Published Post",
            excerpt="excerpt",
            content="content",
            status=Post.Status.PUBLISHED,
        )
        self.draft = Post.objects.create(
            author=self.author,
            title="Draft Post",
            excerpt="excerpt",
            content="content",
        )

    def test_authenticated_user_can_comment_and_soft_delete_own_comment(self):
        self.client.force_authenticate(self.commenter)
        created = self.client.post(
            "/api/v1/comments/",
            {"post_slug": self.post.slug, "content": " useful comment "},
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        comment = Comment.objects.get(pk=created.data["id"])
        self.assertEqual(comment.content, "useful comment")

        deleted = self.client.delete(f"/api/v1/comments/{comment.id}/")
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        comment.refresh_from_db()
        self.assertFalse(comment.is_active)

    def test_non_author_cannot_comment_on_draft_or_edit_comment(self):
        self.client.force_authenticate(self.commenter)
        draft_comment = self.client.post(
            "/api/v1/comments/",
            {"post_slug": self.draft.slug, "content": "not allowed"},
            format="json",
        )
        self.assertEqual(draft_comment.status_code, status.HTTP_400_BAD_REQUEST)

        comment = Comment.objects.create(post=self.post, author=self.commenter, content="original")
        self.client.force_authenticate(self.other)
        updated = self.client.patch(
            f"/api/v1/comments/{comment.id}/",
            {"content": "unauthorized"},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_403_FORBIDDEN)

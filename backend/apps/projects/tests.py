from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User

from .models import Project


class ProjectAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="project-owner",
            email="project-owner@example.com",
            password="StrongTemporary!2026",
        )
        self.other = User.objects.create_user(
            username="project-other",
            email="project-other@example.com",
            password="StrongTemporary!2026",
        )
        self.published = Project.objects.create(
            owner=self.owner,
            title="Published Project",
            summary="summary",
            description="description",
            status=Project.Status.PUBLISHED,
        )
        self.draft = Project.objects.create(
            owner=self.owner,
            title="Draft Project",
            summary="summary",
            description="description",
        )

    def test_anonymous_user_only_sees_published_projects(self):
        response = self.client.get("/api/v1/projects/")
        slugs = {item["slug"] for item in response.data["results"]}

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.published.slug, slugs)
        self.assertNotIn(self.draft.slug, slugs)

    def test_owner_can_create_and_other_user_cannot_edit(self):
        self.client.force_authenticate(self.owner)
        created = self.client.post(
            "/api/v1/projects/",
            {
                "title": "New Project",
                "summary": "summary",
                "description": "description",
                "technologies": ["Django", "React"],
            },
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.get(slug=created.data["slug"]).owner, self.owner)

        self.client.force_authenticate(self.other)
        updated = self.client.patch(
            f"/api/v1/projects/{self.published.slug}/",
            {"summary": "unauthorized"},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_403_FORBIDDEN)

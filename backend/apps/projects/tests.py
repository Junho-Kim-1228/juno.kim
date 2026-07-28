from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User

from .models import Project


class ProjectAPITests(APITestCase):
    def setUp(self):
        self.member = User.objects.create_user(
            username="project-member",
            email="project-member@example.com",
            password="StrongTemporary!2026",
        )
        self.staff = User.objects.create_user(
            username="project-staff",
            email="project-staff@example.com",
            password="StrongTemporary!2026",
            is_staff=True,
        )
        self.published = Project.objects.create(
            owner=self.staff,
            title="Published Project",
            summary="summary",
            description="description",
            status=Project.Status.PUBLISHED,
        )
        self.draft = Project.objects.create(
            owner=self.member,
            title="Draft Project",
            summary="summary",
            description="description",
        )
        self.archived = Project.objects.create(
            owner=self.staff,
            title="Archived Project",
            summary="summary",
            description="description",
            status=Project.Status.ARCHIVED,
        )

    def test_anonymous_user_only_sees_published_projects(self):
        response = self.client.get("/api/v1/projects/")
        slugs = {item["slug"] for item in response.data["results"]}

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.published.slug, slugs)
        self.assertNotIn(self.draft.slug, slugs)
        self.assertNotIn(self.archived.slug, slugs)

    def test_member_cannot_create_or_modify_project(self):
        self.client.force_authenticate(self.member)
        created = self.client.post(
            "/api/v1/projects/",
            {
                "title": "Unauthorized Project",
                "summary": "summary",
                "description": "description",
                "status": Project.Status.PUBLISHED,
                "is_featured": True,
            },
            format="json",
        )
        updated = self.client.patch(
            f"/api/v1/projects/{self.published.slug}/",
            {"status": Project.Status.ARCHIVED, "is_featured": True},
            format="json",
        )

        self.assertEqual(created.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(updated.status_code, status.HTTP_403_FORBIDDEN)
        self.published.refresh_from_db()
        self.assertEqual(self.published.status, Project.Status.PUBLISHED)
        self.assertFalse(self.published.is_featured)

    def test_member_cannot_see_own_draft(self):
        self.client.force_authenticate(self.member)

        listing = self.client.get("/api/v1/projects/")
        detail = self.client.get(f"/api/v1/projects/{self.draft.slug}/")

        slugs = {item["slug"] for item in listing.data["results"]}
        self.assertNotIn(self.draft.slug, slugs)
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_can_see_non_public_projects_and_create_and_modify(self):
        self.client.force_authenticate(self.staff)

        listing = self.client.get("/api/v1/projects/")
        slugs = {item["slug"] for item in listing.data["results"]}
        created = self.client.post(
            "/api/v1/projects/",
            {
                "title": "Staff Project",
                "summary": "summary",
                "description": "description",
                "technologies": ["Django", "React"],
                "status": Project.Status.PUBLISHED,
                "is_featured": True,
            },
            format="json",
        )
        updated = self.client.patch(
            f"/api/v1/projects/{self.draft.slug}/",
            {"status": Project.Status.PUBLISHED},
            format="json",
        )

        self.assertIn(self.draft.slug, slugs)
        self.assertIn(self.archived.slug, slugs)
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        project = Project.objects.get(slug=created.data["slug"])
        self.assertEqual(project.owner, self.staff)
        self.assertTrue(project.is_featured)

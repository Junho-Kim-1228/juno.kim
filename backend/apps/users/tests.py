from django.core.cache import cache
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import User


class CustomUserModelTests(TestCase):
    def test_creating_user_also_creates_profile(self):
        user = User.objects.create_user(
            username="profile_user",
            email="profile@example.com",
            password="StrongTemporary!2026",
        )

        self.assertEqual(user.profile.user_id, user.id)
        self.assertEqual(str(user), "profile_user")


class AuthenticationAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient(enforce_csrf_checks=True)
        response = self.client.get("/api/v1/auth/csrf/")
        self.csrf_token = response.data["csrfToken"]
        self.csrf_headers = {"HTTP_X_CSRFTOKEN": self.csrf_token}

    def test_registration_login_refresh_and_logout(self):
        credentials = {
            "username": "auth_user",
            "email": "auth@example.com",
            "password": "StrongTemporary!2026",
        }
        register = self.client.post(
            "/api/v1/auth/register/",
            credentials,
            format="json",
            **self.csrf_headers,
        )
        self.assertEqual(register.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", register.data)
        registered_user = User.objects.get(username=credentials["username"])
        self.assertFalse(registered_user.is_staff)
        self.assertFalse(registered_user.is_superuser)

        login = self.client.post(
            "/api/v1/auth/login/",
            {"username": credentials["username"], "password": credentials["password"]},
            format="json",
            **self.csrf_headers,
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertIn("access", login.data)
        self.assertNotIn("refresh", login.data)
        self.assertIn("refresh_token", self.client.cookies)
        self.assertTrue(self.client.cookies["refresh_token"]["httponly"])

        refresh = self.client.post(
            "/api/v1/auth/refresh/",
            {},
            format="json",
            **self.csrf_headers,
        )
        self.assertEqual(refresh.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh.data)
        self.assertNotIn("refresh", refresh.data)

        logout = self.client.post(
            "/api/v1/auth/logout/",
            {},
            format="json",
            **self.csrf_headers,
        )
        self.assertEqual(logout.status_code, status.HTTP_204_NO_CONTENT)

    def test_me_requires_authentication(self):
        response = self.client.get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_username_and_email_cannot_be_changed_after_registration(self):
        user = User.objects.create_user(
            username="fixed_identity",
            email="fixed-identity@example.com",
            password="StrongTemporary!2026",
        )
        user.email_verified = True
        user.save(update_fields=("email_verified",))
        self.client.force_authenticate(user)

        username_response = self.client.patch(
            "/api/v1/auth/me/",
            {"username": "changed_identity"},
            format="json",
            **self.csrf_headers,
        )
        email_response = self.client.patch(
            "/api/v1/auth/me/",
            {"email": "changed-identity@example.com"},
            format="json",
            **self.csrf_headers,
        )

        user.refresh_from_db()
        self.assertEqual(username_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(username_response.data["username"], ["아이디는 가입 후 변경할 수 없습니다."])
        self.assertEqual(email_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(email_response.data["email"], ["이메일은 가입 후 변경할 수 없습니다."])
        self.assertEqual(user.username, "fixed_identity")
        self.assertEqual(user.email, "fixed-identity@example.com")
        self.assertTrue(user.email_verified)

    def test_registration_cannot_create_staff_or_superuser(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "username": "malicious_register",
                "email": "malicious@example.com",
                "password": "StrongTemporary!2026",
                "is_staff": True,
                "is_superuser": True,
            },
            format="json",
            **self.csrf_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="malicious_register")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_registration_rejects_duplicate_email(self):
        User.objects.create_user(
            username="existing_user",
            email="duplicate@example.com",
            password="StrongTemporary!2026",
        )

        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "username": "duplicate_email_user",
                "email": "duplicate@example.com",
                "password": "StrongTemporary!2026",
            },
            format="json",
            **self.csrf_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

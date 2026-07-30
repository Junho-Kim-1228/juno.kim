from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User

from .models import ReactionBestScore, ReactionChallenge


class ReactionGameAPITests(APITestCase):
    def setUp(self):
        self.member = User.objects.create_user(
            username="reaction_member",
            email="reaction@example.com",
            password="StrongTemporary!2026",
            email_verified=True,
        )
        self.client.force_authenticate(self.member)

    def create_ready_challenge(self, elapsed_ms):
        challenge = ReactionChallenge.objects.create(
            user=self.member,
            ready_at=timezone.now() - timedelta(milliseconds=elapsed_ms),
            expires_at=timezone.now() + timedelta(seconds=5),
        )
        return self.client.post(reverse("reaction-submit"), {"challenge_id": str(challenge.pk)}, format="json")

    def test_unverified_members_cannot_start_a_ranked_game(self):
        unverified = User.objects.create_user(
            username="unverified_player",
            email="unverified@example.com",
            password="StrongTemporary!2026",
        )
        self.client.force_authenticate(unverified)

        response = self.client.post(reverse("reaction-challenge"), format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_challenge_uses_a_short_relative_wait_time(self):
        response = self.client.post(reverse("reaction-challenge"), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("challenge_id", response.data)
        self.assertGreaterEqual(response.data["wait_ms"], 1000)
        self.assertLessEqual(response.data["wait_ms"], 10000)
        self.assertNotIn("ready_at", response.data)

    def test_member_keeps_only_their_fastest_score(self):
        first = self.create_ready_challenge(240)
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertTrue(first.data["is_personal_best"])

        slower = self.create_ready_challenge(640)
        self.assertEqual(slower.status_code, status.HTTP_200_OK)
        self.assertFalse(slower.data["is_personal_best"])

        score = ReactionBestScore.objects.get(user=self.member)
        self.assertEqual(ReactionBestScore.objects.filter(user=self.member).count(), 1)
        self.assertLess(score.reaction_ms, 400)
        self.assertGreaterEqual(score.reaction_ms, 100)

    def test_early_or_reused_challenges_are_rejected(self):
        challenge = ReactionChallenge.objects.create(
            user=self.member,
            ready_at=timezone.now() + timedelta(seconds=2),
            expires_at=timezone.now() + timedelta(seconds=8),
        )
        early = self.client.post(reverse("reaction-submit"), {"challenge_id": str(challenge.pk)}, format="json")
        self.assertEqual(early.status_code, status.HTTP_400_BAD_REQUEST)

        challenge.ready_at = timezone.now() - timedelta(milliseconds=220)
        challenge.save(update_fields=("ready_at",))
        accepted = self.client.post(reverse("reaction-submit"), {"challenge_id": str(challenge.pk)}, format="json")
        self.assertEqual(accepted.status_code, status.HTTP_200_OK)

        reused = self.client.post(reverse("reaction-submit"), {"challenge_id": str(challenge.pk)}, format="json")
        self.assertEqual(reused.status_code, status.HTTP_400_BAD_REQUEST)

    def test_server_accepts_a_normal_delayed_click_within_ten_seconds(self):
        response = self.create_ready_challenge(8000)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data["reaction_ms"], 7000)

    def test_public_leaderboard_and_authenticated_personal_rank(self):
        self.create_ready_challenge(230)
        self.client.force_authenticate(user=None)

        public = self.client.get(reverse("reaction-leaderboard"))
        self.assertEqual(public.status_code, status.HTTP_200_OK)
        self.assertEqual(len(public.data["results"]), 1)
        self.assertNotIn("my_score", public.data)

        self.client.force_authenticate(self.member)
        member = self.client.get(reverse("reaction-leaderboard"))
        self.assertEqual(member.data["my_score"]["rank"], 1)
        self.assertEqual(member.data["my_score"]["user"]["username"], self.member.username)

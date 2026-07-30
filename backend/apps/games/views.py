import random
from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.permissions import IsVerifiedUserOrReadOnly
from apps.users.security import AccountRateThrottle, IPRateThrottle

from .models import ReactionBestScore, ReactionChallenge
from .serializers import ReactionSubmissionSerializer


MIN_REACTION_MS = 100
MAX_REACTION_MS = 10000
CHALLENGE_TTL = timedelta(seconds=12)


class ReactionChallengeThrottle(AccountRateThrottle):
    scope = "reaction_challenge"


class ReactionSubmissionThrottle(AccountRateThrottle):
    scope = "reaction_submission"


class ReactionGameIPThrottle(IPRateThrottle):
    scope = "reaction_game_ip"


def serialize_score(score, rank):
    profile = getattr(score.user, "profile", None)
    display_name = profile.display_name.strip() if profile and profile.display_name else score.user.username
    return {
        "rank": rank,
        "reaction_ms": score.reaction_ms,
        "achieved_at": score.achieved_at,
        "user": {
            "username": score.user.username,
            "display_name": display_name,
            "is_staff": score.user.is_staff,
        },
    }


def score_rank(score):
    return (
        ReactionBestScore.objects.filter(
            Q(reaction_ms__lt=score.reaction_ms)
            | Q(reaction_ms=score.reaction_ms, achieved_at__lt=score.achieved_at)
            | Q(reaction_ms=score.reaction_ms, achieved_at=score.achieved_at, pk__lt=score.pk)
        ).count()
        + 1
    )


class ReactionLeaderboardView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        scores = list(
            ReactionBestScore.objects.select_related("user", "user__profile")[:20]
        )
        payload = {"results": [serialize_score(score, index) for index, score in enumerate(scores, start=1)]}

        if request.user.is_authenticated:
            own_score = (
                ReactionBestScore.objects.select_related("user", "user__profile")
                .filter(user=request.user)
                .first()
            )
            payload["my_score"] = serialize_score(own_score, score_rank(own_score)) if own_score else None
        return Response(payload)


@method_decorator(csrf_protect, name="dispatch")
class ReactionChallengeView(APIView):
    permission_classes = (IsVerifiedUserOrReadOnly,)
    throttle_classes = (ReactionChallengeThrottle, ReactionGameIPThrottle)

    def post(self, request):
        now = timezone.now()
        ready_at = now + timedelta(milliseconds=random.SystemRandom().randint(1500, 3500))
        challenge = ReactionChallenge.objects.create(
            user=request.user,
            ready_at=ready_at,
            expires_at=ready_at + CHALLENGE_TTL,
        )
        return Response(
            {"challenge_id": challenge.pk, "ready_at": challenge.ready_at},
            status=status.HTTP_201_CREATED,
        )


@method_decorator(csrf_protect, name="dispatch")
class ReactionSubmissionView(APIView):
    permission_classes = (IsVerifiedUserOrReadOnly,)
    throttle_classes = (ReactionSubmissionThrottle, ReactionGameIPThrottle)

    def post(self, request):
        serializer = ReactionSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        now = timezone.now()

        with transaction.atomic():
            challenge = (
                ReactionChallenge.objects.select_for_update()
                .filter(pk=serializer.validated_data["challenge_id"], user=request.user)
                .first()
            )
            if not challenge or challenge.used_at is not None:
                return Response({"detail": "유효하지 않거나 이미 사용한 게임입니다."}, status=status.HTTP_400_BAD_REQUEST)
            if now < challenge.ready_at:
                return Response({"detail": "아직 시작되지 않았습니다. 다시 시도해 주세요."}, status=status.HTTP_400_BAD_REQUEST)
            if now > challenge.expires_at:
                return Response({"detail": "게임 시간이 만료됐습니다. 다시 시작해 주세요."}, status=status.HTTP_400_BAD_REQUEST)

            reaction_ms = round((now - challenge.ready_at).total_seconds() * 1000)
            if not MIN_REACTION_MS <= reaction_ms <= MAX_REACTION_MS:
                return Response({"detail": "너무 늦었어요. 10초 안에 눌러 주세요."}, status=status.HTTP_400_BAD_REQUEST)

            challenge.used_at = now
            challenge.save(update_fields=("used_at",))

            score, created = ReactionBestScore.objects.select_for_update().get_or_create(
                user=request.user,
                defaults={"reaction_ms": reaction_ms},
            )
            is_personal_best = created or reaction_ms < score.reaction_ms
            if is_personal_best and not created:
                score.reaction_ms = reaction_ms
                score.save(update_fields=("reaction_ms", "achieved_at"))

        score.refresh_from_db()
        return Response(
            {
                "reaction_ms": reaction_ms,
                "is_personal_best": is_personal_best,
                "my_score": serialize_score(score, score_rank(score)),
            }
        )

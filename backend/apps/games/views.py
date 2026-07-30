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

from .models import AimBestScore, AimChallenge, ReactionBestScore, ReactionChallenge
from .serializers import ReactionSubmissionSerializer


MIN_REACTION_MS = 100
MAX_REACTION_MS = 10000
CHALLENGE_TTL = timedelta(seconds=12)
MIN_READY_DELAY_MS = 1000
MAX_READY_DELAY_MS = 10000


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
        wait_ms = random.SystemRandom().randint(MIN_READY_DELAY_MS, MAX_READY_DELAY_MS)
        ready_at = now + timedelta(milliseconds=wait_ms)
        challenge = ReactionChallenge.objects.create(
            user=request.user,
            ready_at=ready_at,
            expires_at=ready_at + CHALLENGE_TTL,
        )
        return Response(
            {"challenge_id": challenge.pk, "wait_ms": wait_ms},
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


def aim_payload(score, rank):
    profile = getattr(score.user, "profile", None)
    return {"rank": rank, "score_ms": score.score_ms, "user": {"username": score.user.username, "display_name": profile.display_name.strip() if profile and profile.display_name else score.user.username}}


class AimLeaderboardView(APIView):
    permission_classes = (permissions.AllowAny,)
    def get(self, request):
        scores = list(AimBestScore.objects.select_related("user", "user__profile")[:20])
        data = {"results": [aim_payload(score, index) for index, score in enumerate(scores, 1)]}
        if request.user.is_authenticated:
            score = AimBestScore.objects.select_related("user", "user__profile").filter(user=request.user).first()
            data["my_score"] = aim_payload(score, AimBestScore.objects.filter(Q(score_ms__lt=score.score_ms) | Q(score_ms=score.score_ms, achieved_at__lt=score.achieved_at)).count() + 1) if score else None
        return Response(data)


@method_decorator(csrf_protect, name="dispatch")
class AimChallengeView(APIView):
    permission_classes = (IsVerifiedUserOrReadOnly,)
    throttle_classes = (ReactionChallengeThrottle, ReactionGameIPThrottle)
    def post(self, request):
        challenge = AimChallenge.objects.create(user=request.user, expires_at=timezone.now() + timedelta(minutes=2))
        return Response({"challenge_id": challenge.pk}, status=status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name="dispatch")
class AimSubmissionView(APIView):
    permission_classes = (IsVerifiedUserOrReadOnly,)
    throttle_classes = (ReactionSubmissionThrottle, ReactionGameIPThrottle)
    def post(self, request):
        serializer = ReactionSubmissionSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        score_ms = request.data.get("score_ms")
        if not isinstance(score_ms, int) or not 500 <= score_ms <= 120000:
            return Response({"detail": "유효하지 않은 기록입니다."}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            challenge = AimChallenge.objects.select_for_update().filter(pk=serializer.validated_data["challenge_id"], user=request.user, used_at__isnull=True).first()
            if not challenge or challenge.expires_at < timezone.now(): return Response({"detail": "게임 시간이 만료됐습니다. 다시 시작해 주세요."}, status=status.HTTP_400_BAD_REQUEST)
            challenge.used_at = timezone.now(); challenge.save(update_fields=("used_at",))
            best, created = AimBestScore.objects.select_for_update().get_or_create(user=request.user, defaults={"score_ms": score_ms})
            improved = created or score_ms < best.score_ms
            if improved and not created: best.score_ms = score_ms; best.save(update_fields=("score_ms", "achieved_at"))
        best.refresh_from_db(); rank = AimBestScore.objects.filter(Q(score_ms__lt=best.score_ms) | Q(score_ms=best.score_ms, achieved_at__lt=best.achieved_at)).count() + 1
        return Response({"is_personal_best": improved, "my_score": aim_payload(best, rank)})

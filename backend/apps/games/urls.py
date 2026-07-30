from django.urls import path

from .views import AimChallengeView, AimLeaderboardView, AimSubmissionView, ReactionChallengeView, ReactionLeaderboardView, ReactionSubmissionView


urlpatterns = [
    path("games/aim/leaderboard/", AimLeaderboardView.as_view(), name="aim-leaderboard"),
    path("games/aim/challenge/", AimChallengeView.as_view(), name="aim-challenge"),
    path("games/aim/submit/", AimSubmissionView.as_view(), name="aim-submit"),
    path("games/reaction/leaderboard/", ReactionLeaderboardView.as_view(), name="reaction-leaderboard"),
    path("games/reaction/challenge/", ReactionChallengeView.as_view(), name="reaction-challenge"),
    path("games/reaction/submit/", ReactionSubmissionView.as_view(), name="reaction-submit"),
]

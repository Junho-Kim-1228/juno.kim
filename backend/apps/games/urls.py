from django.urls import path

from .views import ReactionChallengeView, ReactionLeaderboardView, ReactionSubmissionView


urlpatterns = [
    path("games/reaction/leaderboard/", ReactionLeaderboardView.as_view(), name="reaction-leaderboard"),
    path("games/reaction/challenge/", ReactionChallengeView.as_view(), name="reaction-challenge"),
    path("games/reaction/submit/", ReactionSubmissionView.as_view(), name="reaction-submit"),
]

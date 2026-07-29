from django.urls import path

from .views import GuestbookListCreateView, GuestbookReplyView, TodayStatusView


urlpatterns = [
    path("guestbook/", GuestbookListCreateView.as_view(), name="guestbook-list-create"),
    path("guestbook/<int:pk>/reply/", GuestbookReplyView.as_view(), name="guestbook-reply"),
    path("today-status/", TodayStatusView.as_view(), name="today-status"),
]

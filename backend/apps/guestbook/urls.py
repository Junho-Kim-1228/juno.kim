from django.urls import path

from .views import GuestbookListCreateView


urlpatterns = [
    path("guestbook/", GuestbookListCreateView.as_view(), name="guestbook-list-create"),
]

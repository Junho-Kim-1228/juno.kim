from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.throttling import ScopedRateThrottle

from .models import GuestbookEntry
from .serializers import GuestbookEntrySerializer


@method_decorator(csrf_protect, name="dispatch")
class GuestbookListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = GuestbookEntrySerializer
    queryset = GuestbookEntry.objects.filter(is_visible=True)

    def get_throttles(self):
        if self.request.method == "POST":
            self.throttle_scope = "guestbook"
            return [ScopedRateThrottle()]
        return []

    def perform_create(self, serializer):
        profile = getattr(self.request.user, "profile", None)
        display_name = profile.display_name.strip() if profile else ""
        serializer.save(name=display_name or self.request.user.username)

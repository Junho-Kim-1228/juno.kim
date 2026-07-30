from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from rest_framework import generics, permissions
from rest_framework.response import Response
from apps.permissions import IsStaffOrReadOnly, IsVerifiedUserOrReadOnly
from apps.users.security import GuestbookAccountThrottle, GuestbookIPThrottle

from .models import GuestbookEntry, TodayStatus
from .serializers import GuestbookEntrySerializer, GuestbookReplyUpdateSerializer, TodayStatusSerializer


@method_decorator(csrf_protect, name="dispatch")
class GuestbookListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsVerifiedUserOrReadOnly,)
    serializer_class = GuestbookEntrySerializer
    queryset = GuestbookEntry.objects.filter(is_visible=True).select_related(
        "author",
        "author__profile",
        "staff_replied_by",
        "staff_replied_by__profile",
    )

    def get_throttles(self):
        if self.request.method == "POST":
            return [GuestbookAccountThrottle(), GuestbookIPThrottle()]
        return []

    def perform_create(self, serializer):
        profile = getattr(self.request.user, "profile", None)
        display_name = profile.display_name.strip() if profile else ""
        serializer.save(
            author=self.request.user,
            name=display_name or self.request.user.username,
        )


@method_decorator(csrf_protect, name="dispatch")
class GuestbookReplyView(generics.UpdateAPIView):
    permission_classes = (IsStaffOrReadOnly,)
    serializer_class = GuestbookReplyUpdateSerializer
    http_method_names = ("patch", "options")
    queryset = GuestbookEntry.objects.select_related(
        "author",
        "author__profile",
        "staff_replied_by",
        "staff_replied_by__profile",
    )

    def perform_update(self, serializer):
        reply = serializer.validated_data["staff_reply"]
        serializer.save(
            staff_replied_by=self.request.user if reply else None,
            staff_replied_at=timezone.now() if reply else None,
        )


class TodayStatusView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = TodayStatusSerializer

    def get(self, request, *args, **kwargs):
        today = TodayStatus.objects.first()
        if today is None:
            return Response(None)
        return Response(self.get_serializer(today).data)

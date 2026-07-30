from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response

from apps.permissions import IsOwnerOrStaffOrReadOnly, IsVerifiedUserOrReadOnly
from apps.users.security import CommentAccountHourlyThrottle, CommentAccountThrottle, CommentIPThrottle

from .models import Comment
from .serializers import CommentSerializer


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (IsVerifiedUserOrReadOnly, IsOwnerOrStaffOrReadOnly)

    def get_throttles(self):
        if self.action == "create":
            if self.request.user.is_authenticated and self.request.user.is_staff:
                return []
            return [CommentAccountThrottle(), CommentIPThrottle(), CommentAccountHourlyThrottle()]
        return []

    def get_queryset(self):
        queryset = Comment.objects.select_related(
            "post",
            "post__author",
            "author",
            "author__profile",
            "parent",
        )
        user = self.request.user
        if user.is_authenticated and user.is_staff:
            pass
        elif user.is_authenticated:
            queryset = queryset.filter(
                Q(
                    is_active=True,
                    author__is_active=True,
                    post__status="published",
                    post__author__is_active=True,
                )
                | Q(author=user)
                | Q(post__author=user)
            )
        else:
            queryset = queryset.filter(
                is_active=True,
                author__is_active=True,
                post__status="published",
                post__author__is_active=True,
            )
        if self.action == "list":
            queryset = queryset.filter(parent__isnull=True)
        post_slug = self.request.query_params.get("post")
        if post_slug:
            queryset = queryset.filter(post__slug=post_slug)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        comment.is_active = False
        comment.save(update_fields=("is_active", "updated_at"))
        return Response(status=status.HTTP_204_NO_CONTENT)

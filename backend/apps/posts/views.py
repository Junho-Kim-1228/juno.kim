from django.db.models import Count, Q
from rest_framework import permissions, viewsets

from apps.permissions import IsOwnerOrStaffOrReadOnly, IsStaffOrReadOnly

from .models import Category, Post, Tag
from .serializers import CategorySerializer, PostSerializer, TagSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsStaffOrReadOnly,)
    lookup_field = "slug"


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsStaffOrReadOnly,)
    lookup_field = "slug"


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrStaffOrReadOnly)
    lookup_field = "slug"

    def get_queryset(self):
        queryset = (
            Post.objects.select_related("author", "author__profile", "category")
            .prefetch_related("tags")
            .annotate(comment_count=Count("comments", filter=Q(comments__is_active=True)))
            .order_by("-is_featured", "-published_at", "-created_at")
        )
        user = self.request.user
        if user.is_authenticated and user.is_staff:
            return queryset
        if user.is_authenticated:
            return queryset.filter(Q(status=Post.Status.PUBLISHED) | Q(author=user))
        return queryset.filter(status=Post.Status.PUBLISHED)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

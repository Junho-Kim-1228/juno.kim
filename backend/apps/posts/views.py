from django.db.models import Count, Q
from rest_framework import viewsets

from apps.permissions import IsOwnerOrStaffOrReadOnly, IsStaffOrReadOnly, IsVerifiedUserOrStaffOrReadOnly

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
    permission_classes = (IsVerifiedUserOrStaffOrReadOnly, IsOwnerOrStaffOrReadOnly)
    lookup_field = "slug"

    def get_queryset(self):
        queryset = (
            Post.objects.select_related("author", "author__profile", "category")
            .prefetch_related("tags")
            .annotate(comment_count=Count("comments", filter=Q(comments__is_active=True)))
            .order_by("-is_featured", "-published_at", "-created_at")
        )
        user = self.request.user
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category__slug=category)
        if user.is_authenticated and user.is_staff:
            return queryset
        return queryset.filter(status=Post.Status.PUBLISHED)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

from django.db.models import Count, Q
from rest_framework import generics, parsers, viewsets
from rest_framework.throttling import UserRateThrottle

from apps.permissions import IsOwnerOrStaffOrReadOnly, IsStaffOrReadOnly, IsVerifiedUserOrStaffOrReadOnly
from apps.users.security import ContentImageAccountHourlyThrottle, PostAccountHourlyThrottle

from .models import Category, Post, Tag
from .serializers import CategorySerializer, ContentImageSerializer, PostSerializer, TagSerializer


class ContentImageUploadThrottle(UserRateThrottle):
    scope = "content_image_upload"


class ContentImageUploadView(generics.CreateAPIView):
    serializer_class = ContentImageSerializer
    permission_classes = (IsVerifiedUserOrStaffOrReadOnly,)
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)
    throttle_classes = (ContentImageUploadThrottle,)

    def get_throttles(self):
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return []
        return [ContentImageUploadThrottle(), ContentImageAccountHourlyThrottle()]

    def perform_create(self, serializer):
        serializer.save(uploader=self.request.user)


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

    def get_throttles(self):
        if self.action == "create" and not (
            self.request.user.is_authenticated and self.request.user.is_staff
        ):
            return [PostAccountHourlyThrottle()]
        return []

    def get_queryset(self):
        queryset = (
            Post.objects.select_related("author", "author__profile", "category")
            .prefetch_related("tags")
            .annotate(comment_count=Count("comments", filter=Q(comments__is_active=True)))
            .order_by("-is_featured", "-published_at", "-created_at")
        )
        user = self.request.user
        category = self.request.query_params.get("category")
        kind = self.request.query_params.get("kind")
        scope = self.request.query_params.get("scope")
        public_only = self.request.query_params.get("public_only") == "true"
        if category:
            queryset = queryset.filter(category__slug=category)
        if kind in Post.Kind.values:
            queryset = queryset.filter(kind=kind)
        elif self.action == "list" and scope != "drafts":
            queryset = queryset.filter(kind=Post.Kind.BOARD)
        if self.action == "list" and scope == "drafts":
            if user.is_authenticated:
                return queryset.filter(author=user, status=Post.Status.DRAFT)
            return queryset.none()
        if public_only:
            return queryset.filter(status=Post.Status.PUBLISHED, author__is_active=True)
        if user.is_authenticated and user.is_staff:
            if self.action == "list":
                return queryset.exclude(status=Post.Status.DRAFT)
            return queryset
        if user.is_authenticated:
            if self.action == "list":
                return queryset.filter(
                    Q(status=Post.Status.PUBLISHED, author__is_active=True)
                    | Q(author=user, status=Post.Status.PRIVATE)
                )
            return queryset.filter(
                Q(status=Post.Status.PUBLISHED, author__is_active=True) | Q(author=user)
            )
        return queryset.filter(status=Post.Status.PUBLISHED, author__is_active=True)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

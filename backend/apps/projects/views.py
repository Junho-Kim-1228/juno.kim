from django.db.models import Q
from rest_framework import permissions, viewsets

from apps.permissions import IsOwnerOrStaffOrReadOnly

from .models import Project
from .serializers import ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrStaffOrReadOnly)
    lookup_field = "slug"

    def get_queryset(self):
        queryset = Project.objects.select_related("owner", "owner__profile")
        user = self.request.user
        if user.is_authenticated and user.is_staff:
            return queryset
        if user.is_authenticated:
            return queryset.filter(Q(status=Project.Status.PUBLISHED) | Q(owner=user))
        return queryset.filter(status=Project.Status.PUBLISHED)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

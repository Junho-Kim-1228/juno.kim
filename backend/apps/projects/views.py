from rest_framework import viewsets

from apps.permissions import IsStaffOrReadOnly

from .models import Project
from .serializers import ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = (IsStaffOrReadOnly,)
    lookup_field = "slug"

    def get_queryset(self):
        queryset = Project.objects.select_related("owner", "owner__profile")
        user = self.request.user
        if user.is_authenticated and user.is_staff:
            return queryset
        return queryset.filter(status=Project.Status.PUBLISHED)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

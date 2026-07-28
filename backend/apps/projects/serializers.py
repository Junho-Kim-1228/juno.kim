from rest_framework import serializers

from apps.users.serializers import UserSummarySerializer

from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    owner = UserSummarySerializer(read_only=True)

    class Meta:
        model = Project
        fields = (
            "id",
            "owner",
            "title",
            "slug",
            "summary",
            "description",
            "technologies",
            "repository_url",
            "live_url",
            "thumbnail",
            "status",
            "is_featured",
            "started_on",
            "ended_on",
            "published_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "owner", "slug", "published_at", "created_at", "updated_at")

    def validate_technologies(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("기술 스택은 문자열 목록이어야 합니다.")
        return [item.strip() for item in value if item.strip()]

    def validate(self, attrs):
        started_on = attrs.get("started_on", getattr(self.instance, "started_on", None))
        ended_on = attrs.get("ended_on", getattr(self.instance, "ended_on", None))
        if started_on and ended_on and ended_on < started_on:
            raise serializers.ValidationError({"ended_on": "종료일은 시작일보다 빠를 수 없습니다."})
        return attrs

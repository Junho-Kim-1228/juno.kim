from rest_framework import serializers

from apps.users.serializers import UserSummarySerializer

from .models import GuestbookEntry


class GuestbookEntrySerializer(serializers.ModelSerializer):
    author = UserSummarySerializer(read_only=True)

    class Meta:
        model = GuestbookEntry
        fields = ("id", "name", "author", "message", "created_at")
        read_only_fields = ("id", "name", "author", "created_at")

    def validate_message(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("메시지를 입력해 주세요.")
        return value

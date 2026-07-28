from rest_framework import serializers

from .models import GuestbookEntry


class GuestbookEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestbookEntry
        fields = ("id", "name", "message", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("이름은 2자 이상 입력해 주세요.")
        return value

    def validate_message(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("메시지를 입력해 주세요.")
        return value

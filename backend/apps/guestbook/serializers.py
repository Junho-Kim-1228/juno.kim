from rest_framework import serializers

from apps.users.serializers import UserSummarySerializer

from .models import GuestbookEntry, TodayStatus


class GuestbookEntrySerializer(serializers.ModelSerializer):
    author = UserSummarySerializer(read_only=True)
    reply = serializers.SerializerMethodField()

    class Meta:
        model = GuestbookEntry
        fields = ("id", "name", "author", "message", "reply", "created_at")
        read_only_fields = ("id", "name", "author", "reply", "created_at")

    def get_reply(self, obj):
        if not obj.staff_reply:
            return None
        author = UserSummarySerializer(obj.staff_replied_by, context=self.context).data if obj.staff_replied_by else None
        return {
            "message": obj.staff_reply,
            "author": author,
            "created_at": obj.staff_replied_at,
        }

    def validate_message(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("메시지를 입력해 주세요.")
        return value


class GuestbookReplyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestbookEntry
        fields = ("staff_reply",)

    def validate_staff_reply(self, value):
        return value.strip()

    def to_representation(self, instance):
        return GuestbookEntrySerializer(instance, context=self.context).data


class TodayStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TodayStatus
        fields = ("id", "mood", "doing", "listening", "updated_at")
        read_only_fields = fields

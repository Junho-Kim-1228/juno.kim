from rest_framework import serializers


class ReactionSubmissionSerializer(serializers.Serializer):
    challenge_id = serializers.UUIDField()


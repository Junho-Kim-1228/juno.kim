from django.contrib.auth import password_validation
from django.db.models.functions import Lower
from rest_framework import serializers

from .identity import validate_display_name, validate_username
from .models import Profile, User


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            "display_name",
            "bio",
            "avatar",
            "website_url",
            "github_url",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def validate_display_name(self, value):
        try:
            return validate_display_name(value)
        except Exception as error:
            raise serializers.ValidationError(error.messages[0]) from error


class UserSummarySerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(source="profile.display_name", read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "display_name", "is_staff")


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "email_verified",
            "profile",
        )
        read_only_fields = ("id", "is_staff", "email_verified", "profile")

    def validate_email(self, value):
        normalized = value.strip().lower()
        queryset = User.objects.annotate(email_normalized=Lower("email")).filter(email_normalized=normalized)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return normalized

    def validate_username(self, value):
        try:
            return validate_username(value)
        except Exception as error:
            raise serializers.ValidationError(error.messages[0]) from error

    def update(self, instance, validated_data):
        email_changed = "email" in validated_data and validated_data["email"] != instance.email
        if email_changed:
            validated_data["email_verified"] = False
            validated_data["email_verified_at"] = None
        return super().update(instance, validated_data)


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = User
        fields = ("username", "email", "password", "first_name", "last_name")

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def validate_email(self, value):
        normalized = value.strip().lower()
        if User.objects.annotate(email_normalized=Lower("email")).filter(email_normalized=normalized).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return normalized

    def validate_username(self, value):
        try:
            return validate_username(value)
        except Exception as error:
            raise serializers.ValidationError(error.messages[0]) from error

    def create(self, validated_data):
        validated_data["is_staff"] = False
        validated_data["is_superuser"] = False
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password_confirm = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("현재 비밀번호가 올바르지 않습니다.")
        return value

    def validate(self, attrs):
        new_password = attrs["new_password"]
        if new_password != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "새 비밀번호가 일치하지 않습니다."})
        if self.context["request"].user.check_password(new_password):
            raise serializers.ValidationError({"new_password": "현재 비밀번호와 다른 비밀번호를 입력해 주세요."})
        password_validation.validate_password(new_password, self.context["request"].user)
        return attrs

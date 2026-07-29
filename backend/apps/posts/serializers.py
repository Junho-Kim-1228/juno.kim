from django.db import transaction
from rest_framework import serializers

from apps.users.serializers import UserSummarySerializer

from .models import Category, Post, Tag


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "ordering")
        read_only_fields = ("id", "slug")


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug")
        read_only_fields = ("id", "slug")


class PostSerializer(serializers.ModelSerializer):
    author = UserSummarySerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=Category.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        source="tags",
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        required=False,
    )
    comment_count = serializers.IntegerField(read_only=True)
    remove_cover_image = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "category",
            "category_id",
            "tags",
            "tag_ids",
            "kind",
            "title",
            "slug",
            "excerpt",
            "content",
            "cover_image",
            "remove_cover_image",
            "status",
            "is_featured",
            "comment_count",
            "published_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "author",
            "slug",
            "comment_count",
            "published_at",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        if attrs.get("remove_cover_image") and attrs.get("cover_image"):
            raise serializers.ValidationError(
                {"cover_image": "새 이미지를 올리면서 기존 이미지를 제거할 수 없습니다."}
            )

        request = self.context.get("request")
        if request and request.user.is_authenticated and not request.user.is_staff:
            attrs["kind"] = Post.Kind.BOARD
            attrs.pop("is_featured", None)
            if self.instance is None:
                attrs["is_featured"] = False
        return attrs

    def create(self, validated_data):
        validated_data.pop("remove_cover_image", None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        remove_cover_image = validated_data.pop("remove_cover_image", False)
        old_image_name = instance.cover_image.name if remove_cover_image and instance.cover_image else ""
        old_image_storage = instance.cover_image.storage if old_image_name else None
        if remove_cover_image:
            validated_data["cover_image"] = None

        instance = super().update(instance, validated_data)
        if old_image_name:
            transaction.on_commit(lambda: old_image_storage.delete(old_image_name))
        return instance

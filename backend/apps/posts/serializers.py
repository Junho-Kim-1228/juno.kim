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

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "category",
            "category_id",
            "tags",
            "tag_ids",
            "title",
            "slug",
            "excerpt",
            "content",
            "cover_image",
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

from rest_framework import serializers

from apps.posts.models import Post
from apps.users.serializers import UserSummarySerializer

from .models import Comment


class ReplySerializer(serializers.ModelSerializer):
    author = UserSummarySerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "author", "content", "created_at", "updated_at")


class CommentSerializer(serializers.ModelSerializer):
    author = UserSummarySerializer(read_only=True)
    post_slug = serializers.SlugRelatedField(
        source="post",
        slug_field="slug",
        queryset=Post.objects.all(),
        write_only=True,
    )
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            "id",
            "post_slug",
            "author",
            "parent",
            "content",
            "replies",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "author", "replies", "created_at", "updated_at")

    def get_replies(self, obj):
        replies = obj.replies.filter(is_active=True).select_related("author", "author__profile")
        return ReplySerializer(replies, many=True, context=self.context).data

    def validate_content(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("댓글 내용을 입력해야 합니다.")
        return value

    def validate(self, attrs):
        post = attrs.get("post", getattr(self.instance, "post", None))
        parent = attrs.get("parent", getattr(self.instance, "parent", None))
        if parent and parent.post_id != post.id:
            raise serializers.ValidationError({"parent": "부모 댓글은 같은 게시글에 있어야 합니다."})
        if parent and parent.parent_id:
            raise serializers.ValidationError({"parent": "대댓글에는 다시 답글을 달 수 없습니다."})

        request = self.context.get("request")
        if request and post.status != Post.Status.PUBLISHED:
            can_comment = request.user.is_staff or post.author_id == request.user.id
            if not can_comment:
                raise serializers.ValidationError("공개된 게시글에만 댓글을 작성할 수 있습니다.")
        return attrs

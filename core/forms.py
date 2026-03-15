from django import forms

from .models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["nickname", "message"]
        labels = {
            "nickname": "닉네임",
            "message": "댓글",
        }
        widgets = {
            "nickname": forms.TextInput(
                attrs={
                    "placeholder": "닉네임",
                    "maxlength": 20,
                    "autocomplete": "nickname",
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "placeholder": "댓글을 남겨 주세요.",
                    "rows": 5,
                    "maxlength": 500,
                }
            ),
        }


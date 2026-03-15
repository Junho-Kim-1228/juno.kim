from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import CommentForm
from .models import Comment


def home_view(request):
    if request.method == "POST":
        form = CommentForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "댓글이 저장되었습니다.")
            return redirect("core:home")
    else:
        form = CommentForm()

    comments = Comment.objects.all()[:50]

    return render(
        request,
        "core/home.html",
        {
            "comment_form": form,
            "comments": comments,
        },
    )


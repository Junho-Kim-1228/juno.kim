from django.db import models


class Comment(models.Model):
    nickname = models.CharField(max_length=20)
    message = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.nickname}: {self.message[:30]}"


from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, ContentImageUploadView, PostViewSet, TagViewSet


router = DefaultRouter()
router.register("posts", PostViewSet, basename="post")
router.register("categories", CategoryViewSet, basename="category")
router.register("tags", TagViewSet, basename="tag")

urlpatterns = [
    path("content-images/", ContentImageUploadView.as_view(), name="content-image-upload"),
    *router.urls,
]

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from .views import health_check


urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("api/v1/health/", health_check, name="health-check"),
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/", include("apps.projects.urls")),
    path("api/v1/", include("apps.posts.urls")),
    path("api/v1/", include("apps.comments.urls")),
    path("api/v1/", include("apps.guestbook.urls")),
    path("api/v1/", include("apps.games.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

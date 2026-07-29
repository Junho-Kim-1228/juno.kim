import logging

from django.db import connection
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        logger.error("health_check_failed component=database")
        response = Response(
            {"status": "unavailable"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    else:
        response = Response({"status": "ok"})

    response["Cache-Control"] = "no-store"
    return response

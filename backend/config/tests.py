import logging
from unittest.mock import patch

from django.db import DatabaseError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .logging_filters import SensitiveDataFilter


class HealthCheckTests(TestCase):
    def test_health_check_confirms_database_connection(self):
        response = self.client.get(reverse("health-check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertEqual(response["Cache-Control"], "no-store")

    @patch("config.views.connection.cursor", side_effect=DatabaseError("database unavailable"))
    def test_health_check_returns_503_when_database_is_unavailable(self, _cursor):
        response = self.client.get(reverse("health-check"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})


class SensitiveDataFilterTests(SimpleTestCase):
    def test_redacts_credentials_tokens_and_email_addresses(self):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="email=user@example.com token=secret-value Authorization=Bearer abc.def",
            args=(),
            exc_info=None,
        )

        SensitiveDataFilter().filter(record)

        rendered = record.getMessage()
        self.assertNotIn("user@example.com", rendered)
        self.assertNotIn("secret-value", rendered)
        self.assertNotIn("abc.def", rendered)

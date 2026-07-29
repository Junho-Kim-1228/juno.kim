import logging
import re


class SensitiveDataFilter(logging.Filter):
    """Redact common credentials and personal identifiers before they reach stdout."""

    _patterns = (
        (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer <redacted>"),
        (
            re.compile(
                r"(?i)(\b(?:authorization|cookie|password|secret|token|api[_-]?key)\b\s*[:=]\s*)[^\s,;]+"
            ),
            r"\1<redacted>",
        ),
        (re.compile(r"(?i)([?&](?:token|code)=)[^&#\s]+"), r"\1<redacted>"),
        (
            re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])"),
            "<redacted-email>",
        ),
    )

    @classmethod
    def _redact(cls, value):
        if not isinstance(value, str):
            return value
        for pattern, replacement in cls._patterns:
            value = pattern.sub(replacement, value)
        return value

    def filter(self, record):
        record.msg = self._redact(record.msg)
        if isinstance(record.args, dict):
            record.args = {
                key: "<redacted>"
                if str(key).lower() in {"authorization", "cookie", "password", "secret", "token", "api_key"}
                else self._redact(value)
                for key, value in record.args.items()
            }
        elif isinstance(record.args, tuple):
            record.args = tuple(self._redact(value) for value in record.args)
        return True

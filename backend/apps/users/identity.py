import re
import unicodedata

from django.core.exceptions import ValidationError


PERSONAL_IDENTITY_TERMS = {
    "juno",
    "junho",
    "junokim",
    "kimjunho",
    "김준호",
}
AUTHORITY_IDENTITY_TERMS = {
    "admin",
    "administrator",
    "official",
    "operator",
    "staff",
    "support",
    "owner",
    "moderator",
    "운영자",
    "공식",
    "관리자",
    "사이트운영자",
}
USERNAME_PATTERN = re.compile(r"^[a-z0-9_]+$")
DISPLAY_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9가-힣 _.-]*$")


def normalize_identity(value):
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"[\s_.\-]+", "", normalized)


def is_reserved_identity(value):
    normalized = normalize_identity(value)
    if not normalized:
        return False
    if any(term in normalized for term in PERSONAL_IDENTITY_TERMS):
        return True
    if normalized in AUTHORITY_IDENTITY_TERMS:
        return True

    raw_tokens = [
        token for token in re.split(r"[\s_.\-]+", unicodedata.normalize("NFKC", value).casefold()) if token
    ]
    return any(token in AUTHORITY_IDENTITY_TERMS for token in raw_tokens)


def validate_username(value):
    normalized = unicodedata.normalize("NFKC", value).casefold()
    if value != normalized or not USERNAME_PATTERN.fullmatch(normalized):
        raise ValidationError("username은 영문 소문자, 숫자, 밑줄만 사용할 수 있습니다.")
    if is_reserved_identity(normalized):
        raise ValidationError("사용할 수 없는 username입니다.")
    return normalized


def validate_display_name(value):
    normalized = unicodedata.normalize("NFKC", value).strip()
    if normalized and not DISPLAY_NAME_PATTERN.fullmatch(normalized):
        raise ValidationError("표시 이름에는 한글, 영문, 숫자, 공백, 밑줄, 하이픈, 마침표만 사용할 수 있습니다.")
    if normalized and is_reserved_identity(normalized):
        raise ValidationError("운영자와 혼동될 수 있는 표시 이름은 사용할 수 없습니다.")
    return normalized

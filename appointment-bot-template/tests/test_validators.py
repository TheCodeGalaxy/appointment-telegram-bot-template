from datetime import date, timedelta, time
from unittest.mock import PropertyMock, patch

import pytest

from bot.utils.validators import ValidationError, is_admin, validate_date_text, validate_name, validate_phone, validate_time_text


def test_validate_name_success():
    assert validate_name("John Doe") == "John Doe"
    assert validate_name("  Alice  ") == "Alice"


def test_validate_name_too_short():
    with pytest.raises(ValidationError, match="Name must be between 2 and 100 characters."):
        validate_name("A")


def test_validate_name_too_long():
    long_name = "A" * 101
    with pytest.raises(ValidationError, match="Name must be between 2 and 100 characters."):
        validate_name(long_name)


def test_validate_name_contains_numbers():
    with pytest.raises(ValidationError, match="Name should not contain numbers."):
        validate_name("John123")


def test_validate_phone_success():
    assert validate_phone("+1234567890") == "+1234567890"
    assert validate_phone("123-456-7890") == "1234567890"
    assert validate_phone("(123) 456 7890") == "1234567890"


def test_validate_phone_invalid():
    with pytest.raises(ValidationError, match="Please send a valid phone number."):
        validate_phone("abc123")
    with pytest.raises(ValidationError, match="Please send a valid phone number."):
        validate_phone("123")


def test_validate_date_text_success():
    today_str = date.today().strftime("%Y-%m-%d")
    assert validate_date_text(today_str) == date.today()


def test_validate_date_text_past():
    past_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    with pytest.raises(ValidationError, match="You cannot book an appointment in the past."):
        validate_date_text(past_date)


def test_validate_date_text_invalid_format():
    with pytest.raises(ValidationError, match="Use the format YYYY-MM-DD, e.g. 2026-07-25."):
        validate_date_text("25-07-2026")


def test_validate_time_text_success():
    assert validate_time_text("14:30") == time(14, 30)


def test_validate_time_text_invalid_format():
    with pytest.raises(ValidationError, match="Use the format HH:MM, e.g. 14:30."):
        validate_time_text("2:30 PM")


def test_is_admin_success():
    with patch("bot.utils.validators.settings") as mock_settings:
        type(mock_settings).admin_ids = PropertyMock(return_value={123, 456})
        assert is_admin(123) is True
        assert is_admin(456) is True
        assert is_admin(999) is False

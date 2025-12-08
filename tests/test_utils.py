import pytest

from src.utils import clean_price_string


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("96.72", 96.72),                         # Simple float
        ("ƒ,1 96.72", 96.72),                     # Encoded currency symbol with stray digits
        ("Rs. 96.72", 96.72),                     # Text currency prefix
        ("1,200.50", 1200.50),                    # Comma as thousands separator
        ("  96.72  ", 96.72),                     # Surrounding whitespace
    ],
)
def test_clean_price_string_valid_inputs(raw, expected):
    result = clean_price_string(raw)
    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "N/A",
        "Free",
    ],
)
def test_clean_price_string_invalid_inputs(raw):
    assert clean_price_string(raw) is None


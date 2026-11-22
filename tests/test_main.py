from datetime import date, datetime

import pytest

import main
from src.scraper import ExtractionError

PETROL = [{"city": "New Delhi", "state": "Delhi", "price": 102.12}]
DIESEL = [{"city": "New Delhi", "state": "Delhi", "price": 95.20}]


def _ppac(monkeypatch, ppac_date, delhi_petrol):
    official = {"petrol": {"New Delhi": delhi_petrol}, "diesel": {"New Delhi": 95.20}}
    monkeypatch.setattr(main, "fetch_ppac_metro_prices", lambda s: (ppac_date, official))


def test_ppac_match_passes(monkeypatch):
    _ppac(monkeypatch, datetime.now(main.IST).date(), 102.13)  # within tolerance
    main.check_against_ppac(PETROL, DIESEL, None)


def test_ppac_mismatch_same_day_fails(monkeypatch):
    _ppac(monkeypatch, datetime.now(main.IST).date(), 99.00)
    with pytest.raises(ExtractionError):
        main.check_against_ppac(PETROL, DIESEL, None)


def test_ppac_mismatch_stale_only_warns(monkeypatch):
    _ppac(monkeypatch, date(2020, 1, 1), 99.00)
    main.check_against_ppac(PETROL, DIESEL, None)


def test_ppac_unavailable_only_warns(monkeypatch):
    monkeypatch.setattr(main, "fetch_ppac_metro_prices", lambda s: None)
    main.check_against_ppac(PETROL, DIESEL, None)

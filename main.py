#!/usr/bin/env python3
"""
Main script to scrape fuel prices and generate prices.json
Run with: uv run python main.py
"""
import json
import logging
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.scraper import (
    fetch_fuel_data,
    fetch_ppac_metro_prices,
    parse_fuel_data,
    get_request_session,
    PETROL_URL,
    DIESEL_URL,
    MIN_DISTRICTS,
    SOURCE,
    ExtractionError,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


IST = timezone(timedelta(hours=5, minutes=30))
PPAC_TOLERANCE = 0.05  # rupees; oil companies differ by a paisa or two


def get_ist_timestamp() -> str:
    """Return the current timestamp in IST timezone (ISO 8601)."""
    return datetime.now(IST).isoformat()


def check_against_ppac(petrol_data: list, diesel_data: list, session) -> None:
    """
    Compare metro prices with PPAC's official figures.

    Raises ExtractionError on a mismatch only when PPAC is dated today; PPAC posts
    with a lag of a day or two, so older figures can legitimately differ after a revision.
    """
    ppac = fetch_ppac_metro_prices(session)
    if ppac is None:
        logger.warning("PPAC cross-check skipped: could not fetch official prices")
        return

    ppac_date, official = ppac
    ours = {"petrol": petrol_data, "diesel": diesel_data}
    mismatches = []
    for fuel, metros in official.items():
        scraped = {row["city"]: row["price"] for row in ours[fuel]}
        for city, price in metros.items():
            got = scraped.get(city)
            if got is None or abs(got - price) > PPAC_TOLERANCE:
                mismatches.append(f"{fuel} {city}: scraped {got}, PPAC {price}")

    if not mismatches:
        logger.info("PPAC cross-check passed (PPAC dated %s)", ppac_date)
    elif ppac_date == datetime.now(IST).date():
        raise ExtractionError("PPAC mismatch: " + "; ".join(mismatches))
    else:
        logger.warning(
            "PPAC (dated %s) differs, likely a price revision since: %s",
            ppac_date, "; ".join(mismatches),
        )


def scrape_fuel_prices() -> dict:
    """
    Main function to scrape petrol and diesel prices.

    Returns:
        dict: Data structure with petrol and diesel price lists.

    Raises:
        ExtractionError: If scraping fails critically.
    """
    logger.info("=" * 70)
    logger.info("Starting OpenFuel scraping pipeline")
    logger.info("=" * 70)

    scraper = get_request_session()

    # Fetch and parse petrol data
    logger.info("Fetching petrol prices...")
    petrol_html = fetch_fuel_data(PETROL_URL, session=scraper)

    if petrol_html is None:
        logger.error("Failed to fetch petrol data")
        raise ExtractionError("Could not fetch petrol data from source")

    try:
        petrol_data = parse_fuel_data(petrol_html, "petrol")
        logger.info("Successfully extracted %d petrol prices", len(petrol_data))
    except ExtractionError as exc:
        logger.error("Failed to parse petrol data: %s", exc)
        raise

    # Fetch and parse diesel data
    logger.info("Fetching diesel prices...")
    diesel_html = fetch_fuel_data(DIESEL_URL, session=scraper)

    if diesel_html is None:
        logger.error("Failed to fetch diesel data")
        raise ExtractionError("Could not fetch diesel data from source")

    try:
        diesel_data = parse_fuel_data(diesel_html, "diesel")
        logger.info("Successfully extracted %d diesel prices", len(diesel_data))
    except ExtractionError as exc:
        logger.error("Failed to parse diesel data: %s", exc)
        raise

    # A sharp drop in rows means the source layout changed; keep yesterday's file instead.
    for fuel, rows in (("petrol", petrol_data), ("diesel", diesel_data)):
        if len(rows) < MIN_DISTRICTS:
            raise ExtractionError(
                f"Only got {len(rows)} {fuel} prices, expected at least {MIN_DISTRICTS}"
            )

    check_against_ppac(petrol_data, diesel_data, scraper)

    # Create output structure
    timestamp = get_ist_timestamp()
    output = {
        "last_updated_ist": timestamp,
        "source": SOURCE,
        "petrol": petrol_data,
        "diesel": diesel_data,
    }

    logger.info("\n" + "=" * 70)
    logger.info("Scraping completed successfully")
    logger.info("   Timestamp: %s", timestamp)
    logger.info("   Petrol entries: %d", len(petrol_data))
    logger.info("   Diesel entries: %d", len(diesel_data))
    logger.info("=" * 70)

    return output


def save_json(data: dict, output_path: Path = Path("prices.json")) -> None:
    """
    Save scraped data to JSON file.

    Args:
        data: Data structure to save.
        output_path: Path to output file (default: prices.json).
    """
    logger.info("Saving data to %s...", output_path)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info("Successfully saved to %s", output_path)
        file_size = output_path.stat().st_size
        logger.info("   File size: %s bytes", f"{file_size:,}")
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to save JSON file: %s", exc)
        raise


def main() -> None:
    """Main entry point."""
    try:
        data = scrape_fuel_prices()
        save_json(data)

        logger.info("Sample data:")
        if data.get("petrol"):
            logger.info("   First petrol entry: %s", data["petrol"][0])
        if data.get("diesel"):
            logger.info("   First diesel entry: %s", data["diesel"][0])

        logger.info("Pipeline completed successfully!")
        sys.exit(0)

    except ExtractionError as exc:
        logger.error("Critical extraction error: %s", exc)
        logger.error("The scraper failed to extract sufficient data.")
        logger.error("Previous prices.json (if exists) will remain unchanged.")
        sys.exit(1)

    except Exception as exc:  # noqa: BLE001
        logger.error("Unexpected error: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()


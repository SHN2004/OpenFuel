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
    parse_fuel_data,
    get_scraper,
    PETROL_URL,
    DIESEL_URL,
    ExtractionError,
    CLOUDSCRAPER_AVAILABLE,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def get_ist_timestamp() -> str:
    """Return the current timestamp in IST timezone (ISO 8601)."""
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).isoformat()


def scrape_fuel_prices() -> dict:
    """
    Main function to scrape petrol and diesel prices.

    Returns:
        dict: Data structure with petrol and diesel price lists.

    Raises:
        ExtractionError: If scraping fails critically.
    """
    if not CLOUDSCRAPER_AVAILABLE:
        logger.error(
            "cloudscraper is not installed. Install with: uv add cloudscraper"
        )
        sys.exit(1)

    logger.info("=" * 70)
    logger.info("Starting OpenFuel scraping pipeline")
    logger.info("=" * 70)

    # Create a single scraper instance to reuse
    scraper = get_scraper()

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

    # Validate we got reasonable data
    if len(petrol_data) < 20:
        logger.warning(
            "Only got %d petrol prices, expected at least 20", len(petrol_data)
        )

    if len(diesel_data) < 20:
        logger.warning(
            "Only got %d diesel prices, expected at least 20", len(diesel_data)
        )

    # Create output structure
    timestamp = get_ist_timestamp()
    output = {
        "last_updated_ist": timestamp,
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


"""
Integration test for the fuel price scraper.
Run this with: uv run pytest tests/test_scraper_integration.py -v
Or run directly: uv run python tests/test_scraper_integration.py
"""
import json
import logging
from pathlib import Path

import pytest

from src.scraper import (
    fetch_fuel_data,
    parse_fuel_data,
    get_request_session,
    PETROL_URL,
    DIESEL_URL,
    ExtractionError
)


# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)


class TestScraperIntegration:
    """Integration tests that hit the real website."""
    
    def test_fetch_petrol_data(self):
        """Test fetching petrol data from the real website."""
        session = get_request_session()
        html_content = fetch_fuel_data(PETROL_URL, session)
        
        assert html_content is not None, "Failed to fetch petrol data"
        assert len(html_content) > 0, "Petrol HTML content is empty"
        assert "petrol" in html_content.lower(), "HTML doesn't contain 'petrol'"
    
    def test_fetch_diesel_data(self):
        """Test fetching diesel data from the real website."""
        session = get_request_session()
        html_content = fetch_fuel_data(DIESEL_URL, session)
        
        assert html_content is not None, "Failed to fetch diesel data"
        assert len(html_content) > 0, "Diesel HTML content is empty"
        assert "diesel" in html_content.lower(), "HTML doesn't contain 'diesel'"
    
    def test_parse_petrol_prices(self):
        """Test parsing petrol prices from real data."""
        session = get_request_session()
        html_content = fetch_fuel_data(PETROL_URL, session)
        
        assert html_content is not None, "Failed to fetch data"
        
        petrol_data = parse_fuel_data(html_content, "petrol")
        
        # Assertions
        assert len(petrol_data) > 0, "No petrol data extracted"
        assert len(petrol_data) >= 20, f"Expected at least 20 cities, got {len(petrol_data)}"
        
        # Check structure of first item
        first_item = petrol_data[0]
        assert "city" in first_item, "Missing 'city' key"
        assert "price" in first_item, "Missing 'price' key"
        assert isinstance(first_item["city"], str), "City should be a string"
        assert isinstance(first_item["price"], float), "Price should be a float"
        assert first_item["price"] > 0, "Price should be positive"
        
        # Print sample data for visual verification
        print(f"\n✓ Extracted {len(petrol_data)} petrol prices")
        print(f"Sample data (first 5 cities):")
        for item in petrol_data[:5]:
            print(f"  {item['city']}: ₹{item['price']}")
    
    def test_parse_diesel_prices(self):
        """Test parsing diesel prices from real data."""
        session = get_request_session()
        html_content = fetch_fuel_data(DIESEL_URL, session)
        
        assert html_content is not None, "Failed to fetch data"
        
        diesel_data = parse_fuel_data(html_content, "diesel")
        
        # Assertions
        assert len(diesel_data) > 0, "No diesel data extracted"
        assert len(diesel_data) >= 20, f"Expected at least 20 cities, got {len(diesel_data)}"
        
        # Check structure
        first_item = diesel_data[0]
        assert "city" in first_item, "Missing 'city' key"
        assert "price" in first_item, "Missing 'price' key"
        assert isinstance(first_item["price"], float), "Price should be a float"
        
        # Print sample data
        print(f"\n✓ Extracted {len(diesel_data)} diesel prices")
        print(f"Sample data (first 5 cities):")
        for item in diesel_data[:5]:
            print(f"  {item['city']}: ₹{item['price']}")
    
    def test_full_pipeline_generates_json(self):
        """Test the complete pipeline and generate a sample JSON output."""
        session = get_request_session()
        
        # Fetch petrol data
        petrol_html = fetch_fuel_data(PETROL_URL, session)
        assert petrol_html is not None, "Failed to fetch petrol data"
        petrol_data = parse_fuel_data(petrol_html, "petrol")
        
        # Fetch diesel data
        diesel_html = fetch_fuel_data(DIESEL_URL, session)
        assert diesel_html is not None, "Failed to fetch diesel data"
        diesel_data = parse_fuel_data(diesel_html, "diesel")
        
        # Create a combined structure (as your actual pipeline might do)
        from datetime import datetime, timezone, timedelta
        
        ist = timezone(timedelta(hours=5, minutes=30))
        timestamp = datetime.now(ist).isoformat()
        
        output = {
            "last_updated_ist": timestamp,
            "petrol": petrol_data,
            "diesel": diesel_data
        }
        
        # Save to test output file
        output_path = Path("test_output.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Successfully generated {output_path}")
        print(f"✓ Petrol entries: {len(petrol_data)}")
        print(f"✓ Diesel entries: {len(diesel_data)}")
        print(f"✓ Last updated: {timestamp}")
        
        # Verify file was created and is valid JSON
        assert output_path.exists(), "Output file was not created"
        
        with open(output_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        
        assert "last_updated_ist" in loaded
        assert "petrol" in loaded
        assert "diesel" in loaded
        assert len(loaded["petrol"]) == len(petrol_data)
        assert len(loaded["diesel"]) == len(diesel_data)


def manual_test():
    """Run a quick manual test without pytest."""
    print("🚀 Running manual scraper test...\n")
    
    try:
        session = get_request_session()
        
        # Test petrol
        print("📊 Fetching petrol prices...")
        petrol_html = fetch_fuel_data(PETROL_URL, session)
        if petrol_html:
            petrol_data = parse_fuel_data(petrol_html, "petrol")
            print(f"✓ Extracted {len(petrol_data)} petrol prices")
            print(f"  Sample: {petrol_data[0]}")
        else:
            print("✗ Failed to fetch petrol data")
            return
        
        # Test diesel
        print("\n📊 Fetching diesel prices...")
        diesel_html = fetch_fuel_data(DIESEL_URL, session)
        if diesel_html:
            diesel_data = parse_fuel_data(diesel_html, "diesel")
            print(f"✓ Extracted {len(diesel_data)} diesel prices")
            print(f"  Sample: {diesel_data[0]}")
        else:
            print("✗ Failed to fetch diesel data")
            return
        
        # Generate JSON
        print("\n💾 Generating JSON output...")
        from datetime import datetime, timezone, timedelta
        
        ist = timezone(timedelta(hours=5, minutes=30))
        timestamp = datetime.now(ist).isoformat()
        
        output = {
            "last_updated_ist": timestamp,
            "petrol": petrol_data,
            "diesel": diesel_data
        }
        
        output_path = Path("test_output.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Successfully saved to {output_path}")
        print(f"\n📈 Summary:")
        print(f"  - Petrol cities: {len(petrol_data)}")
        print(f"  - Diesel cities: {len(diesel_data)}")
        print(f"  - Timestamp: {timestamp}")
        print(f"\n✅ All tests passed!")
        
    except ExtractionError as e:
        print(f"\n✗ Extraction error: {e}")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    manual_test()
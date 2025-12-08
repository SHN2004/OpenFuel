import logging
from typing import Dict, List, Optional, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from bs4 import BeautifulSoup

from src.utils import clean_price_string

try:
    import cloudscraper  # type: ignore[import]
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False
    cloudscraper = None  # type: ignore[assignment]


# Constants
PETROL_URL = "https://www.goodreturns.in/petrol-price.html"
DIESEL_URL = "https://www.goodreturns.in/diesel-price.html"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 30  # Increased for Cloudflare challenges

# CSS Selectors
CSS_SELECTOR_BLOCK = "gd-fuel-table-block"
CSS_SELECTOR_TABLE = "gd-fuel-table-list"
CSS_SELECTOR_ROW = "tr"
CSS_SELECTOR_HEADER = "th"
CSS_SELECTOR_CELL = "td"


class ExtractionError(Exception):
    """Raised when fuel data extraction fails (e.g., no tables found)."""
    pass


def get_request_session() -> requests.Session:
    """
    Create and configure a requests.Session with retry and headers.

    This is the primary HTTP client used in unit tests and non-Cloudflare
    environments, and it matches Story 2.1 acceptance criteria.
    """
    session = requests.Session()

    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    session.headers.update({"User-Agent": USER_AGENT})
    return session


def get_scraper():
    """
    Create a scraper client suitable for real scraping runs.

    When cloudscraper is available, use it to better handle Cloudflare.
    Otherwise, fall back to the standard requests.Session.
    """
    if CLOUDSCRAPER_AVAILABLE:
        logging.info("Using cloudscraper to bypass Cloudflare protection")
        scraper = cloudscraper.create_scraper(
            browser={
                "browser": "chrome",
                "platform": "windows",
                "desktop": True,
            },
            delay=10,
        )
        return scraper

    logging.warning(
        "cloudscraper not available, using basic requests (may fail with Cloudflare)"
    )
    return get_request_session()


def fetch_fuel_data(url: str, session: Optional[requests.Session] = None) -> Optional[str]:
    """
    Fetches the raw HTML content from the given URL using a configured scraper.

    Args:
        url (str): The URL to fetch data from.
        session (Optional[requests.Session]): Existing session/scraper to reuse.
            If None, a new requests.Session is created via get_request_session().

    Returns:
        Optional[str]: The raw HTML content as a string if successful, 
                       or None if the request fails or times out.
    """
    client = session or get_request_session()

    try:
        logging.info(f"Fetching data from {url}")
        response = client.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        # Verify we didn't get a Cloudflare challenge page
        if 'cloudflare' in response.text.lower() and 'ray id' in response.text.lower():
            logging.error("Received Cloudflare challenge page instead of actual content")
            return None
            
        logging.info(f"Successfully fetched {len(response.text)} bytes from {url}")
        return response.text
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching {url}: {e}", exc_info=True)
        return None


def parse_fuel_data(html_content: str, fuel_type: str) -> List[Dict[str, Union[str, float]]]:
    """
    Parses HTML content to extract fuel prices.

    Args:
        html_content (str): The raw HTML content.
        fuel_type (str): The type of fuel (e.g., 'petrol' or 'diesel').

    Returns:
        List[Dict[str, Union[str, float]]]: A list of dictionaries containing city and price data.
                                            e.g. [{'city': 'New Delhi', 'price': 96.72}, ...]

    Raises:
        ExtractionError: If no valid data tables are found in the HTML.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    blocks = soup.find_all("div", class_=CSS_SELECTOR_BLOCK)
    
    unique_data: Dict[str, float] = {}
    tables_found = False

    for block in blocks:
        table = block.find("table", class_=CSS_SELECTOR_TABLE)
        if not table:
            continue
        
        tables_found = True
        rows = table.find_all(CSS_SELECTOR_ROW)
        
        for row in rows:
            # Skip header rows
            if row.find(CSS_SELECTOR_HEADER):
                continue
            
            cols = row.find_all(CSS_SELECTOR_CELL)
            if len(cols) >= 2:
                # Extract city/state name (usually in the first column)
                name_col = cols[0]
                price_col = cols[1]
                
                name_text = name_col.get_text(strip=True)
                price_text = price_col.get_text(strip=True)

                price_val = clean_price_string(price_text)

                if price_val is None:
                    logging.warning(f"Could not parse price '{price_text}' for {name_text}")
                    continue

                if name_text and name_text not in unique_data:
                    unique_data[name_text] = price_val

    if not unique_data:
        # If tables were found but no data extracted, or no tables found at all
        if not tables_found:
             raise ExtractionError(f"No fuel table blocks found in {fuel_type} data.")
        else:
             raise ExtractionError(f"Failed to extract any fuel data from {fuel_type} page.")

    logging.info(f"Successfully extracted {len(unique_data)} {fuel_type} prices")
    return [{"city": city, "price": price} for city, price in unique_data.items()]

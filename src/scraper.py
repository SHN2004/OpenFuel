import io
import json
import logging
import re
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple, Union

import pypdf
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from bs4 import BeautifulSoup

from src.utils import clean_price_string


# Constants
# Any Business Today state page carries the all-India district table; Delhi is the stable one.
PETROL_URL = "https://www.businesstoday.in/fuel-price/petrol-price-in-delhi-today"
DIESEL_URL = "https://www.businesstoday.in/fuel-price/diesel-price-in-delhi-today"
PPAC_PAGE_URL = (
    "https://ppac.gov.in/retail-selling-price-rsp-of-petrol-diesel-and-domestic-lpg/"
    "rsp-of-petrol-and-diesel-in-metro-cities-since-16-6-2017"
)
SOURCE = "businesstoday.in"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 30
MIN_DISTRICTS = 600  # ~709 as of Nov 2026; fewer means the page layout changed
# PPAC column order, named as Business Today names them (PPAC's "Delhi" is "New Delhi").
PPAC_METROS = ("New Delhi", "Mumbai", "Chennai", "Kolkata")


class ExtractionError(Exception):
    """Raised when fuel data extraction fails (e.g., no tables found)."""
    pass


def get_request_session() -> requests.Session:
    """Create a requests.Session with retry and a browser User-Agent."""
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


def fetch_fuel_data(url: str, session: Optional[requests.Session] = None) -> Optional[str]:
    """
    Fetch the raw HTML content from the given URL.

    Returns None if the request fails, times out, or a Cloudflare challenge is served.
    """
    client = session or get_request_session()

    try:
        logging.info(f"Fetching data from {url}")
        response = client.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        if 'cloudflare' in response.text.lower() and 'ray id' in response.text.lower():
            logging.error("Received Cloudflare challenge page instead of actual content")
            return None

        logging.info(f"Successfully fetched {len(response.text)} bytes from {url}")
        return response.text

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching {url}: {e}", exc_info=True)
        return None


def _district_states(html_content: str) -> Dict[str, Optional[str]]:
    """
    Map lowercase district name -> state from the page's embedded dropdown JSON.

    Names the source lists under more than one state (e.g. Aurangabad: Bihar and
    Maharashtra) map to None, since the price table can't tell them apart.
    """
    start = html_content.find("let states")
    if start == -1:
        return {}
    try:
        master = json.JSONDecoder().raw_decode(
            html_content[html_content.index("{", start):]
        )[0]["master"]
    except (ValueError, KeyError):
        return {}

    owners: Dict[str, set] = {}
    for state, districts in master.items():
        for district in districts:
            owners.setdefault(district, set()).add(state.title())
    return {d: (s.pop() if len(s) == 1 else None) for d, s in owners.items()}


def parse_fuel_data(html_content: str, fuel_type: str) -> List[Dict[str, Union[str, float, None]]]:
    """
    Parse the all-India district price table from a Business Today fuel page.

    Returns:
        [{'city': 'Barabanki', 'state': 'Uttar Pradesh', 'price': 102.68}, ...]
        'city' holds the district name (key kept for API compatibility);
        'state' is None when unknown or ambiguous.

    Raises:
        ExtractionError: If the district table is missing or yields no prices.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    table = next(
        (t for t in soup.find_all("table")
         if (tr := t.find("tr")) and tr.get_text(strip=True).upper().startswith("CITY")),
        None,
    )
    if table is None:
        raise ExtractionError(f"No district table found in {fuel_type} data.")

    states = _district_states(html_content)
    unique_data: Dict[str, Dict[str, Union[str, float, None]]] = {}

    for row in table.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) < 2:
            continue
        name = cols[0].get_text(strip=True)
        price = clean_price_string(cols[1].get_text(strip=True))
        if not name or price is None:
            logging.warning(f"Could not parse row {row.get_text(' ', strip=True)!r}")
            continue
        if name not in unique_data:
            unique_data[name] = {"city": name, "state": states.get(name.lower()), "price": price}

    if not unique_data:
        raise ExtractionError(f"Failed to extract any fuel data from {fuel_type} page.")

    logging.info(f"Successfully extracted {len(unique_data)} {fuel_type} prices")
    return list(unique_data.values())


def parse_ppac_text(text: str) -> Optional[Tuple[date, Dict[str, Dict[str, float]]]]:
    """
    Parse the latest row of PPAC's daily metro price PDF text.

    The row looks like: "20-Nov-26 102.12 111.21 107.77 113.51 20-Nov-26 95.20 97.83 99.55 99.82"
    (petrol for Delhi, Mumbai, Chennai, Kolkata, then diesel for the same).
    """
    num = r"\s+(\d{2,3}\.\d{2})"
    m = re.search(r"(\d{2}-[A-Za-z]{3}-\d{2})" + num * 4 + r"\s+\1" + num * 4, text)
    if not m:
        return None
    prices = [float(p) for p in m.groups()[1:]]
    return (
        datetime.strptime(m.group(1), "%d-%b-%y").date(),
        {
            "petrol": dict(zip(PPAC_METROS, prices[:4])),
            "diesel": dict(zip(PPAC_METROS, prices[4:])),
        },
    )


def fetch_ppac_metro_prices(
    session: Optional[requests.Session] = None,
) -> Optional[Tuple[date, Dict[str, Dict[str, float]]]]:
    """
    Fetch official IOC metro prices from PPAC's latest daily PDF.

    The PDF name changes daily, so it is found via the PPAC page. Returns None on any failure.
    """
    client = session or get_request_session()
    page = fetch_fuel_data(PPAC_PAGE_URL, client)
    if page is None:
        return None
    m = re.search(r'href="([^"]*PP_9_a_DailyPriceMSHSD_Metro[^"]*\.pdf)"', page)
    if not m:
        logging.error("PPAC daily metro PDF link not found")
        return None
    try:
        response = client.get(m.group(1), timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        text = pypdf.PdfReader(io.BytesIO(response.content)).pages[0].extract_text()
    except Exception as exc:  # noqa: BLE001 - PPAC is a cross-check, never fatal on its own
        logging.error(f"Could not read PPAC PDF: {exc}")
        return None
    return parse_ppac_text(text)

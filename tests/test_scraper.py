import pytest
import requests
import requests_mock
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from datetime import date
from src.scraper import get_request_session, fetch_fuel_data, parse_fuel_data, parse_ppac_text, ExtractionError, USER_AGENT, REQUEST_TIMEOUT

@pytest.fixture
def MOCK_HTML_COMPLETE():
    # Shape of a Business Today fuel page: embedded state map + all-India district table.
    return """
    <script>
        function manageDependentdropdown(state, city = '') {
            let states = {"master": {
                "uttar pradesh": {"barabanki": {"city_id": 1}, "lucknow": {"city_id": 2}},
                "bihar": {"aurangabad": {"city_id": 3}},
                "maharashtra": {"aurangabad": {"city_id": 4}}
            }};
        }
    </script>
    <table><tr><td>Open Price</td><td>₹102.91</td></tr></table>
    <table class="table table-striped">
        <tr><th>CITY</th><th>PETROL PRICE/LITRE</th><th>CHANGES</th></tr>
        <tr><td><a href="/fuel-price/petrol-price-in-barabanki-today">Barabanki</a></td>
            <td>₹102.68</td><td><div>0.00</div></td></tr>
        <tr><td><a href="/fuel-price/petrol-price-in-lucknow-today">Lucknow</a></td>
            <td>₹102.23</td><td><div>0.00</div></td></tr>
        <tr><td><a href="/fuel-price/petrol-price-in-lucknow-today">Lucknow</a></td>
            <td>₹102.23</td><td><div>0.00</div></td></tr>
        <tr><td><a href="/fuel-price/petrol-price-in-aurangabad-today">Aurangabad</a></td>
            <td>₹110.50</td><td><div>0.00</div></td></tr>
        <tr><td><a href="/fuel-price/petrol-price-in-nowhere-today">Nowhere</a></td>
            <td>N/A</td><td><div>0.00</div></td></tr>
    </table>
    """

@pytest.fixture
def MOCK_HTML_NO_TABLE():
    return """
    <html>
        <body>
            <div>No fuel tables here</div>
        </body>
    </html>
    """

def test_get_request_session_configuration():
    """
    Test that get_request_session returns a properly configured Session object
    per Acceptance Criteria #1 and #2.
    """
    session = get_request_session()
    
    # AC 1: Must be a requests.Session object
    assert isinstance(session, requests.Session)
    
    # AC 3: Must include specific User-Agent
    assert session.headers['User-Agent'] == USER_AGENT
    
    # AC 2: HTTPAdapter with specific Retry strategy
    # Check adapter mounting for https and http
    adapter_https = session.get_adapter("https://www.goodreturns.in")
    adapter_http = session.get_adapter("http://www.goodreturns.in")
    
    assert isinstance(adapter_https, HTTPAdapter)
    assert isinstance(adapter_http, HTTPAdapter)
    
    # Inspect the Retry object of the adapter
    retry_strategy = adapter_https.max_retries
    
    assert isinstance(retry_strategy, Retry)
    assert retry_strategy.total == 3
    assert retry_strategy.backoff_factor == 1
    assert set(retry_strategy.status_forcelist) == {429, 500, 502, 503, 504}
    assert set(retry_strategy.allowed_methods) == {"GET"}

def test_fetch_fuel_data_success():
    """
    Test AC 4: fetch_fuel_data returns raw HTML content on success (HTTP 200).
    """
    test_url = "https://www.goodreturns.in/petrol-price.html"
    mock_html = "<html><body>Price Data</body></html>"
    
    with requests_mock.Mocker() as m:
        m.get(test_url, text=mock_html, status_code=200)
        result = fetch_fuel_data(test_url)
        assert result == mock_html

def test_fetch_fuel_data_timeout():
    """
    Test AC 5: fetch_fuel_data returns None on timeout and handles it gracefully.
    """
    test_url = "https://www.goodreturns.in/petrol-price.html"
    
    with requests_mock.Mocker() as m:
        m.get(test_url, exc=requests.exceptions.Timeout)
        result = fetch_fuel_data(test_url)
        assert result is None

def test_fetch_fuel_data_http_error_handling():
    """
    Test AC 5: fetch_fuel_data returns None on HTTP errors (e.g., 500).
    Note: We cannot easily verify call_count == 4 here because requests_mock
    mocks the adapter's send method, bypassing the retry loop.
    We rely on test_get_request_session_configuration to verify the retry strategy.
    """
    test_url = "https://www.goodreturns.in/diesel-price.html"
    
    with requests_mock.Mocker() as m:
        m.get(test_url, status_code=500)
        
        result = fetch_fuel_data(test_url)
        assert result is None


def test_fetch_fuel_data_uses_provided_session():
    """
    Test that fetch_fuel_data uses the session provided in the argument.
    """
    test_url = "https://www.goodreturns.in/petrol-price.html"
    mock_html = "<html>Data</html>"
    
    session = requests.Session()
    session.headers.update({'Custom-Header': 'TestValue'})
    
    with requests_mock.Mocker() as m:
        m.get(test_url, text=mock_html, status_code=200, request_headers={'Custom-Header': 'TestValue'})
        
        result = fetch_fuel_data(test_url, session=session)
        assert result == mock_html

def test_parse_fuel_data_complete(MOCK_HTML_COMPLETE):
    """District table is parsed, deduplicated, and joined with states."""
    result = parse_fuel_data(MOCK_HTML_COMPLETE, "petrol")
    by_city = {item['city']: item for item in result}

    # Open Price table ignored, duplicate Lucknow collapsed, unparseable price skipped
    assert set(by_city) == {"Barabanki", "Lucknow", "Aurangabad"}
    assert by_city["Barabanki"] == {"city": "Barabanki", "state": "Uttar Pradesh", "price": 102.68}
    assert by_city["Lucknow"]["price"] == 102.23
    # Listed under two states by the source, so the state is unknown rather than guessed
    assert by_city["Aurangabad"]["state"] is None


def test_parse_fuel_data_without_state_map(MOCK_HTML_COMPLETE):
    """Prices still parse if the embedded state map disappears."""
    html = MOCK_HTML_COMPLETE.replace("let states", "let other")
    result = parse_fuel_data(html, "petrol")
    assert len(result) == 3
    assert all(item["state"] is None for item in result)


def test_parse_ppac_text():
    text = (
        "Table Posted: 20-Nov-26\n"
        "Delhi Mumbai Chennai Kolkata Delhi Mumbai Chennai Kolkata\n"
        "20-Nov-26 102.12   111.21   107.77   113.51   20-Nov-26 95.20   97.83   99.55   99.82\n"
        "19-Nov-26 101.00   111.21   107.77   113.51   19-Nov-26 95.20   97.83   99.55   99.82\n"
    )
    ppac_date, prices = parse_ppac_text(text)
    assert ppac_date == date(2026, 11, 20)
    assert prices["petrol"] == {"New Delhi": 102.12, "Mumbai": 111.21, "Chennai": 107.77, "Kolkata": 113.51}
    assert prices["diesel"]["Kolkata"] == 99.82
    assert parse_ppac_text("no table here") is None


def test_parse_fuel_data_no_table(MOCK_HTML_NO_TABLE):
    """
    Test parse_fuel_data raises ExtractionError when no tables are found.
    AC 8
    """
    with pytest.raises(ExtractionError):
        parse_fuel_data(MOCK_HTML_NO_TABLE, "petrol")
import pytest
import requests
import requests_mock
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from src.scraper import get_request_session, fetch_fuel_data, parse_fuel_data, ExtractionError, USER_AGENT, REQUEST_TIMEOUT

@pytest.fixture
def MOCK_HTML_COMPLETE():
    return """
    <section>
        <div class="gd-fuel-table-block">
            <div class="gd-fuel-table-data">
                <h2 class="gd-fuel-table-block-title">Petrol Price in Indian Metro Cities</h2>
                <table class="gd-fuel-table-list">
                    <tbody>
                        <tr><th>City</th><th>Price</th></tr>
                        <tr>
                            <td><a href="/delhi">New Delhi</a></td>
                            <td>₹94.77</td>
                        </tr>
                        <tr>
                            <td><a href="/chandigarh">Chandigarh</a></td>
                            <td>₹94.30</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        <div class="gd-fuel-table-block">
            <div class="gd-fuel-table-data">
                <h2 class="gd-fuel-table-block-title">State-Wise Petrol Price in India</h2>
                <table class="gd-fuel-table-list">
                    <tbody>
                        <tr><th>State</th><th>Price</th></tr>
                        <tr>
                            <td><a href="/chandigarh-state">Chandigarh</a></td>
                            <td>₹94.30</td>
                        </tr>
                        <tr>
                            <td><a href="/punjab">Punjab</a></td>
                            <td>₹98.15</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </section>
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
    """
    Test parse_fuel_data with a complete HTML structure containing duplicate cities.
    AC 3, 4, 5, 6, 7
    """
    result = parse_fuel_data(MOCK_HTML_COMPLETE, "petrol")
    
    # Convert list of dicts to a dictionary for easier assertion
    result_dict = {item['city']: item['price'] for item in result}
    
    # AC 5: Check extraction
    assert result_dict['New Delhi'] == 94.77
    assert result_dict['Chandigarh'] == 94.30
    assert result_dict['Punjab'] == 98.15
    
    # AC 6: Check deduplication (Chandigarh appears twice in HTML, should be extracted once)
    # The list length should match unique cities
    assert len(result) == 3
    
    # Ensure structure matches AC 7
    assert isinstance(result, list)
    assert isinstance(result[0], dict)
    assert 'city' in result[0]
    assert 'price' in result[0]
    assert isinstance(result[0]['price'], float)

def test_parse_fuel_data_no_table(MOCK_HTML_NO_TABLE):
    """
    Test parse_fuel_data raises ExtractionError when no tables are found.
    AC 8
    """
    with pytest.raises(ExtractionError):
        parse_fuel_data(MOCK_HTML_NO_TABLE, "petrol")
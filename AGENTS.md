# Agent Guidelines for OpenFuel

This file contains project-specific instructions for AI agents working on this repository.

## Commands

### Setup
```bash
uv sync                    # Install dependencies
```

### Running the Scraper
```bash
uv run python main.py      # Execute scraping pipeline locally
```

### Testing
```bash
uv run pytest              # Run all tests
uv run pytest tests/test_scraper.py  # Run specific test file
uv run pytest tests/test_scraper.py::test_function_name -v  # Run specific test
```

### No Linting/Type Checking
This project does not have explicit linting (ruff, black, flake8) or type checking (mypy) configured. Focus on writing clean, readable code following the guidelines below.

## Project Structure

```
main.py                              # Entry point - orchestrates scraping pipeline
├── src/
│   ├── scraper.py                   # HTTP fetching (cloudscraper) and HTML parsing (BeautifulSoup)
│   └── utils.py                     # Price string cleaning/normalization
├── tests/
│   ├── conftest.py                  # Shared pytest fixtures
│   ├── test_scraper.py              # Unit tests for scraper module
│   ├── test_scraper_integration.py  # Integration tests for scraper
│   ├── test_utils.py                # Unit tests for utils module
│   └── test_workflow_infra.py       # Tests for GitHub Actions workflow configuration
├── prices.json                      # Output data file (the "database")
├── verify_structure.py              # Initial setup verification script (validates project structure)
└── .github/workflows/
    └── daily_scrape.yml             # GitHub Actions workflow (runs at 06:00 IST / 00:30 UTC)
```

## Code Style Guidelines

### Naming Conventions
- **Functions/variables:** `snake_case`
- **Classes:** `CamelCase`
- **Constants:** `UPPER_CASE`
- **Files:** `snake_case.py`
- **JSON keys:** `snake_case` (e.g., `last_updated_ist`, `petrol`, `diesel`)

### Imports
- Order: standard library → third-party → local modules
- Group imports logically with blank lines between groups
- Use `from typing import Optional, Dict, List, Union` for type hints
- Try/except imports for optional dependencies:
  ```python
  try:
      import cloudscraper
      CLOUDSCRAPER_AVAILABLE = True
  except ImportError:
      CLOUDSCRAPER_AVAILABLE = False
      cloudscraper = None
  ```

### Type Hints
- All function parameters and return types must have type hints
- Use `Optional[T]` for nullable return types
- Use `Union[str, float, ...]` for multiple possible types
- Example:
  ```python
  def clean_price_string(price_str: str) -> Optional[float]:
      ...
  def parse_fuel_data(html_content: str, fuel_type: str) -> List[Dict[str, Union[str, float]]]:
      ...
  ```

### Formatting
- Use 4 spaces for indentation (not tabs)
- Maximum line length: follow standard Python conventions (~88-100 characters)
- Use docstrings for all functions and classes (Google style or similar)

### Error Handling
- **HTTP requests:** Use retry with exponential backoff (3 retries) via `requests.Session` + `urllib3.Retry`
- **Parsing failures:** Log warnings and skip individual entries, do not crash entire scrape
- **Critical failures:** Raise custom exceptions (e.g., `ExtractionError`) and exit non-zero
- **Logging:** Always log errors with context; use `exc_info=True` for exceptions:
  ```python
  logging.error("Error fetching %s: %s", url, e, exc_info=True)
  ```

### Data Formats
- **Timestamps:** ISO 8601 with IST offset (`YYYY-MM-DDTHH:MM:SS+05:30`)
- **Prices:** Floats only, never strings (`102.50` not `"102.50"`)
- **Encoding:** UTF-8 for all file I/O
- **JSON:** `indent=2, ensure_ascii=False` when writing

### Constants
Define URL patterns, user agents, timeouts, and CSS selectors at module level:
```python
PETROL_URL = "https://www.goodreturns.in/petrol-price.html"
REQUEST_TIMEOUT = 30
CSS_SELECTOR_ROW = "tr"
```

### Testing
- Use `pytest` for all tests
- Create fixtures in `tests/conftest.py` for shared test data
- Mock HTTP requests using `requests_mock` in unit tests
- Test both success and error paths
- Test edge cases (empty tables, missing fields, malformed data)
- Test functions must have descriptive names beginning with `test_`

### Critical Data Integrity Rules
- **Never overwrite prices.json with incomplete/empty data** - the fail-safe mechanism preserves previous valid data
- Script exits non-zero on critical failures to prevent bad commits
- Validate scraped data before saving (minimum threshold checks)

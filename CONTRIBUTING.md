# Contributing to OpenFuel

Thank you for your interest in contributing to OpenFuel! This guide will help you get started.

## Table of Contents

- [Ways to Contribute](#ways-to-contribute)
- [Contribution Workflow](#contribution-workflow)
- [Setting Up Local Development](#setting-up-local-development)
- [Adding a New Data Source](#adding-a-new-data-source)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Pull Request Guidelines](#pull-request-guidelines)

---

## Ways to Contribute

### High Priority (Phase 1)
- **Find new data sources** for more Indian cities
- **Implement scrapers** for approved sources

### Other Contributions
- Add CNG/LPG data sources (Phase 2)
- Improve documentation
- Fix bugs
- Add tests
- Review pull requests

Check the [ROADMAP.md](./ROADMAP.md) to see current priorities.

---

## Contribution Workflow

### For New Features or Data Sources

```
1. Open Issue          →  Discuss your idea before coding
2. Get Approval        →  Wait for maintainer feedback
3. Fork & Branch       →  Create a feature branch
4. Implement           →  Write code + tests
5. Test Locally        →  Run pytest, use --dry-run
6. Submit PR           →  Reference the issue
7. Review & Merge      →  Address feedback
```

**Why issue first?**
- Prevents duplicate work
- Ensures the source/feature fits the project
- Gets early feedback on approach

### For Bug Fixes

Small, obvious bug fixes can go directly to PR. For larger bugs, open an issue first.

---

## Setting Up Local Development

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (package manager)

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/OpenFuel.git
cd OpenFuel

# Install dependencies
uv sync
```

### Running the Scraper

```bash
# Run full scrape (updates prices.json)
uv run python main.py

# Dry run - test without modifying prices.json (coming soon)
uv run python main.py --dry-run
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_scraper.py

# Run specific test with verbose output
uv run pytest tests/test_scraper.py::test_function_name -v
```

---

## Adding a New Data Source

This is currently our highest priority contribution.

### Step 1: Find a Source

Look for websites that:
- List daily fuel prices for Indian cities
- Update regularly (daily)
- Cover cities not already in our dataset
- Are publicly accessible

### Step 2: Open an Issue

Use the "New Data Source" issue template and include:
- Source URL
- What data it provides (cities, fuel types)
- How often it updates
- Sample of the data format

### Step 3: Implement the Scraper

Once approved, create your scraper in `src/`:

```python
# src/scrapers/your_source.py

from typing import List, Dict, Union
from bs4 import BeautifulSoup

def parse_your_source(html_content: str) -> List[Dict[str, Union[str, float]]]:
    """
    Parse fuel prices from your source.

    Returns:
        List of dicts: [{"city": "City Name", "price": 99.99}, ...]
    """
    soup = BeautifulSoup(html_content, "html.parser")
    # Your parsing logic here
    ...
```

### Step 4: Handle Errors Gracefully

```python
# DO: Log and skip bad entries
if price_val is None:
    logging.warning(f"Could not parse price for {city}")
    continue

# DON'T: Let one bad entry crash everything
# price = float(price_text)  # Will crash on invalid input
```

### Step 5: Add Tests

Create tests in `tests/` with sample HTML:

```python
# tests/test_your_source.py

def test_parse_your_source_valid_html():
    html = """<table>...</table>"""
    result = parse_your_source(html)
    assert len(result) > 0
    assert "city" in result[0]
    assert "price" in result[0]
```

---

## Code Standards

### Python Style

- **Functions/variables**: `snake_case`
- **Classes**: `CamelCase`
- **Constants**: `UPPER_CASE`
- **Files**: `snake_case.py`

### JSON Keys

- Always use `snake_case`
- Prices are floats, not strings: `102.50` not `"102.50"`
- Timestamps in ISO 8601 with IST: `2025-01-08T06:30:00+05:30`

### Error Handling

```python
# Use retry for HTTP requests (already configured in get_request_session)
# Log errors, don't silently ignore them
# Individual parse failures should not crash the entire scrape
```

### Logging

```python
import logging

logging.info("Fetching data from %s", url)
logging.warning("Could not parse price for %s", city)
logging.error("Critical failure: %s", error)
```

---

## Testing

### What to Test

- Parsing logic with valid HTML
- Parsing logic with malformed HTML (should not crash)
- Edge cases (empty tables, missing fields)
- Price string cleaning

### Running Tests

```bash
# All tests
uv run pytest

# Specific test
uv run pytest tests/test_scraper.py::test_parse_fuel_data -v
```

### Test Files Structure

```
tests/
├── test_scraper.py              # Unit tests for main scraper
├── test_scraper_integration.py  # Integration tests
├── test_utils.py                # Tests for utility functions
└── conftest.py                  # Shared fixtures
```

---

## Pull Request Guidelines

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] Tests pass locally (`uv run pytest`)
- [ ] New code has tests
- [ ] Commit messages are clear and descriptive

### PR Title Format

```
feat: Add scraper for newssource.com
fix: Handle missing price field in goodreturns parser
docs: Add API usage examples
test: Add edge case tests for price cleaning
```

### PR Description

- Reference the related issue: `Closes #123`
- Explain what changed and why
- Note any breaking changes
- Include testing steps if applicable

### Review Process

1. Maintainers will review within a few days
2. Address any feedback
3. Once approved, maintainer will merge

---

## Questions?

- Open a [GitHub Issue](https://github.com/SHN2004/OpenFuel/issues) for bugs or features
- Check existing issues before creating new ones
- Be patient - maintainers are volunteers

Thank you for contributing!

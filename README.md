# OpenFuel

**Serverless, zero-cost, real-time fuel price API for India.**

OpenFuel is a "Git Scraping" project that automatically fetches daily petrol and diesel prices from `goodreturns.in`, cleans the data, and serves it as a static JSON API. It runs entirely on GitHub Actions, providing a high-availability, self-updating database without the need for traditional server infrastructure.

---

## Features

- **Daily Updates:** Automatically scrapes prices every morning at 06:30 AM IST.
- **Cost-Efficiency:** Zero operational costs, leveraging GitHub's free tier for compute and storage.
- **High Availability:** Served via GitHub's global content delivery network (CDN).
- **Reliability:** Includes fail-safe mechanisms to ensure data integrity and prevent overwrite on failure.
- **Developer-Friendly:** Standard JSON format with ISO 8601 timestamps for seamless integration.
- **Open Data:** Publicly accessible and free for all users.

## API Usage

Access the latest fuel prices directly via the raw GitHub URL.

**Endpoint:**
```
GET https://raw.githubusercontent.com/SHN2004/OpenFuel/main/prices.json
```

**Response Schema:**
```json
{
  "meta": {
    "source": "GoodReturns",
    "currency": "INR",
    "last_updated_ist": "2025-12-06T06:30:00+05:30",
    "version": "1.0"
  },
  "data": [
    {
      "state": "Karnataka",
      "city": "Bengaluru",
      "aliases": ["Bangalore"],
      "petrol_price": 101.23,
      "diesel_price": 87.10
    }
  ]
}
```

## How It Works

1.  **Scheduled Execution:** A GitHub Actions workflow triggers daily based on a cron schedule.
2.  **Data Extraction:** A Python-based scraper fetches current prices from source providers.
3.  **Data Processing:** Extracted data is cleaned, normalized, and merged into a structured format.
4.  **Versioned Storage:** If changes are detected, the updated dataset is committed to the repository.

## Local Development

Guidelines for setting up the project in a local environment.

### Prerequisites

- Python 3.11 or higher
- **uv** (Mandatory for dependency management)

### Installing uv

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

For other methods, refer to the [official uv documentation](https://github.com/astral-sh/uv).

### Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/SHN2004/OpenFuel.git
    cd OpenFuel
    ```

2.  **Install dependencies:**
    ```bash
    uv sync
    ```

### Running the Scraper

To execute the scraping logic locally:

```bash
uv run python src/scraper.py
```

### Running Tests

Execute the test suite using `pytest`:

```bash
uv run pytest
```

## Contributing

Contributions are welcome and appreciated.

1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/new-feature`).
3.  Commit your changes (`git commit -m 'Implement new feature'`).
4.  Push to the branch (`git push origin feature/new-feature`).
5.  Submit a Pull Request.

**Guidelines:**
- Adhere to the project's coding standards.
- Ensure backward compatibility for the `prices.json` schema.
- Include unit tests for any new functionality.

## License

This project is open-source and available under the MIT License.

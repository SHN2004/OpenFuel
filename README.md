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
  "last_updated_ist": "2025-12-25T12:34:57.438675+05:30",
  "petrol": [
    {
      "city": "New Delhi",
      "price": 94.77
    }
  ],
  "diesel": [
    {
      "city": "New Delhi",
      "price": 87.67
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

## Roadmap

We're actively expanding OpenFuel! Current priorities:

1. **More Cities** - Expand from ~50 to 200+ Indian cities
2. **CNG/LPG Support** - Add more fuel types
3. **API Versioning** - Multiple endpoints, per-city queries
4. **Documentation** - API docs and contributor guides
5. **Historical Data** - Price trends and history

See [ROADMAP.md](./ROADMAP.md) for the full plan.

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](./CONTRIBUTING.md) for the full guide.

**Quick start:**
1. Check [open issues](https://github.com/SHN2004/OpenFuel/issues) for tasks
2. Open an issue before starting major work
3. Fork, branch, code, test, PR

**Top priority:** Finding new data sources with more Indian cities.

## License

This project is open-source and available under the MIT License.

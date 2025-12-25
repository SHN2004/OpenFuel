# OpenFuel 🇮🇳

**Serverless, zero-cost, real-time fuel price API for India.**

OpenFuel is a "Git Scraping" project that automatically fetches daily petrol and diesel prices from `goodreturns.in`, cleans the data, and serves it as a static JSON API. It runs entirely on GitHub Actions, providing a high-availability, self-updating database without the need for traditional servers.

---

## 🚀 Features

- **Daily Updates:** Automatically scrapes prices every morning at 06:30 AM IST.
- **Zero Cost & High Availability:** Served via GitHub's raw content CDN.
- **Reliable:** Features fail-safe mechanisms to ensure broken scrapes don't overwrite valid data.
- **Developer Friendly:** Simple, standard JSON format with ISO 8601 timestamps.
- **Open Data:** Free for anyone to use.

## 🔌 API Usage

You can access the latest fuel prices directly via the raw GitHub URL.

**Endpoint:**
```
GET https://raw.githubusercontent.com/SHN2004/OpenFuel/refs/heads/main/prices.json
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
    // ...
  ]
}
```

## 🛠️ How It Works

1.  **Scheduled Trigger:** A GitHub Actions workflow (`.github/workflows/daily_scrape.yml`) triggers daily.
2.  **Scrape:** The Python script (`src/scraper.py`) fetches HTML from source websites.
3.  **Process:** Data is cleaned, normalized, and merged (Petrol + Diesel).
4.  **Commit:** If prices have changed, the new `prices.json` is committed back to the repository.

## 👨‍💻 Local Development

We welcome contributions! Here's how to set up the project locally.

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (Recommended) or `pip`

### Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/OpenFuel.git
    cd OpenFuel
    ```

2.  **Install dependencies:**
    ```bash
    uv sync
    # OR using pip
    # pip install -r requirements.txt
    ```

### Running the Scraper

To test the scraper logic locally:

```bash
uv run python src/scraper.py
```

This will generate/update `prices.json` in your local directory.

### Running Tests

We use `pytest` for testing. Ensure all tests pass before submitting a PR.

```bash
uv run pytest
```

## 🤝 Contributing

1.  Fork the repository.
2.  Create a new feature branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes (`git commit -m 'Add some amazing feature'`).
4.  Push to the branch (`git push origin feature/amazing-feature`).
5.  Open a Pull Request.

**Guidelines:**
- Follow the existing code style (standard Python `snake_case`).
- Ensure `prices.json` structure remains backward compatible unless intended otherwise.
- Add tests for new features.

## 📄 License

This project is open-source.

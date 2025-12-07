# Project Context: OpenFuel

## Overview
This document provides critical implementation rules and guidelines for AI agents working on the OpenFuel project. The goal is to ensure consistent, high-quality code generation that adheres to the project's specific architectural decisions and patterns.

## Project Summary
OpenFuel is a serverless, zero-cost real-time fuel price acquisition engine designed for the Indian market. It uses a "Git Scraping" architectural pattern, leveraging GitHub Actions as an ETL pipeline to scrape daily dynamic fuel prices, standardize the data, and commit it back to the repository. The GitHub repository itself serves as a high-availability, self-updating database.

## Technical Stack & Dependencies

### Primary Domain
- **Serverless Data Pipeline (Git Scraping)** using Python scripts executed by GitHub Actions.

### Key Technologies
- **Language:** Python 3.x
- **Scraping Libraries:** `requests`, `beautifulsoup4`
- **Automation/Orchestration:** GitHub Actions
- **Data Format:** JSON (flat file storage)
- **Testing:** Pytest

## Critical Implementation Rules for AI Agents

### 1. Naming Conventions

#### Python Code
- **Variables & Functions:** `snake_case` (e.g., `fetch_petrol_prices`, `process_city_data`).
- **Classes:** `CamelCase` (e.g., `FuelScraper`, `DataCleaner`).
- **Files:** `snake_case.py` (e.g., `scraper.py`, `utils.py`).
- **Constants:** `UPPER_CASE` (e.g., `PETROL_URL`, `DIESEL_URL`).

#### JSON Data
- **Keys:** `snake_case` (e.g., `last_updated_ist`, `petrol_price`, `diesel_price`).
  - **Reason:** Consistency with Python code and standard JSON practices.

### 2. Project Structure

- **Core Logic:** All primary Python scripts and modules reside in the `src/` directory.
- **Testing:** Unit and integration tests are placed in the `tests/` directory, mirroring the `src/` structure.
- **CI/CD:** GitHub Actions workflow definitions are in `.github/workflows/`.
- **Root Level:** Configuration files (`requirements.txt`), the data output (`prices.json`), and documentation (`README.md`).

### 3. Data Formats

- **Date/Time:** All timestamps MUST be in ISO 8601 format with the appropriate IST timezone offset (`YYYY-MM-DDTHH:MM:SS+05:30`).
  - **Reason:** Ensures clarity and proper handling of timezones, crucial for daily price updates.
- **Prices:** MUST be stored as floating-point numbers (e.g., `102.50`), NEVER as strings (e.g., `"102.50"`).
  - **Reason:** Enables direct numerical operations and avoids type conversion issues for consumers.
- **Encoding:** All text-based files, especially JSON output, MUST use **UTF-8** encoding.

### 4. Error Handling & Robustness

- **Network Errors:** Implement retry logic (e.g., 3 retries with exponential backoff) for HTTP requests to external sources.
- **Parsing Errors:** Individual data points (e.g., a single city's price) should be skipped/logged if parsing fails, rather than failing the entire scrape.
- **Critical Failure:** If the scraper encounters a structural change that prevents a significant portion (e.g., >50%) of data extraction, the script MUST exit with a non-zero status code (e.g., `exit(1)`).
- **Fail-Safe Mechanism:** The workflow MUST NEVER overwrite `prices.json` with incomplete, corrupted, or empty data if the scrape fails. The previous day's valid data should remain accessible.
- **Logging:** All errors, warnings, and significant operational messages MUST be logged to `stderr` or `stdout` for visibility in GitHub Actions logs.

### 5. GitHub Actions Workflow Specifics

- **Scheduling:** The primary workflow (`daily_scrape.yml`) MUST be scheduled to run daily at `06:30 AM IST` (which is `01:00 UTC`).
- **Commit Strategy:** The workflow MUST only commit changes to the repository if `prices.json` has genuinely changed. No empty commits.
- **Authentication:** Use the automatically provided `GITHUB_TOKEN` for repository write access within the workflow.

### 6. External Data Source Interactions

- **Target:** `https://www.goodreturns.in/petrol-price.html` and `https://www.goodreturns.in/diesel-price.html`.
- **Headers:** Implement a basic `User-Agent` header for HTTP requests to mimic a standard browser.

### 7. Client-Side Responsibilities

- **Fuzzy Matching:** Any logic for mapping user locations to the scraped city names is a CLIENT-SIDE responsibility. The backend provides raw city-based data.

## Anti-Patterns to Avoid

- **Hardcoding values:** Avoid hardcoding URLs, selectors, or other changeable parameters directly in the `scraper.py` if they can be externalized (e.g., as constants at the top of the file).
- **Ignoring errors:** Never use `try-except pass` for critical operations; always log errors and handle exceptions gracefully.
- **Inconsistent Naming:** Mixing `camelCase` and `snake_case` within the same context (e.g., JSON keys).
- **Direct database access:** No traditional database connections; the Git repository is the data store.
- **Overwriting data on failure:** Adhere strictly to the fail-safe mechanism for `prices.json`.

# OpenFuel Roadmap

This document outlines the development roadmap for OpenFuel. Contributors are encouraged to pick up issues from any phase - earlier phases are higher priority.

## Project Vision

Make OpenFuel the go-to open-source fuel price API for India - covering all major cities, multiple fuel types (petrol, diesel, CNG, LPG), with historical price trends and developer-friendly endpoints.

---

## Phase 1: Expand City Coverage (High Priority)

**Goal**: Expand from ~50 cities/states to 200+ cities across India.

### What We Need
- **New data sources** that cover more Indian cities
- Current source (goodreturns.in) mainly covers state capitals and metro cities
- Looking for sources that include tier-2 and tier-3 cities

### How to Contribute
1. Find a reliable website that lists daily fuel prices for Indian cities
2. Verify it updates daily and has consistent data
3. Open an issue using the "New Data Source" template
4. Once approved, implement the scraper following our contribution guide

### Acceptance Criteria
- Source must be publicly accessible
- Data should update daily
- Must cover cities not already in our dataset
- Scraper must handle errors gracefully

---

## Phase 2: CNG & LPG Support

**Goal**: Add CNG and LPG fuel prices alongside petrol and diesel.

### What We Need
- Reliable sources for CNG prices (city-wise)
- Reliable sources for LPG prices (domestic cylinder rates)
- Scraper implementations for these sources

### Schema Addition
```json
{
  "last_updated_ist": "...",
  "petrol": [...],
  "diesel": [...],
  "cng": [
    {"city": "New Delhi", "price": 76.59}
  ],
  "lpg": [
    {"city": "New Delhi", "price": 803.00, "cylinder_kg": 14.2}
  ]
}
```

### How to Contribute
1. Find a source for CNG or LPG prices
2. Open an issue to discuss the source and proposed schema
3. Implement after approval

---

## Phase 3: API Versioning & Multiple Endpoints

**Goal**: Provide flexible API endpoints for different use cases.

### Planned Endpoints
```
/v1/prices.json           # Full data (current format, backward compatible)
/v1/petrol.json            # Petrol prices only
/v1/diesel.json            # Diesel prices only
/v1/cng.json               # CNG prices only
/v1/lpg.json               # LPG prices only
/v1/cities/{city}.json     # All fuel prices for a specific city
/v1/states/{state}.json    # All cities in a state
```

### Additional Data Points
Once we have versioning, v2 can include:
- `price_change`: Daily change from yesterday (+/-₹)
- `state_tax`: VAT/tax breakdown if available
- `last_updated`: Per-entry timestamps

### Technical Considerations
- Generate static JSON files for all endpoints during scrape
- City names should be URL-friendly slugs (e.g., `new-delhi`, `mumbai`)
- Maintain canonical name mapping with aliases (Bangalore/Bengaluru, Bombay/Mumbai)

---

## Phase 4: Documentation

**Goal**: Comprehensive docs for users and contributors.

### User Documentation
- API reference with all endpoints
- Response schema documentation
- Code examples (curl, Python, JavaScript)
- Rate limiting policy (when implemented)
- Data accuracy disclaimer

### Contributor Documentation
- Architecture overview
- Adding a new data source (step-by-step)
- Testing guide
- Code style guide

### Implementation
- Docs site (GitHub Pages, Docusaurus, or similar)
- Keep docs in `/docs` folder in repo

---

## Phase 5: Historical Data & Trends

**Goal**: Enable price history queries and trend analysis.

### Data Storage
- Store daily snapshots in `/history/YYYY/MM/DD.json`
- Git repo serves as the database
- Retain at least 1 year of history

### Features
- Price trends over time (7-day, 30-day, 90-day)
- Percentage change calculations
- Highest/lowest prices in period
- City-wise historical comparisons

### Technical Considerations
- May require compute (Cloudflare Workers, Vercel Edge) for dynamic queries
- Alternative: Pre-generate common trend files during daily scrape
- Decision on infrastructure deferred until this phase

---

## Future Considerations

These are not prioritized yet but may be added later:

- **Rate Limiting**: API keys and usage limits if traffic demands
- **Multiple Fallback Sources**: Redundant scrapers for reliability
- **Client SDKs**: Official Python, JavaScript, Go libraries
- **Alerts/Webhooks**: Notify subscribers of price changes
- **Mobile App**: Reference implementation consuming the API
- **Fuel Station Data**: Locations, brands, amenities

---

## How Phases Work

- Phases are **not strictly sequential** - contributors can work on any phase
- Earlier phases are **higher priority** and should be completed first
- Each phase may have multiple parallel workstreams
- Major features require an issue discussion before implementation

---

## Current Status

| Phase | Status | Progress |
|-------|--------|----------|
| Phase 1: More Cities | **Active** | Looking for contributors |
| Phase 2: CNG/LPG | Open | Needs data sources |
| Phase 3: API Structure | Open | Design phase |
| Phase 4: Documentation | Open | Needs contributors |
| Phase 5: Historical Data | Planned | Not started |

---

## Get Involved

1. Check [open issues](https://github.com/SHN2004/OpenFuel/issues) for tasks
2. Read [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines
3. Join discussions on issues before starting work
4. Submit PRs following the contribution workflow

Questions? Open a discussion or issue!

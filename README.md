# Middle East Crisis Tracker

A production-minded single-service FastAPI application that ingests practical public sources, normalises events, clusters duplicates, scores confidence/materiality, and presents a calm, evidence-weighted dashboard.

## Why this design

This app deliberately prefers **clarity, resilience, and inspectable scoring** over opaque “AI magic”.

Key choices:

- **Single deployable service**: FastAPI serves both APIs and the frontend.
- **Deterministic scoring**: confidence and materiality are explicit and reviewable.
- **Graceful degradation**: each source can fail without taking down the app.
- **Aggressive deduplication**: articles are clustered into canonical event cards.
- **Operational relevance**: event cards explain what happened, why it matters, and what to watch next.

## Features

- Multi-source ingestion:
  - Google News RSS (search-based)
  - U.S. Treasury press releases
  - OFAC recent actions
  - UK sanctions list/collection page
  - White House briefings/statements
  - UKMTO recent incidents
  - UN Security Council RSS
  - Israel MFA press page
  - Gov.il PMO/FM news
  - Iran MFA statements
- Canonical event model with:
  - actors, countries, locations
  - event type
  - asset exposure tags
  - confidence/materiality/novelty scores
  - corroboration count
  - summary / why it matters / uncertainty
- Situation/regime summary
- Forward watchlist
- Source-health admin pages
- JSON/CSV export
- Tests for clustering, scoring, parser behaviour, and graceful failure

## Architecture

- `backend/app/main.py` bootstraps the application.
- `backend/app/sources/*` define fetchers/parsers.
- `backend/app/services/ingest_service.py` orchestrates ingestion and persistence.
- `backend/app/services/normalization.py` extracts entities and event attributes.
- `backend/app/services/scoring.py` computes deterministic scores.
- `backend/app/services/clustering.py` clusters near-duplicate events.
- `backend/app/services/situation.py` builds the top summary and watchlist.
- `backend/app/routers/*.py` expose dashboard and admin APIs.
- `backend/app/templates/` + `static/` render the frontend.

## Local run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt
uvicorn app.main:app --reload
```

Open:
- Dashboard: `http://127.0.0.1:8000/`
- Health: `http://127.0.0.1:8000/health`
- Admin status: `http://127.0.0.1:8000/admin/status`

## Environment variables

See `.env.example`.

Main ones:

- `APP_ENV`
- `APP_HOST`
- `APP_PORT`
- `APP_BASE_URL`
- `APP_ADMIN_TOKEN`
- `APP_DATABASE_URL`
- `APP_REFRESH_INTERVAL_MINUTES`
- `APP_SOURCE_TIMEOUT_SECONDS`
- `APP_FETCH_USER_AGENT`
- `APP_ENABLE_BACKGROUND_REFRESH`
- `APP_MAX_ITEMS_PER_SOURCE`
- `APP_EVENT_LOOKBACK_HOURS`
- `APP_SOURCE_ENABLED_OVERRIDES`
- `APP_EXPORT_DEFAULT_FORMAT`

## Render deployment

1. Create a new Render **Web Service** from the repo.
2. Runtime: Python
3. Pin Python to **3.12.13** using either the included `.python-version` file or:
   - `PYTHON_VERSION=3.12.13`
4. Build command:
   ```bash
   pip install -r requirements.txt
   ```
5. Start command:
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
   ```
6. Add env vars from `.env.example`.
7. Persistent disk is optional for SQLite. If you want persistence across deploys, mount a disk and set:
   - `APP_DATABASE_URL=sqlite:////var/data/mect.db`

This Python pin is included because some Render deployments currently default to Python 3.14, which can trigger a source build of `pydantic-core` and fail the build.

## Notes on sources

This repo uses a **practical default source stack** rather than a maximal one. It is intentionally biased toward:
- low friction
- official/institutional pages where available
- RSS where practical
- HTML-list parsers for sources without RSS
- source-by-source failure isolation

You can disable any source via `APP_SOURCE_ENABLED_OVERRIDES`.

Example:
```bash
APP_SOURCE_ENABLED_OVERRIDES=google_news_middle_east=1,ukmto_recent_incidents=1,whitehouse_briefings=0
```

## Deterministic scoring overview

### Confidence
Confidence score considers:
- source credibility tier
- corroboration by independent sources
- specificity signals
- recency
- official confirmation
- whether the item looks like direct reporting or commentary

### Materiality
Materiality score considers:
- event type
- actor significance
- shipping/oil/market exposure
- kinetic or sanctions/policy significance
- likelihood of short-term follow-on risk

### Novelty
Novelty score considers:
- similarity to recent canonical events
- freshness
- whether the event introduces materially new entities / locations

## Security / operations notes

- Admin write endpoints require `X-Admin-Token`.
- This is **not** a predictive trading engine and does **not** provide price forecasts.
- This is **not** a truth oracle. Confidence is an evidence-weighted operational heuristic.

## Tests

```bash
pytest backend/tests -q
```
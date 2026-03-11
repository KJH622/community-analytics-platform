# Market Signal Hub

Market Signal Hub is a modular analytics platform for:

- market and macro data collection
- market news aggregation
- community sentiment analytics
- political community and polling analytics
- dashboard and API serving

The project is split into two major domains:

- `Market`: economic indicators, news, community sentiment, dashboard
- `Politics`: political indicators, politician mentions, community mood, dashboard

## Architecture

### Backend

- `backend/app/api`: market API routes
- `backend/app/politics/api`: politics API routes
- `backend/app/models`: market SQLAlchemy models
- `backend/app/politics/models`: politics SQLAlchemy models
- `backend/app/collectors`: market collectors
- `backend/app/politics/collectors`: political connectors
- `backend/app/analytics`: market analytics
- `backend/app/politics/analytics`: political analytics
- `backend/app/services`: market services and seeding
- `backend/app/politics/services`: political queries and seeding

### Frontend

- `frontend/app/page.tsx`: Market dashboard
- `frontend/app/politics/page.tsx`: Politics dashboard
- `frontend/app/news/page.tsx`: News list
- `frontend/app/community/page.tsx`: Community list

## Compliance and Crawling

- Official APIs, RSS feeds, and public sources are preferred.
- Community crawling must respect `robots.txt`, site terms, rate limits, and legal constraints.
- Sources with unclear permissions should remain `disabled` connectors.
- The current repository includes mock and disabled connectors for sensitive community targets.

## Quick Start

### Option 1: Docker Compose

1. Copy environment files.

```powershell
Copy-Item .env.example .env
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.local.example frontend\.env.local
```

2. Start the full stack.

```powershell
docker compose up --build
```

3. Open:

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend health: [http://localhost:8000/health](http://localhost:8000/health)
- Politics dashboard API: [http://localhost:8000/api/v1/politics/dashboard](http://localhost:8000/api/v1/politics/dashboard)
- Market dashboard page: [http://localhost:3000](http://localhost:3000)
- Politics dashboard page: [http://localhost:3000/politics](http://localhost:3000/politics)

### Option 2: Local Development

#### 1. Start PostgreSQL

Use a local PostgreSQL instance and create database `market_signal_hub`.

Example connection:

- host: `localhost`
- port: `5432`
- user: `postgres`
- password: `postgres`
- database: `market_signal_hub`

#### 2. Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
Copy-Item .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Backend first-run notes:

- On startup, demo market data and demo politics data are seeded when `SEED_DEMO_DATA=true`
- The scheduler also starts automatically when `SCHEDULER_ENABLED=true`
- If you do not want scheduled jobs during local development, set `SCHEDULER_ENABLED=false`

#### 3. Frontend

```powershell
cd frontend
npm install
Copy-Item .env.local.example .env.local
npm run dev
```

Then open:

- Market dashboard: [http://localhost:3000](http://localhost:3000)
- Politics dashboard: [http://localhost:3000/politics](http://localhost:3000/politics)
- News page: [http://localhost:3000/news](http://localhost:3000/news)
- Community page: [http://localhost:3000/community](http://localhost:3000/community)

## First Run Checklist

After startup, confirm these pages in order:

1. Backend health returns JSON at `/health`
2. Market indicator API returns seeded data at `/api/v1/indicators/latest`
3. Politics API returns seeded data at `/api/v1/politics/dashboard`
4. Frontend root page renders the Market dashboard
5. Frontend `/politics` page renders the Politics dashboard

Example API checks:

```powershell
Invoke-WebRequest http://localhost:8000/health
Invoke-WebRequest http://localhost:8000/api/v1/indicators/latest
Invoke-WebRequest http://localhost:8000/api/v1/politics/dashboard
```

## Environment Variables

### Root `.env`

Used by Docker Compose.

### Backend `backend/.env`

- `DATABASE_URL`
- `SCHEDULER_ENABLED`
- `SEED_DEMO_DATA`
- `CORS_ORIGINS`
- `FRED_API_KEY`
- `OPENAI_API_KEY`

### Frontend `frontend/.env.local`

- `NEXT_PUBLIC_API_BASE_URL`

## Database Migrations

```powershell
cd backend
alembic upgrade head
```

Current revisions:

- `0001_initial`: market domain schema
- `0002_politics`: politics domain schema

## Seed Data

When `SEED_DEMO_DATA=true`, the backend seeds:

- market indicators and articles
- community seed posts
- political parties, politicians, polling indicators
- political community references
- mock political community posts

## API Summary

### Market APIs

- `GET /health`
- `GET /api/v1/indicators/latest`
- `GET /api/v1/indicators/{indicator_code}/history`
- `GET /api/v1/news`
- `GET /api/v1/news/{id}`
- `GET /api/v1/community/posts`
- `GET /api/v1/community/posts/{id}`
- `GET /api/v1/analytics/daily-sentiment`
- `GET /api/v1/analytics/keyword-trends`
- `GET /api/v1/analytics/topic-breakdown`
- `POST /api/v1/jobs/run/{job_name}`

### Politics APIs

- `GET /api/v1/politics/dashboard`
- `GET /api/v1/politics/politicians`
- `GET /api/v1/politics/politicians/{name}`
- `GET /api/v1/politics/indicators`
- `GET /api/v1/politics/keywords`
- `GET /api/v1/politics/community-posts`
- `GET /api/v1/politics/sentiment`
- `GET /api/v1/politics/polarization`

## Tests

```powershell
cd backend
pytest
```

## Troubleshooting

### Database connection failed

Check:

- PostgreSQL is running
- `DATABASE_URL` points to the correct host and port
- the `market_signal_hub` database exists

If using Docker Compose, the backend should use:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/market_signal_hub
```

If using local PostgreSQL, use:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/market_signal_hub
```

### Frontend cannot reach backend

Check `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Then restart `npm run dev`.

### Alembic migration failed

Run:

```powershell
cd backend
alembic current
alembic upgrade head
```

If you already have a partially created database from an earlier broken run, drop the DB and recreate it for the cleanest MVP setup.

### Tests do not run

Install backend dev dependencies:

```powershell
cd backend
pip install -e .[dev]
pytest
```

### Python version warnings

Tests currently pass on the machine even with Python `3.14`, but a few third-party packages emit compatibility warnings.

Recommended local Python version:

- `3.11`
- `3.12`

## Demo Data Included

The seeded MVP includes:

- market indicators: CPI, USD/KRW
- market documents: sample article and sample community post
- political entities: sample parties and politicians
- political indicators: president approval, party support, national performance
- political posts: mock political community posts
- political reference communities: mock plus disabled real-world candidates

## OpenAI Key Usage

`OPENAI_API_KEY` is for analysis workloads only, such as:

- LLM-based summarization
- sentiment classification upgrades
- topic extraction upgrades
- moderation or labeling helpers

It does **not** grant access to third-party community posts.

To collect community posts legally, you still need one of:

- an official API from the community provider
- a public RSS or public feed
- a terms-compliant public HTML path that is allowed by `robots.txt`

Never commit API keys into the repository. Store them only in `.env`.

If a key has been pasted into chat or logged accidentally, rotate it immediately.

## Suggested Dev Workflow

For daily development:

1. Start PostgreSQL
2. Start backend with `uvicorn`
3. Start frontend with `npm run dev`
4. Run `pytest` after backend changes
5. Run `POST /api/v1/jobs/run/{job_name}` to refresh market jobs manually

Useful job names:

- `collect_indicators`
- `collect_news`
- `collect_community`
- `refresh_snapshots`

Example:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/v1/jobs/run/collect_news
```

## Adding a New Connector

### Market community connector

1. Add a class under `backend/app/collectors/communities/`
2. Inherit from `BaseCommunityConnector`
3. Implement:
   - `fetch_board_metadata`
   - `fetch_posts_page`
   - `fetch_post_detail`
   - `parse_post`
   - `normalize_post`
4. Register it in the ingestion service only after compliance review

### Political community connector

1. Add a class under `backend/app/politics/collectors/`
2. Inherit from `BasePoliticalCommunityConnector`
3. Keep it `disabled` or `mock` unless robots and terms are cleared
4. Add source metadata into `political_community_sources`

## Known MVP Limits

- PostgreSQL full text search is not fully wired yet
- Docker setup targets local development convenience over production hardening
- Some community sources are represented as disabled references only
- Frontend filtering UI is placeholder-only for now
- Political community source ingestion is mock-first and compliance-gated by design
- The politics dashboard currently uses seeded polling-style data rather than live polling feeds
- Several Korean community candidates currently remain disabled because public access policy is unclear or restrictive

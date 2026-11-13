# CYAI Club Assistant Agent

An AI-powered assistant built for a college Cybersecurity & AI club to automate the discovery, curation, and distribution of career opportunities, scholarships, and club communications — so student leaders can spend less time searching and more time building community.

## What It Does

The agent continuously discovers and curates real, current opportunities relevant to undergraduate students in cybersecurity and AI, then turns that data into ready-to-use newsletters and social content — all reviewed by a human before anything goes out.

### Core Features

**Opportunity Aggregation**
- Live CTF competition tracking (CTFtime)
- Entry-level job and internship sourcing (Adzuna), filtered specifically for students with no professional experience
- AI-assisted discovery of scholarships, fellowships, tech-prep programs, and residency programs (Tavily search + Mistral AI extraction and validation)
- Automatic dead-link detection and cleanup
- Automatic removal of opportunities past their deadline

**Newsletter Generation**
- AI-drafted monthly newsletters matching the club's real editorial voice
- Avoids repeating the same opportunities across consecutive newsletters
- Full review-and-edit workflow before anything is sent
- Branded PDF export with QR codes linking directly to each opportunity

**Social Media Content**
- Auto-generated CircleIn and Instagram post drafts from any opportunity or event
- Manual "write your own" option for fully custom posts
- Every post is a draft — nothing posts automatically

**Club Operations**
- Event management with photo/flyer uploads
- Member list management with self-serve unsubscribe
- CSV export for backups and reporting
- System health dashboard for monitoring integrations

**Automation, With Guardrails**
- Scheduled background sync for fresh opportunities (daily) and AI-powered searches (weekly)
- All content generation stops short of the final send/post — a human always reviews before anything reaches real people

## How It's Built

**Backend:** FastAPI (Python), PostgreSQL (hosted on Supabase), SQLAlchemy ORM, APScheduler for background jobs, Playwright for PDF rendering, rate limiting and API-key authentication throughout.

**Frontend:** React + Vite + Tailwind CSS, a custom dashboard for club officers to manage everything the agent tracks.

**AI Integrations:** Mistral AI for content generation and extraction, Tavily for web search.

## Setup and Deployment

### Deploy on Render (Blueprint)

Everything Render needs is in [`render.yaml`](render.yaml): the backend web service (`backend/`) and the website static site (`frontend/`). No secret values are stored in the file.

1. Prepare the values first and keep them in the officers' password vault: the Supabase connection string, and two random values from `openssl rand -hex 32` (one for the API key, one for the token secret).
2. In Render, connect the `york-cyai` GitHub organization, then choose **New → Blueprint**, pick this repo and the `main` branch.
3. Fill in the prompted values. `AGENT_API_KEY` (backend) and `VITE_API_KEY` (website) must be **the same value**. Set `ALLOWED_ORIGINS` to the website's address and `VITE_API_BASE_URL` to the backend's address (both start with `https://`, no slash at the end). Gmail and AI keys can be left blank and added later.
4. Click **Apply**. Afterwards, check both services' real addresses; if Render added a suffix, correct `ALLOWED_ORIGINS` and `VITE_API_BASE_URL`, then redeploy the website with **Manual Deploy → Clear build cache & deploy** (the website reads its variables only when it is built).

Render only asks for `sync: false` values when the Blueprint is first created. To change one later, edit it on the service's **Environment** page.

### Configuration

All backend settings are listed in [`backend/.env.example`](backend/.env.example).

| Variable | Notes |
|---|---|
| `DATABASE_URL`, `AGENT_API_KEY`, `TOKEN_SECRET_KEY` | **Required on Render.** If any is missing or a placeholder, the backend refuses to start and its log shows `STARTUP ERROR` naming the variable. |
| `ALLOWED_ORIGINS` | Extra website addresses allowed to call the API, comma-separated. Added to the defaults in `backend/app/config.py`. Change this whenever the website address changes. |
| `APP_ENV` | Leave unset locally. Render is treated as production automatically. |
| `GMAIL_*` | Newsletter sending. To renew the token, see [`GMAIL_TOKEN_RENEWAL.md`](GMAIL_TOKEN_RENEWAL.md). |
| `MISTRAL_API_KEY`, `TAVILY_API_KEY`, `ADZUNA_APP_ID`, `ADZUNA_API_KEY` | AI drafting, web search and job listings. `GEMINI_API_KEY` is optional; the current code does not use it. |

The website's `VITE_API_KEY` is built into its public JavaScript, so anyone with the website address can use the app. Do not post the address publicly.

### Run locally

Requires **Python 3.11+** and Node.js.

```sh
# Backend (run from the backend folder)
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
playwright install chromium        # needed for newsletter PDFs
cp .env.example .env               # then fill in values; the SQLite default is fine locally
uvicorn app.main:app --reload      # http://localhost:8000

# Website (in a second terminal)
cd frontend
printf 'VITE_API_BASE_URL=http://localhost:8000\nVITE_API_KEY=<same as AGENT_API_KEY in backend/.env>\n' > .env
npm install && npm run dev         # http://localhost:5173
```

### Tests

```sh
cd backend && python -m pytest
```

The tests use a temporary SQLite database and a fake API key, and refuse to run against any other database, so they never touch real data.

## Project History

This project started as a fully local tool — a FastAPI backend and React frontend running entirely on a laptop, used to prototype and validate the core workflows (sourcing, newsletter generation, member management). Once the feature set was proven out, the project was migrated to a cloud-hosted architecture: the database moved to a managed PostgreSQL instance, and the backend and frontend were deployed as separate always-on web services — making the tool accessible to the full club leadership team from any device, without requiring anyone to run code locally.

## Security

- API-key authentication on all administrative endpoints
- Rate limiting on all AI-powered and external-API-calling endpoints
- Automated link validation before any URL is surfaced to members
- No credentials or member data committed to source control
- Content generation and sending are strictly separated — no automated system sends anything to real people without human review

## Status

Actively maintained and used in production by club leadership for opportunity sourcing, monthly newsletters, and event coordination.

## Credits

Designed and built by Maheen Bilal ([@maheenb-04](https://github.com/maheenb-04)), CYAI president 2026, and handed over to the club's officers in November 2026. Now maintained by the CYAI officer team in the [`york-cyai`](https://github.com/york-cyai) organization.

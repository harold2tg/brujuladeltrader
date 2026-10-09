# La Brújula del Trader

> Professional statistical analysis platform for XAUUSD (Gold) traders. Connect your real cTrader account, automatically import your trades, and improve your strategy with AI analysis.

---

## Table of Contents

1. [What is this?](#what-is-this)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [cTrader Setup](#ctrader-setup)
5. [Quick Start](#quick-start)
6. [Environment Variables](#environment-variables)
7. [How to Use](#how-to-use)
8. [Ports & Services](#ports--services)
9. [Useful Commands](#useful-commands)
10. [Troubleshooting](#troubleshooting)
11. [Project Structure](#project-structure)
12. [License](#license)

---

## What is this?

```
┌─────────────────────────────────────────────────────────┐
│                    YOUR BROWSER                         │
│                  http://localhost:3001                   │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │   Dashboard  │  │ Data Sources │  │  AI Engine    │  │
│  │  Real-time   │  │ cTrader OAuth│  │  Analysis     │  │
│  │  metrics     │  │ Auto Import  │  │  Claude/GPT/  │  │
│  │              │  │ (no files!)  │  │  Gemini       │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              cTrader Connection (OAuth2)                │
│         Automatic sync of real trades                   │
│    (no manual CSV uploads)                              │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   API (FastAPI)                         │
│                  http://localhost:8001                   │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │   Auth   │  │Data      │  │ AI Engine│  │cTrader │  │
│  │  JWT +   │  │Sources   │  │ Trade    │  │ OAuth2 │  │
│  │  bcrypt  │  │Import    │  │ Analysis │  │ Auto-  │  │
│  │          │  │Automatic │  │ Trades   │  │ Import │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘  │
├─────────────────────────────────────────────────────────┤
│              PostgreSQL (port 5433)                     │
│              Redis (port 6379)                          │
└─────────────────────────────────────────────────────────┘
```

### How it works

**Before:** Upload CSV file → Wait for processing → See data  
**Now:** Click "Connect with cTrader" → Login → Your real trades imported automatically ✅

---

## Architecture

| Module | Description |
|--------|-------------|
| **Auth** | JWT login, registration, refresh tokens |
| **DataSources** | Unified model for importing data from multiple brokers |
| **cTrader** | Automatic OAuth2 to import trades from real accounts |
| **Analytics** | Stats by hour, day, month, session, streaks |
| **AI Engine** | Analysis with Claude, GPT-4, Gemini (optional) |
| **Alerts** | Configurable trade alerts |
| **Reports** | Monthly/yearly PDF/CSV export |

### Data import flow

```
User clicks "Connect with cTrader"
    ↓
Popup opens https://id.ctrader.com/my/settings/openapi/grantingaccess/
    ↓
User logs in with their cTrader account (FxPro, Pepperstone, etc.)
    ↓
User selects which accounts to authorize (Live/Demo)
    ↓
Backend receives code → exchanges for access_token + refresh_token
    ↓
Backend discovers accounts with get_accounts() → detects LIVE or DEMO
    ↓
Credentials stored (AES-256-GCM encrypted in DB)
    ↓
Sync button → imports all closed trades from that account
    ↓
Trades stored in 'trades' table with data_source_id as FK
    ↓
Dashboard shows calculated metrics from imported trades
```

---

## Prerequisites

| Requirement | Min Version | Verify |
|-----------|----------------|----------------|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | v24+ | `docker --version` |
| Git | Any | `git --version` |

> You only need Docker. No need to install Node.js or Python on your machine.

---

## cTrader Setup

You need to register a cTrader Open API app. It's **free**.

### Step 1: Create app at cTrader Open API

1. Go to: **https://openapi.ctrader.com/apps**
2. Login with your cTrader account (or create one free)
3. Click **"Create New App"**
4. Fill out:
   - **App Name**: `La Brújula del Trader` (or whatever you like)
   - **Redirect URI**: `http://localhost:8001/ctrader/callback` ⚠️ Exactly this, no trailing slash
   - **App Type**: `Web App`
5. Save the **Client ID** and **Client Secret**

### Step 2: Configure account access

In your cTrader platform (Desktop/Web):
1. Go to **Settings → API Trading**
2. Enable the accounts you want to sync
3. Note the account numbers (e.g., `1320323`)

---

## Quick Start

### 1. Clone repository

```bash
git clone https://github.com/harold2tg/brujuladeltrader.git
cd brujuladeltrader
```

### 2. Configure backend environment

```bash
cp Bakend-bdt/.env.example Bakend-bdt/.env
```

Edit `Bakend-bdt/.env` and fill these fields:

```bash
APP_SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

CTRADER_CLIENT_ID=your_client_id_here
CTRADER_CLIENT_SECRET=your_client_secret_here
```

Generate the secrets with the commands above (auto-generated by openssl/python).

### 3. Configure frontend

The `.env.local` already comes with correct config for Docker:

```bash
# Just verify it exists
ls frontend-bdt/.env.local || cp frontend-bdt/.env.local.example frontend-bdt/.env.local
```

### 4. Run migrations and start

```bash
# Build and start containers
docker compose -f docker-compose.dev.yml up -d

# Run database migrations
docker compose -f docker-compose.dev.yml exec api alembic upgrade head
```

### 5. Open the app

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3001 |
| **API Docs** | http://localhost:8001/docs |

### 6. Login

Use the email/password you registered (or create one new from the frontend).

### 7. Connect cTrader

1. Go to **http://localhost:3001/ctrader**
2. Click **"Conectar con cTrader"**
3. A popup opens with cTrader login
4. Login and authorize your accounts
5. Done! You can now click **"Synchronize"** to import your real trades

---

## Environment Variables

### `Bakend-bdt/.env`

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_SECRET_KEY` | ✅ | - | App secret key (min 32 hex chars) |
| `DATABASE_URL` | ✅ | - | PostgreSQL async (use Docker service names) |
| `REDIS_URL` | ✅ | `redis://redis:6379/0` | Redis URL |
| `JWT_SECRET_KEY` | ✅ | - | Secret for signing JWTs |
| `ENCRYPTION_KEY` | ✅ | - | AES-256 key for encrypting credentials |
| `CTRADER_CLIENT_ID` | ✅* | - | Your cTrader app Client ID *(see section below)* |
| `CTRADER_CLIENT_SECRET` | ✅* | - | Your cTrader app Client Secret |
| `CTRADER_REDIRECT_URI` | ❌ | `http://localhost:8001/ctrader/callback` | OAuth2 callback URI |
| `CORS_ORIGINS` | ❌ | `http://localhost:3000,...` | Allowed origins |

### Development values (Docker):

```bash
DATABASE_URL=postgresql+asyncpg://brujula:brujula123@db:5432/brujula_db
REDIS_URL=redis://redis:6379/0
```

### `frontend-bdt/.env.local`

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8001` | Backend URL |

---

## How to use

### 1. Dashboard

Shows real-time metrics:
- Win Rate (% of winning trades)
- Net PnL (total gain/loss)
- R:R Ratio (Risk/Reward)
- Equity Curve charts, monthly PnL, sessions

### 2. Data Sources

Manage your broker connections:
- **Connect**: Click button → cTrader popup → authorization → automatic sync
- **Sync**: Pull all closed trades from your account
- **View**: List of connected sources with status (idle/syncing/error)

### 3. Analytics

Detailed breakdown by dimension:
- By hour of day (london_open, ny_overlap, ny_session, off_hours)
- By day of week
- By month/year
- Result distribution (histogram)
- Streaks (winning/losing consecutive trades)
- Simulations (fixed stop loss, best hours)

### 4. Alerts

Configure automatic rules:
- Max loss per trade ($)
- Losing streak
- Daily loss limit

### 5. Reports

Export monthly/yearly performance as PDF or CSV.

### 6. AI Engine

Automated analysis using language models (requires Anthropic/OpenAI/Gemini/Ollama API key).

---

## Ports & Services

| Service | External Port | Internal | Description |
|---------|---------------|----------|-------------|
| Frontend (Next.js) | **3001** | 3000 | Web app |
| API (FastAPI) | **8001** | 8000 | Backend + Swagger docs |
| PostgreSQL | **5433** | 5432 | Database |
| Redis | **6379** | 6379 | Cache + queues |

External ports are mapped to avoid conflicts with other local projects.

---

## Useful Commands

```bash
# View backend logs
docker compose -f docker-compose.dev.yml logs -f api

# View frontend logs
docker compose -f docker-compose.dev.yml logs -f web

# Restart only the API
docker compose -f docker-compose.dev.yml restart api

# Rebuild with modified Dockerfile
docker compose -f docker-compose.dev.yml up -d --build

# Open DB console
docker compose -f docker-compose.dev.yml exec db psql -U brujula -d brujula_db

# Stop everything
docker compose -f docker-compose.dev.yml down

# Full reset (removes volumes)
docker compose -f docker-compose.dev.yml down -v
```

---

## Troubleshooting

### Error "Application authentication failed: Provided application does not contain provided URI"

1. Verify that in https://openapi.ctrader.com/apps your Redirect URI is EXACTLY: `http://localhost:8001/ctrader/callback`
2. No trailing `/`
3. Using `http://` (not `https://`)
4. You saved the changes in cTrader before trying to connect

### Graphs appear empty after connecting

1. Confirm you clicked **"Synchronize"** after connecting
2. If it synced and still empty, check browser console (F12) for errors
3. Retry: disconnect → reconnect → sync

### cTrader says "No accounts found"

1. Verify you enabled accounts in Settings → API Trading on your cTrader platform
2. The access token must have read permissions for those accounts

### "Missing authorization token" when loading page

Verify you have a user created in the database:
```bash
docker compose -f docker-compose.dev.yml exec db psql -U brujula -d brujula_db -c "SELECT email FROM users;"
```

If no users, register at http://localhost:3001/register

### CORS errors in frontend

Verify `CORS_ORIGINS` in `.env` includes `http://localhost:3000` or `http://localhost:3001`.

### API doesn't start

```bash
# Check specific logs
docker compose -f docker-compose.dev.yml logs api

# If it says "relation does not exist":
docker compose -f docker-compose.dev.yml exec api alembic upgrade head
```

---

## Project Structure

```
brujuladeltrader/
├── Bakend-bdt/              # FastAPI Backend
│   ├── app/
│   │   ├── modules/
│   │   │   ├── auth/        # Login, JWT, registration
│   │   │   ├── ctrader/     # cTrader OAuth2 connection
│   │   │   ├── ai_engine/   # AI-powered analysis
│   │   │   ├── analytics/   # Statistics and calculations
│   │   │   ├── alerts/      # Trading alerts
│   │   │   ├── reports/     # Exportable reports
│   │   │   └── data_sources/# DataSource + Trade models
│   │   ├── config.py        # Central configuration
│   │   └── main.py          # Entry point
│   ├── .env.example         # Environment template
│   └── docker/Dockerfile.dev
├── frontend-bdt/            # Next.js 15 Frontend
│   ├── app/                 # App Router
│   ├── components/          # React components
│   ├── lib/                 # Utils, hooks, stores
│   └── messages/            # Translations (ES/EN)
├── scripts/                 # Utility scripts
├── openspec/                # SDD design documents
├── docker-compose.dev.yml   # Local development
├── docker-compose.prod.yml  # Production
└── LICENSE
```

> **Note:** The `parser/` and `uploads/` modules no longer exist. Data import is exclusively done via cTrader OAuth2. This makes it easy to add more brokers (MetaTrader, Binance, etc.) in the future — each will be a new provider creating a `DataSource`.

---

## License

This project is licensed under the [Apache License 2.0](LICENSE).

You are free to use, modify, and distribute this software, including commercial use, as long as you:
- Keep the copyright notice
- Indicate any changes you made
- Include the full license text

See [LICENSE](LICENSE) for details.

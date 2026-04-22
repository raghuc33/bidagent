# BidAgent — Azure Deployment Guide (MVP / Dev)

> **Goal**: deploy the MVP on Azure at the lowest possible cost so you can
> share a working URL with a handful of early customers.

---

## Architecture at a glance

```
┌──────────────────────────────────┐
│  Azure Static Web Apps (Free)    │  ← React SPA (frontend/)
│  https://bidagent-xxxx.azurestaticapps.net
└──────────────┬───────────────────┘
               │ /api/v1/*
               ▼
┌──────────────────────────────────┐
│  Azure App Service (B1 — $13/mo) │  ← FastAPI backend
│  https://bidagent-api.azurewebsites.net
│  ┌────────────┐  ┌─────────────┐ │
│  │ SQLite DB   │  │ ChromaDB    │ │
│  │ (file-based)│  │ (file-based)│ │
│  └────────────┘  └─────────────┘ │
└──────────────────────────────────┘
```

**Estimated monthly cost: ~$13 USD** (just the B1 App Service plan).
The frontend hosting on Static Web Apps Free tier is $0.

### Why this stack?

| Option considered | Monthly cost | Why we chose / skipped |
|---|---|---|
| **Static Web Apps Free** | $0 | Perfect for SPAs, global CDN, custom domain + SSL included |
| **App Service B1** | ~$13 | Always-on, 1.75 GB RAM, custom domain, SSH access, persistent disk |
| App Service F1 (Free) | $0 | Only 60 min compute/day, no custom domain SSL — too limited for demos |
| Container Apps (Consumption) | ~$0–5 | Scales to zero (cold starts ~10 s), trickier for persistent files |
| Azure Container Instances | ~$3–10 | No auto-restart, no built-in domain/SSL |
| Azure SQL / Cosmos DB | $5–25+ | Overkill — SQLite on disk is fine for MVP |

---

## Prerequisites

1. An Azure account ([free tier](https://azure.microsoft.com/free/) gives $200 credit for 30 days)
2. [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) installed
3. GitHub repo pushed (e.g. `github.com/gitmj/bidagent`)

```bash
# Login
az login

# Create a resource group (pick a region close to your customers)
az group create --name bidagent-rg --location uksouth
```

---

## Step 1 — Deploy the Backend (App Service)

### 1a. Create the App Service plan + web app

```bash
# B1 plan (~$13/mo) — use F1 for free tier testing (limited)
az appservice plan create \
  --name bidagent-plan \
  --resource-group bidagent-rg \
  --sku B1 \
  --is-linux

az webapp create \
  --name bidagent-api \
  --resource-group bidagent-rg \
  --plan bidagent-plan \
  --runtime "PYTHON:3.11"
```

### 1b. Configure environment variables

```bash
az webapp config appsettings set \
  --name bidagent-api \
  --resource-group bidagent-rg \
  --settings \
    LLM_API_KEY="your-gemini-api-key" \
    LLM_MODEL="gemini-2.0-flash" \
    LLM_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai" \
    JWT_SECRET="$(openssl rand -hex 32)" \
    DATABASE_URL="sqlite:///./bidagent.db" \
    CHROMA_PERSIST_DIR="/home/chroma_data" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true"
```

> **Note**: `/home` is the only persistent directory on App Service Linux.
> SQLite and ChromaDB data stored there survive restarts.

### 1c. Configure the startup command

```bash
az webapp config set \
  --name bidagent-api \
  --resource-group bidagent-rg \
  --startup-file "gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 120"
```

### 1d. Deploy from GitHub

```bash
# Option A: Deploy with GitHub Actions (recommended)
az webapp deployment github-actions add \
  --name bidagent-api \
  --resource-group bidagent-rg \
  --repo "gitmj/bidagent" \
  --branch main

# Option B: Quick zip deploy from local machine
cd backend
zip -r ../deploy.zip . -x "*.pyc" "__pycache__/*" "chroma_data/*" "*.db"
az webapp deploy \
  --name bidagent-api \
  --resource-group bidagent-rg \
  --src-path ../deploy.zip \
  --type zip
```

### 1e. Verify the backend

```bash
curl https://bidagent-api.azurewebsites.net/health
# Expected: {"status": "ok"}
```

---

## Step 2 — Deploy the Frontend (Static Web Apps)

### 2a. Create the Static Web App

The easiest path is to connect it to your GitHub repo directly.

```bash
az staticwebapp create \
  --name bidagent-web \
  --resource-group bidagent-rg \
  --source "https://github.com/gitmj/bidagent" \
  --branch main \
  --app-location "/frontend" \
  --output-location "dist" \
  --login-with-github
```

This creates a GitHub Actions workflow automatically that builds and deploys on every push.

### 2b. Set the API base URL

In the GitHub Actions workflow file (`.github/workflows/azure-static-web-apps-*.yml`),
add the env variable to the build step:

```yaml
env:
  VITE_API_BASE_URL: "https://bidagent-api.azurewebsites.net"
```

Or set it in the Static Web Apps configuration:

```bash
az staticwebapp appsettings set \
  --name bidagent-web \
  --resource-group bidagent-rg \
  --setting-names "VITE_API_BASE_URL=https://bidagent-api.azurewebsites.net"
```

### 2c. Handle SPA routing

Create `frontend/staticwebapp.config.json`:

```json
{
  "navigationFallback": {
    "rewrite": "/index.html"
  }
}
```

(Already added to the repo — see the file below.)

---

## Step 3 — Update CORS

Add your new Azure URLs to the backend's CORS allow list.

In `backend/main.py`, add to `allow_origins`:

```python
"https://bidagent-web.azurestaticapps.net",   # Azure Static Web App
"https://bidagent-api.azurewebsites.net",      # Backend itself (if needed)
```

> **Tip**: Replace the placeholder names with your actual Azure resource names.

---

## Step 4 — Custom Domain (Optional)

### Backend
```bash
az webapp config hostname add \
  --webapp-name bidagent-api \
  --resource-group bidagent-rg \
  --hostname api.bidagent.co.uk

# Free managed SSL certificate
az webapp config ssl create \
  --name bidagent-api \
  --resource-group bidagent-rg \
  --hostname api.bidagent.co.uk
```

### Frontend
```bash
az staticwebapp hostname set \
  --name bidagent-web \
  --resource-group bidagent-rg \
  --hostname app.bidagent.co.uk
```

Free SSL is included with both services.

---

## Cost Summary

| Resource | SKU | Monthly cost |
|---|---|---|
| App Service plan | B1 Linux | ~$13 |
| Static Web Apps | Free | $0 |
| SQLite | File on disk | $0 |
| ChromaDB | File on disk | $0 |
| Custom domain SSL | Managed certs | $0 |
| **Total** | | **~$13/mo** |

> **Scaling up later**: When you outgrow this setup, the natural path is
> B1 → S1 ($55/mo) for staging slots and auto-scale, then move SQLite →
> Azure PostgreSQL Flexible ($15/mo) and optionally add Azure Blob Storage
> for uploaded PDFs.

---

## Quick Reference Commands

```bash
# View live logs
az webapp log tail --name bidagent-api --resource-group bidagent-rg

# SSH into the container
az webapp ssh --name bidagent-api --resource-group bidagent-rg

# Restart the backend
az webapp restart --name bidagent-api --resource-group bidagent-rg

# Check deployment status
az webapp deployment list-publishing-profiles \
  --name bidagent-api --resource-group bidagent-rg

# Tear down everything when done
az group delete --name bidagent-rg --yes --no-wait
```

---

## Troubleshooting

**"Module not found" errors after deploy**
Make sure `SCM_DO_BUILD_DURING_DEPLOYMENT=true` is set. Azure's Oryx build
system will run `pip install -r requirements.txt` automatically.

**ChromaDB / sentence-transformers slow on first request**
The embedding model (~90 MB) downloads on first load. On B1 with 1.75 GB RAM
this takes ~30 seconds the very first time. Subsequent requests are fast.
To pre-warm: `curl https://bidagent-api.azurewebsites.net/api/v1/knowledge`

**SQLite "database is locked"**
With 2 Gunicorn workers you can occasionally hit this under concurrent writes.
For MVP with a few users this is rare. If it happens, reduce to `-w 1` in the
startup command, or plan the move to PostgreSQL.

**Frontend shows blank page**
Ensure `staticwebapp.config.json` is in the `frontend/` folder and the
`navigationFallback` rewrite is configured. Check that `VITE_API_BASE_URL`
was set at build time (not runtime — Vite bakes env vars into the bundle).

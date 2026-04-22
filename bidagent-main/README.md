# BidAgent

AI-powered platform that helps companies respond to government and enterprise tenders. Upload a tender PDF, and BidAgent analyses it, matches it against your company's knowledge base, and generates draft responses with an agentic refinement chat.

**Status:** MVP functional. Go/No-Go analysis, RAG-powered bid generation, agentic chat, and JWT auth are all working. Migrating to Azure for production.

**Task Board:** [Google Sheets](https://docs.google.com/spreadsheets/d/1f9xD9YNUwoCmhcs3zkN1lukawc4fMsBG/edit?gid=508052490#gid=508052490) — all tasks with descriptions, steps, and acceptance criteria.

## Live URLs

| What | URL |
|------|-----|
| Frontend (dev) | https://bidagent.vercel.app |
| Backend dashboard (dev) | https://dashboard.render.com/web/srv-d5gkkjf5r7bs73efi1n0 |
| Swagger API docs | `<backend-url>/docs` |

> **Production (Azure):** Not yet deployed. See [Azure Deployment Guide](docs/azure-deployment.md) for setup instructions (~$13/mo).

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Git

### Backend (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Edit with your API keys
uvicorn main:app --host 0.0.0.0 --reload
```

API runs at `http://localhost:8000`. Verify: `http://localhost:8000/health`.

### Frontend (React + Vite)

```bash
cd frontend
npm install
cp .env.example .env.local      # Edit if backend is not on :8000
npm run dev
```

Opens at `http://localhost:5173`.

### Environment Variables

| Variable | Where | Description |
|----------|-------|-------------|
| `LLM_API_KEY` | Backend `.env` | API key for the LLM provider (Gemini by default) |
| `LLM_MODEL` | Backend `.env` | Model name (default: `gemini-2.0-flash`) |
| `LLM_BASE_URL` | Backend `.env` | OpenAI-compatible endpoint |
| `DATABASE_URL` | Backend `.env` | DB connection string (default: `sqlite:///./bidagent.db`) |
| `JWT_SECRET` | Backend `.env` | Secret for JWT token signing |
| `CHROMA_PERSIST_DIR` | Backend `.env` | ChromaDB storage path (default: `./chroma_data`) |
| `EMBEDDING_MODEL` | Backend `.env` | Sentence-transformers model (default: `all-MiniLM-L6-v2`) |
| `VITE_API_BASE_URL` | Frontend `.env.local` | Backend URL (default: `http://localhost:8000`) |

---

## Architecture

```
Frontend (React 18 + Vite)  ──HTTP──>  Backend (FastAPI)  ──API──>  LLM Provider (Gemini)
     │                                      │
     │                                      ├── PDF Parser (PyMuPDF)
     │                                      ├── Knowledge Base (ChromaDB + sentence-transformers)
     │                                      ├── RAG Retrieval (semantic search → prompt building)
     │                                      ├── Agentic Chat (6-tool agent loop)
     │                                      ├── Auth (JWT + bcrypt)
     │                                      └── Database (SQLite via SQLAlchemy)
     │
  Vercel (dev)                           Render (dev)
  Azure Static Web Apps (prod)           Azure App Service B1 (prod)
```

| Component | Technology | Status |
|-----------|------------|--------|
| Backend API | Python + FastAPI | Live |
| Frontend | React 18 + Vite + Tailwind CSS v4 | Live |
| PDF Processing | PyMuPDF (fitz) | Working |
| AI / LLM | Gemini 2.0 Flash (OpenAI-compatible wrapper) | Working |
| Knowledge Base | ChromaDB + sentence-transformers (all-MiniLM-L6-v2) | Working |
| RAG Pipeline | Semantic retrieval → prompt building → LLM generation | Working |
| Agentic Chat | 6-tool agent loop with SSE streaming | Working |
| Database | SQLite + SQLAlchemy | Working |
| Auth | JWT + bcrypt (login/signup) | Working |
| Bid Builder | Four-phase inference pipeline with SSE progress | Working |
| Compliance Checker | AI-powered requirement validation | Not started |
| DOCX/PDF Export | Formatted bid document export | Not started |

---

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/` | API info |
| POST | `/api/v1/go-no-go` | Upload PDF → Go/No-Go decision + evidence |
| POST | `/api/v1/generate` | Send text + prompt to LLM, get response |
| POST | `/api/v1/auth/signup` | Create account |
| POST | `/api/v1/auth/login` | Login, receive JWT |
| POST | `/api/v1/knowledge/upload` | Upload a knowledge base document (PDF) |
| GET | `/api/v1/knowledge` | List knowledge base documents |
| GET | `/api/v1/knowledge/search?q=...` | Semantic search across knowledge base |
| DELETE | `/api/v1/knowledge/{doc_id}` | Remove a document from knowledge base |
| POST | `/api/v1/knowledge/ask` | RAG-powered Q&A against knowledge base |
| POST | `/api/v1/bid/...` | Bid generation pipeline endpoints |
| POST | `/api/v1/chat/...` | Agentic refinement chat endpoints |
| GET | `/api/v1/sessions` | List tender sessions |
| GET | `/docs` | Interactive Swagger docs |

---

## Code Structure

```
bidagent/
├── backend/
│   ├── main.py                  # FastAPI entry, CORS, router setup
│   ├── config.py                # All settings from env vars
│   ├── database.py              # SQLAlchemy engine + session
│   ├── seed.py                  # DB backup/restore scheduler
│   ├── routes/
│   │   ├── health.py            # GET /health
│   │   ├── go_no_go.py          # POST /api/v1/go-no-go
│   │   ├── generate.py          # POST /api/v1/generate
│   │   ├── knowledge.py         # Knowledge base CRUD + search + ask
│   │   ├── auth.py              # JWT signup/login
│   │   ├── bid.py               # Bid generation pipeline
│   │   ├── chat.py              # Agentic refinement chat
│   │   └── sessions.py          # Tender session management
│   ├── services/
│   │   ├── pdf_parser.py        # Extract text & structure from PDFs
│   │   ├── knowledge_base.py    # ChromaDB vector store operations
│   │   ├── rag.py               # RAG retrieval + prompt building
│   │   └── llm.py               # LLM client (generate_text + generate_with_tools)
│   ├── models/                  # SQLAlchemy models
│   ├── requirements.txt
│   └── runtime.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # ErrorBoundary, LoadingSpinner, ChatPanel, etc.
│   │   ├── pages/               # Home, Login, Signup, BidBuilder, Debug
│   │   ├── services/            # api.js — all fetch calls
│   │   └── App.jsx              # React Router + ProtectedRoute
│   ├── package.json
│   ├── vercel.json              # Vercel SPA rewrites
│   └── staticwebapp.config.json # Azure Static Web Apps config
├── docs/
│   └── azure-deployment.md      # Azure deployment guide (~$13/mo)
├── .github/
│   └── workflows/
│       ├── azure-backend.yml    # CI/CD: backend → Azure App Service
│       └── azure-frontend.yml   # CI/CD: frontend → Azure Static Web Apps
├── .env.example
├── .gitignore
└── README.md
```

---

## Deployment

### Dev (current)

Frontend deploys to **Vercel** on push to `main`. Backend deploys to **Render** on push to `main`.

### Production (Azure) — ~$13/mo

See **[docs/azure-deployment.md](docs/azure-deployment.md)** for the full guide. Summary:

- **Frontend:** Azure Static Web Apps (Free tier, $0) — global CDN, free SSL
- **Backend:** Azure App Service B1 Linux (~$13/mo) — always-on, 1.75 GB RAM, persistent disk
- **Database:** SQLite on App Service disk (no separate DB service needed for MVP)
- **Vector store:** ChromaDB on App Service disk
- **CI/CD:** GitHub Actions workflows included in `.github/workflows/`

```bash
# Quick setup (4 commands)
az group create --name bidagent-rg --location uksouth
az appservice plan create --name bidagent-plan --resource-group bidagent-rg --sku B1 --is-linux
az webapp create --name bidagent-api --resource-group bidagent-rg --plan bidagent-plan --runtime "PYTHON:3.11"
az staticwebapp create --name bidagent-web --resource-group bidagent-rg \
  --source "https://github.com/gitmj/bidagent" --branch main \
  --app-location "/frontend" --output-location "dist"
```

---

## How We Work

### Branches

| Branch | Purpose | Deploys to |
|--------|---------|------------|
| `main` | Stable. Never push directly. | Vercel + Render (dev), Azure (prod) |
| `feature/your-task` | New features | Vercel preview URL per PR |
| `fix/bug-name` | Bug fixes | Vercel preview URL per PR |

### Workflow

1. `git checkout main && git pull`
2. `git checkout -b feature/your-task-name`
3. Code and test locally
4. `git add <files> && git commit -m "description"`
5. `git push -u origin feature/your-task-name`
6. Open a PR — describe what changed and how to test
7. Get a review, then merge → auto-deploys

---

## Tech Stack

| Layer | Technology | Docs |
|-------|------------|------|
| Backend | FastAPI (Python) | [fastapi.tiangolo.com](https://fastapi.tiangolo.com) |
| Frontend | React 18 | [react.dev](https://react.dev) |
| Build | Vite 5 | [vitejs.dev](https://vitejs.dev) |
| Styling | Tailwind CSS v4 | [tailwindcss.com](https://tailwindcss.com) |
| Routing | React Router v6 | [reactrouter.com](https://reactrouter.com) |
| PDF parsing | PyMuPDF | [pymupdf.readthedocs.io](https://pymupdf.readthedocs.io) |
| Vector DB | ChromaDB | [docs.trychroma.com](https://docs.trychroma.com) |
| Embeddings | sentence-transformers | [sbert.net](https://sbert.net) |
| LLM | Gemini 2.0 Flash | [ai.google.dev](https://ai.google.dev) |
| ORM | SQLAlchemy | [sqlalchemy.org](https://sqlalchemy.org) |
| Frontend hosting (dev) | Vercel | [vercel.com/docs](https://vercel.com/docs) |
| Backend hosting (dev) | Render | [docs.render.com](https://docs.render.com) |
| Production hosting | Azure (App Service + Static Web Apps) | [azure.microsoft.com](https://azure.microsoft.com) |

## Useful Commands

| What | Command |
|------|---------|
| Start backend | `cd backend && uvicorn main:app --host 0.0.0.0 --reload` |
| Start frontend | `cd frontend && npm run dev` |
| Health check | `curl http://localhost:8000/health` |
| Test Go/No-Go | `curl -F "file=@tender.pdf" http://localhost:8000/api/v1/go-no-go` |
| Build frontend | `cd frontend && npm run build` |
| View Azure logs | `az webapp log tail --name bidagent-api --resource-group bidagent-rg` |
| Tear down Azure | `az group delete --name bidagent-rg --yes` |

# Backend Architecture

## Overview

BidAgent backend is a FastAPI application that powers an AI-driven bid response platform for UK Public Sector tenders. It provides PDF analysis, knowledge base management with vector search, agentic bid drafting with a 4-phase pipeline, iterative refinement via a chat interface with tool-use capabilities, compliance checking, and session persistence.

**Stack:** Python 3.11, FastAPI, SQLAlchemy (SQLite), ChromaDB (vector DB), Sentence-Transformers (embeddings), Gemini 2.0 Flash (LLM via OpenAI-compatible API).

---

## System Diagram

```
Client (React)
    │
    ├── POST /api/v1/auth/signup, /login     → JWT token
    ├── POST /api/v1/go-no-go               → PDF → GO/NO-GO decision
    ├── POST /api/v1/knowledge/upload        → PDF → ChromaDB embeddings
    ├── POST /api/v1/bid/extract-sections    → LLM reads tender → section list
    ├── POST /api/v1/bid/generate-pipeline   → SSE: 4-phase draft generation
    ├── POST /api/v1/bid/compliance          → Compliance matrix check
    ├── POST /api/v1/chat/message            → Agent loop (LLM + tools)
    ├── CRUD /api/v1/sessions               → Bid session persistence
    └── GET  /api/v1/chat/history/:sid/:sec  → Conversation history
                │
    ┌───────────┴───────────────────────────────────┐
    │                  FastAPI App                   │
    │                                               │
    │  Routes ──► Services ──► External Systems     │
    │                                               │
    │  routes/       services/                      │
    │  ├── auth      ├── auth.py     → bcrypt, JWT  │
    │  ├── go_no_go  ├── pdf_parser  → PyMuPDF      │
    │  ├── knowledge ├── knowledge   → ChromaDB     │
    │  ├── bid       ├── rag.py      → KB + LLM     │
    │  ├── chat      ├── llm.py      → Gemini API   │
    │  ├── sessions  ├── agent.py    → Tool loop    │
    │  └── generate  └── agent_tools → 7 tools      │
    │                                               │
    │  models/           database.py                │
    │  ├── user          SQLAlchemy + SQLite         │
    │  ├── session                                  │
    │  ├── conversation  seed.py (JSON backup)      │
    │  └── bid_session                              │
    └───────────────────────────────────────────────┘
```

---

## Directory Structure

```
backend/
├── main.py                  # App entry: FastAPI init, CORS, router registration
├── config.py                # Environment variables (dotenv)
├── database.py              # SQLAlchemy engine, session factory, Base class
├── seed.py                  # JSON dump/restore for persistence
├── seed_data.json           # Backup data (auto-generated every 5 min)
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (not committed)
├── .env.example             # Template for env vars
├── design-docs/
│   └── ARCHITECTURE.md      # This file
├── routes/
│   ├── __init__.py          # Exports all routers
│   ├── health.py            # GET /health
│   ├── auth.py              # POST /auth/signup, /auth/login
│   ├── go_no_go.py          # POST /go-no-go (PDF analysis)
│   ├── generate.py          # POST /generate (direct LLM)
│   ├── knowledge.py         # CRUD for knowledge base docs
│   ├── bid.py               # Section extraction + 4-phase pipeline + compliance
│   ├── chat.py              # Agentic chat with tool use
│   └── sessions.py          # Bid session CRUD (save/load/list drafts)
├── services/
│   ├── auth.py              # Password hashing, JWT creation/verification
│   ├── llm.py               # LLM calls (text + tool-use)
│   ├── pdf_parser.py        # PDF text extraction, chunking, go/no-go logic
│   ├── knowledge_base.py    # ChromaDB: ingest, search, list, delete
│   ├── rag.py               # Retrieve-Augment-Generate pipeline
│   ├── agent.py             # Agent loop engine (LLM ↔ tools)
│   └── agent_tools.py       # 7 tool definitions + implementations
└── models/
    ├── __init__.py           # Exports all models
    ├── user.py               # User table (email, password, name)
    ├── session.py            # TenderSession table (go/no-go results)
    ├── conversation.py       # Conversation table (chat messages)
    └── bid_session.py        # BidSession table (drafts, sections, status)
```

---

## Database Schema

```sql
-- Users (authentication)
CREATE TABLE users (
    id              INTEGER PRIMARY KEY,
    email           TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    name            TEXT NOT NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tender sessions (go/no-go results)
CREATE TABLE tender_sessions (
    id          INTEGER PRIMARY KEY,
    filename    TEXT NOT NULL,
    decision    TEXT,
    confidence  REAL,
    facts_json  TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Chat conversations (agent messages)
CREATE TABLE conversations (
    id              INTEGER PRIMARY KEY,
    session_id      TEXT NOT NULL,
    section_id      TEXT NOT NULL,   -- "_global" for shared chat
    role            TEXT NOT NULL,
    content         TEXT,
    tool_calls_json TEXT,
    updated_draft   TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Bid sessions (draft persistence)
CREATE TABLE bid_sessions (
    id              INTEGER PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    tender_name     TEXT NOT NULL,
    tender_doc_id   TEXT,            -- ChromaDB doc ID
    sections_json   TEXT,            -- JSON: extracted sections list
    drafts_json     TEXT,            -- JSON: {section_id: {text, sources, score, wordCount}}
    status          TEXT DEFAULT 'in_progress',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Vector DB (ChromaDB):** Stores document chunks as embeddings in `./chroma_data/`. Collection name: `bidagent_knowledge`. Each chunk has metadata: `{doc_id, filename, page, chunk_id}`.

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | No | Health check |
| POST | `/api/v1/auth/signup` | No | Create account, return JWT |
| POST | `/api/v1/auth/login` | No | Login, return JWT |
| GET | `/api/v1/` | No | API info |
| POST | `/api/v1/go-no-go` | Yes | Upload PDF, get GO/NO-GO decision |
| POST | `/api/v1/generate` | Yes | Direct LLM text generation |
| POST | `/api/v1/knowledge/upload` | No* | Upload PDF to knowledge base |
| GET | `/api/v1/knowledge` | No* | List KB documents |
| GET | `/api/v1/knowledge/search` | No* | Semantic search |
| DELETE | `/api/v1/knowledge/{doc_id}` | No* | Delete document |
| POST | `/api/v1/knowledge/ask` | No* | RAG Q&A |
| POST | `/api/v1/bid/extract-sections` | Yes | LLM extracts sections from tender |
| POST | `/api/v1/bid/generate-response` | Yes | Single-pass RAG generation |
| POST | `/api/v1/bid/generate-pipeline` | Yes | SSE: 4-phase pipeline |
| POST | `/api/v1/bid/compliance` | Yes | Compliance matrix check |
| POST | `/api/v1/chat/message` | Yes | Send message to agent |
| GET | `/api/v1/chat/history/{sid}/{sec}` | Yes | Get conversation history |
| POST | `/api/v1/sessions` | Yes | Create bid session |
| GET | `/api/v1/sessions` | Yes | List user's bid sessions |
| GET | `/api/v1/sessions/{id}` | Yes | Get bid session |
| PUT | `/api/v1/sessions/{id}` | Yes | Update drafts (autosave) |
| DELETE | `/api/v1/sessions/{id}` | Yes | Delete bid session |

*\*TODO: Knowledge base routes need auth added (see TODO.md #1)*

---

## Core Flows

### Authentication
```
signup/login request → hash/verify password (bcrypt)
→ create JWT (HS256, 24h expiry) → return {token, user}
```

### Go/No-Go Decision
```
PDF upload → extract_pages (PyMuPDF) → chunk_pages (≤4000 chars)
→ keyword search (dates, bonds, mandatory language)
→ regex date extraction → decide GO/NO-GO/NEEDS_INFO → return with evidence
```

### Knowledge Base Ingestion
```
PDF upload → extract_pages → chunk_pages
→ embed chunks (sentence-transformers all-MiniLM-L6-v2)
→ store in ChromaDB with metadata (doc_id, page, filename)
```

### 4-Phase Pipeline (SSE)
```
Phase A: Evidence Gap Analysis
  → search KB for section relevance → LLM identifies gaps

Phase B: Draft & Squeeze
  → RAG generates ~400 word draft → LLM rewrites to 240-249 words

Phase C: Tone Styling
  → LLM rewrites for UK public sector tone (active voice, outcome-focused)

Phase D: Red Team Scoring
  → Independent LLM evaluates 0-100 against rubric
  → Returns score, breakdown, strengths, improvements

Each phase emits an SSE event with status and result.
Final event: {final_draft, word_count, score, gaps, sources}
```

### Agent Chat Loop
```
User message → load conversation history from DB → build system prompt
→ call LLM with messages + 7 tool definitions
→ LOOP (max 10 iterations):
    If LLM returns tool_calls:
      → execute each tool → append tool results to messages → loop again
    If LLM returns text:
      → extract any updated_draft from tool results → break
→ save assistant response + tool calls to DB → return
```

### Compliance Matrix
```
Extract all "shall/must/required" statements from tender (via KB search + LLM)
→ If drafts provided: check each requirement against drafts (via LLM)
→ Return: requirements list with status (addressed/partial/missing),
  category, criticality, coverage percentage
```

### Session Persistence
```
New bid: upload → extract sections → create BidSession in DB → auto-generate
Edit: user modifies drafts → autosave (PUT /sessions/{id}) every 3 seconds
Resume: GET /sessions/{id} → restore sections + drafts → continue editing
Duplicate detection: check for existing session with same tender_doc_id
```

### Agent Tools

| Tool | Purpose | Implementation |
|------|---------|----------------|
| `search_knowledge_base` | Semantic search across uploaded docs | `knowledge_base.search()` |
| `generate_draft` | RAG-powered bid draft (~400 words) | `rag.answer_with_context()` |
| `squeeze_word_count` | Rewrite to 240-249 words | LLM call with squeeze prompt |
| `score_against_rubric` | Score 0-100 with breakdown | LLM call as independent evaluator |
| `analyze_evidence_gaps` | Identify missing evidence | KB search + LLM gap analysis |
| `restyle_tone` | UK public sector tone adjustment | LLM call with tone guidelines |
| `compliance_check` | Extract requirements, check coverage | KB search + 2 LLM calls |

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_API_KEY` | *(required)* | Gemini API key |
| `LLM_MODEL` | `gemini-2.0-flash` | LLM model name |
| `LLM_BASE_URL` | Google AI OpenAI-compat endpoint | API base URL |
| `DATABASE_URL` | `sqlite:///./bidagent.db` | SQLAlchemy connection string |
| `JWT_SECRET` | `change-me-in-production` | JWT signing key |
| `JWT_EXPIRY_HOURS` | `24` | Token lifetime |
| `CHROMA_PERSIST_DIR` | `./chroma_data` | Vector DB storage path |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformers model |

---

## Persistence Strategy

- **SQLite:** Users, tender sessions, conversations, bid sessions. Auto-created on startup via `init_db()`.
- **ChromaDB:** Document chunks + embeddings. Persisted to `./chroma_data/`.
- **JSON Backup:** `seed.py` dumps users + sessions to `seed_data.json` every 5 minutes. On startup, `restore_db()` re-populates from JSON.
- **Autosave:** Frontend sends `PUT /sessions/{id}` every 3 seconds on draft changes.

---

## Dependencies

```
fastapi==0.109.0           # Web framework
uvicorn[standard]==0.27.0  # ASGI server
gunicorn==21.2.0           # Production process manager
python-multipart==0.0.6    # File uploads
PyMuPDF==1.25.3            # PDF text extraction
httpx==0.27.0              # Async HTTP client (LLM calls)
sqlalchemy==2.0.25         # ORM
chromadb==0.6.3            # Vector database
sentence-transformers==3.0.1 # Embeddings
bcrypt==4.1.2              # Password hashing
python-jose[cryptography]==3.3.0 # JWT
python-dotenv==1.0.1       # .env file loading
```

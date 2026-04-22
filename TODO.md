# BidAgent TODO Tracker

## Critical (Fix Now)

| # | Category | Issue | File |
|---|----------|-------|------|
| 1 | Security | Knowledge base routes have **no auth** — anyone can upload/delete docs | `routes/knowledge.py` |
| 2 | Security | JWT secret defaults to `"change-me-in-production"` — token forgery risk | `config.py:10` |
| 3 | Bug | Chat saves user message to DB **before** agent runs — orphaned messages on failure | `routes/chat.py:52-58` |
| 4 | Bug | SSE pipeline `connectPipeline` has **no error handling** — UI hangs on failure | `api.js:118-154` |
| 5 | Security | No multi-user isolation — all users share the same knowledge base | Multiple files |

## High Priority

| # | Category | Issue | File |
|---|----------|-------|------|
| 6 | UX | Chat context quote not cleared when switching sections | `BidBuilder.jsx` |
| 7 | Bug | No timeout on agent tool execution — agent loop can hang | `agent.py:72-128` |
| 8 | UX | No way to **cancel** a running pipeline or chat operation | BidBuilder + ChatPanel |
| 9 | Missing | Session/drafts **lost on page refresh** — no persistence | `BidBuilder.jsx:22` |
| 10 | Missing | No database migrations (Alembic) — schema changes break existing data | `database.py` |
| 11 | Bug | SQLite contention — seed dump thread can deadlock with main app | `seed.py:83-95` |

## Medium Priority

| # | Category | Issue | File |
|---|----------|-------|------|
| 12 | Missing | No **DOCX export** — only markdown (design says Word doc) | `BidBuilder.jsx:140` |
| 13 | Missing | No **draft version history** — edits overwrite permanently | BidBuilder |
| 14 | Missing | No **autosave** of manual edits to backend | BidBuilder |
| 15 | Incomplete | Go/No-Go decision logic is naive (keyword-only, no real scoring) | `pdf_parser.py:119-139` |
| 16 | Incomplete | Evidence gap analysis is a basic LLM prompt, not structured | `agent_tools.py:174-189` |
| 17 | Incomplete | Scoring rubric is **hardcoded** — should be configurable per tender | `agent_tools.py:147-171` |
| 18 | Debt | No env var validation at startup — silent failures at runtime | `config.py` |
| 19 | Debt | Inconsistent error handling across routes (different exceptions, HTTP codes) | Multiple routes |
| 20 | Security | CORS allows all methods/headers — should be explicit | `main.py:13-25` |
| 21 | Security | No rate limiting on any endpoint | All routes |
| 22 | Security | LLM responses not sanitized — potential XSS via markdown | ChatPanel |
| 23 | Missing | No Dockerfile for production deployment | Backend |

## Low Priority

| # | Category | Issue | File |
|---|----------|-------|------|
| 24 | Debt | `TenderSession` model exists but is never used by routes | `models/session.py` |
| 25 | Debt | ChromaDB/embedding model singletons not thread-safe | `knowledge_base.py:24-43` |
| 26 | Debt | Magic numbers scattered (4000 chunk size, 250 word limit, 300s dump interval) | Multiple |
| 27 | UX | Word count calculation is naive (`split(/\s+/)`) | `BidBuilder.jsx:13` |
| 28 | UX | Pipeline errors shown in tiny red box — easy to miss | `BidBuilder.jsx:405` |
| 29 | Incomplete | No pagination on KB document list | `knowledge.py:57-65` |
| 30 | Missing | No real-time collaboration (WebSocket) | Not built |
| 31 | Bug | Scanned PDF detection too simplistic (< 500 chars) | `pdf_parser.py:36-38` |

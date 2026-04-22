# Frontend Architecture

## Overview

BidAgent frontend is a React 18 SPA that provides a document-editor-style interface for building bid responses. Users upload tender PDFs, the system extracts sections via LLM, auto-generates drafts through a 4-phase pipeline, and users refine responses via an agentic chat panel with text selection tools. Bid sessions persist across browser sessions with autosave.

**Stack:** React 18, Vite, Tailwind CSS v4, React Router v6, React Markdown.

---

## User Flow

```
Login/Signup → Home (Upload or Resume) → BidBuilder (Edit + Chat) → Export
```

1. **Auth:** Login or signup → JWT stored in localStorage → protected routes
2. **Dashboard:** View saved bid sessions (with progress) or start a new bid
3. **Upload:** Enter tender name → upload tender PDF + optional evidence PDFs → files sent to knowledge base
4. **Duplicate check:** If a session for this tender exists, prompt to continue or start fresh
5. **Build:** Sections extracted from tender → all sections auto-generate → user edits in document view → chat panel for refinement → text selection toolbar for quick actions → compliance matrix check
6. **Autosave:** Drafts save to backend every 3 seconds
7. **Export:** Download all sections as markdown file

---

## Directory Structure

```
frontend/
├── src/
│   ├── main.jsx                    # React entry point
│   ├── index.css                   # Tailwind + typography plugin imports
│   ├── App.jsx                     # Router + ErrorBoundary
│   ├── pages/
│   │   ├── Login.jsx               # Auth form
│   │   ├── Signup.jsx              # Registration form
│   │   ├── Home.jsx                # Dashboard: saved sessions + new bid upload
│   │   ├── BidBuilder.jsx          # Main editing interface
│   │   └── Debug.jsx               # API diagnostics (no auth)
│   ├── components/
│   │   ├── ErrorBoundary.jsx       # React error catch
│   │   ├── LoadingSpinner.jsx      # Animated spinner (sm/md/lg)
│   │   ├── ProtectedRoute.jsx      # Auth guard → redirects to /login
│   │   ├── ChatPanel.jsx           # Chat interface with markdown + context quotes
│   │   ├── PipelineProgress.jsx    # 4-phase progress stepper
│   │   ├── SelectionToolbar.jsx    # Floating text action toolbar
│   │   └── ComplianceMatrix.jsx    # Modal: requirement coverage check
│   ├── hooks/
│   │   ├── useChat.js              # Chat state + API (global per session)
│   │   └── usePipeline.js          # Pipeline SSE + phase tracking
│   └── services/
│       └── api.js                  # All backend API calls (25+ functions)
├── package.json
├── vite.config.js                  # Vite + React + Tailwind plugins
└── vercel.json                     # SPA rewrite rules
```

---

## Route Map

| Path | Component | Auth | Description |
|------|-----------|------|-------------|
| `/login` | Login | No | Email/password login |
| `/signup` | Signup | No | Account creation |
| `/` | Home | Yes | Dashboard: saved sessions + new bid upload |
| `/bid` | BidBuilder | Yes | New bid (via location.state) |
| `/bid/:sessionId` | BidBuilder | Yes | Resume saved bid |
| `/debug` | Debug | No | API connectivity diagnostics |

---

## Component Hierarchy

```
App
├── ErrorBoundary
├── BrowserRouter
│   ├── Login
│   ├── Signup
│   ├── ProtectedRoute → Home
│   │   └── Session list (resume) + Upload form (new bid)
│   ├── ProtectedRoute → BidBuilder
│   │   ├── ChatPanel (left, resizable)
│   │   ├── SelectionToolbar (floating on text select)
│   │   ├── PipelineProgress (inline during generation)
│   │   ├── ComplianceMatrix (modal)
│   │   └── LoadingSpinner
│   └── Debug
```

---

## BidBuilder Layout

```
┌──────────────────────────────────────────────────────────┐
│ Dashboard │ Tender Name (X/N sections) Saved │ Compliance│
│           │                                  │ Export    │
├──────────────────────────────────────────────────────────┤
│ [Section 1 ✓] ─ [Section 2 ✓] ─ [Section 3 ~] ─ ...    │
├──────────────┬─┬─────────────────────────────────────────┤
│              │↔│                                         │
│  Chat Panel  │ │  Bid Document                           │
│  (30%)       │ │                                         │
│              │ │  Section Title          72/100  Regen   │
│  Messages    │ │  Description in italic                  │
│  w/ markdown │ │  [rendered markdown / editable textarea]│
│              │ │  sources: file.pdf p.3                  │
│  Tool call   │ │  ──────────────────────                 │
│  badges      │ │  Section Title            --    Gen     │
│              │ │  Click Generate...                      │
│  Context     │ │  ──────────────────────                 │
│  quote       │ │                                         │
│  ──────────  │ │  [SelectionToolbar] (floating on select)│
│  [input] Send│ │  [Add to chat] [Rewrite] [Improve]     │
└──────────────┴─┴─────────────────────────────────────────┘
```

### Panel resize
- Drag handle (1px) between chat and document
- Min 15%, max 55% for chat panel width

### Document rendering
- **Active section:** editable textarea with blue border
- **Inactive sections:** rendered as formatted markdown (bold, lists, etc.)
- Click a section to switch between view/edit mode

---

## Key Pages

### Home.jsx — Dashboard
**State:** `tenderName`, `tenderFile`, `evidenceFiles[]`, `uploading`, `error`, `uploadStatus`, `sessions[]`

**Features:**
- **Continue Working** section: lists saved bid sessions with progress bars, section counts, last edited date, delete button
- Click a session → navigates to `/bid/:sessionId` to resume
- **New Bid** form: tender name, SoR upload, evidence upload, Start Bid button

### BidBuilder.jsx — Main Interface
**State:** `dbSessionId`, `sections[]`, `responses{}`, `activeSection`, `chatWidth`, `generatingAll`, `selectedText`, `chatContext`, `showCompliance`, `existingSession`, `saveStatus`

**Two entry modes:**
1. **New bid** (via `location.state`): checks for duplicate session → extract sections → create DB session → auto-generate all
2. **Resume** (via URL `params.sessionId`): load saved session from DB → restore sections + drafts

**Autosave:** `useEffect` watches `responses` changes → debounced 3-second `PUT /sessions/{id}` → shows "Saved" indicator

**Duplicate detection:** When starting a new bid, checks `listSessions()` for matching `tender_doc_id`. If found, shows prompt: "Continue existing bid" or "Start fresh"

---

## Components

### ChatPanel
**Props:** `messages`, `onSend`, `isLoading`, `sectionTitle`, `contextText`, `onClearContext`

- Markdown rendering for assistant messages (react-markdown + prose classes)
- Tool call badges (blue cards with summary text)
- Suggestion chips when empty
- Context quote block (blue, from text selection, with dismiss ✕)
- Input auto-focuses after send and on section change

### ComplianceMatrix
**Props:** `drafts` (concatenated section texts), `onClose`

- Modal overlay with Run Check button
- Summary cards: total requirements, addressed, partial, gaps
- Coverage progress bar (green >80%, yellow >50%, red <50%)
- Filter tabs: All / Missing / Partial / Addressed
- Each requirement: status badge, category, criticality, notes, addressed-in reference
- Re-run button for checking after edits

### PipelineProgress
**Props:** `phases[]` (each: `{id, label, status, result}`)

- 4 phases: Evidence Analysis → Draft & Squeeze → Tone Styling → Quality Scoring
- Pending (gray) → Running (blue pulse) → Done (green check)
- Shows score and word count when available

### SelectionToolbar
**Props:** `position`, `onAddToChat`, `onRegenerate`, `onImprove`

- Dark floating toolbar, appears above text selection
- Buttons: "Add to chat", "Rewrite", "Improve"
- Works with both textarea and DOM text selections
- `onMouseDown={preventDefault}` prevents deselection

---

## Hooks

### useChat(sessionId, sectionTitle, sectionDescription, docId)
**Returns:** `{ messages, sendMessage, isLoading }`

- Global per bid session (uses `_global` as section_id)
- Loads history on mount, sends messages via API
- Returns response object (may include `updated_draft`)

### usePipeline()
**Returns:** `{ phases, isRunning, result, runPipeline }`

- Connects SSE for real-time pipeline progress
- Updates phase statuses as events arrive
- Sets final result on completion

---

## API Service Layer (api.js)

**25+ functions** organized by domain:

| Domain | Functions |
|--------|-----------|
| Auth | `signup`, `login`, `logout`, `getStoredUser`, `isAuthenticated` |
| Health | `checkHealth` |
| Go/No-Go | `analyzeGoNoGo` |
| LLM | `generate` |
| Knowledge Base | `uploadToKnowledgeBase`, `listKnowledgeBase` |
| Bid Builder | `extractSections`, `generateBidResponse` |
| Sessions | `createSession`, `listSessions`, `getSession`, `updateSessionDrafts`, `deleteSession` |
| Compliance | `runComplianceCheck` |
| Pipeline | `connectPipeline` (SSE streaming) |
| Chat | `sendChatMessage`, `getChatHistory` |

---

## Auth State Management

- **Storage:** JWT token + user JSON in `localStorage`
- **Guard:** `ProtectedRoute` redirects to `/login` if not authenticated
- **Expiry:** 401 responses trigger automatic logout + redirect (global in `request()`)

---

## Styling

- **Framework:** Tailwind CSS v4 with `@tailwindcss/typography` plugin
- **Approach:** Utility classes only
- **Typography:** `prose` classes for markdown rendering in chat and document
- **Layout:** Flexbox-based, full viewport height (`h-screen`)

---

## Dependencies

```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "react-router-dom": "^6.21.0",
  "react-markdown": "^10.1.0",
  "tailwindcss": "^4.2.2",
  "@tailwindcss/typography": "^0.5.19",
  "@tailwindcss/vite": "^4.2.2",
  "vite": "^5.1.0",
  "@vitejs/plugin-react": "^4.2.1"
}
```

---

## Deployment

- **Platform:** Vercel
- **Build:** `npm run build` → `dist/`
- **SPA routing:** `vercel.json` rewrites all paths to `/index.html`
- **Env var:** `VITE_API_BASE_URL` points to backend (defaults to `http://localhost:8000`)

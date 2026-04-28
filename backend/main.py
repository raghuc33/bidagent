import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# INIT
# -----------------------------------------------------------------------------

print("🚀 MAIN.PY LOADING...")

load_dotenv()
app = FastAPI()

# -----------------------------------------------------------------------------
# SAFE IMPORTS (no heavy work here)
# -----------------------------------------------------------------------------

from routes.health import router as health_router
from routes.go_no_go import router as go_no_go_router
from routes.generate import router as generate_router
# ⚠️ disable heavy modules initially if needed
# from routes.knowledge import router as knowledge_router
from routes.auth import router as auth_router
from routes.bid import router as bid_router
from routes.chat import router as chat_router
from routes.sessions import router as sessions_router

# -----------------------------------------------------------------------------
# CORS CONFIG
# -----------------------------------------------------------------------------

def get_allowed_origins():
    env_origins = os.getenv("CORS_ORIGINS")

    if env_origins:
        return [o.strip() for o in env_origins.split(",")]

    return [
        "https://lemon-tree-0946c4803.7.azurestaticapps.net",
        "https://bidagent-backend1.azurewebsites.net",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


allow_origins = get_allowed_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# ROUTERS
# -----------------------------------------------------------------------------

app.include_router(health_router)
app.include_router(go_no_go_router)
app.include_router(generate_router)
# app.include_router(knowledge_router)  # 🔥 enable later
app.include_router(auth_router)
app.include_router(bid_router)
app.include_router(chat_router)
app.include_router(sessions_router)

# -----------------------------------------------------------------------------
# LAZY LOADING (MODEL)
# -----------------------------------------------------------------------------

_model = None

def get_model():
    global _model
    if _model is None:
        print("🔄 Loading SentenceTransformer model (lazy)...")

        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("all-MiniLM-L6-v2")

        print("✅ Model loaded")

    return _model

# -----------------------------------------------------------------------------
# OPTIONAL: LAZY CHROMA (SAFE)
# -----------------------------------------------------------------------------

_chroma_client = None
_collection = None

def get_collection():
    global _chroma_client, _collection

    if _chroma_client is None:
        print("🔄 Initializing ChromaDB (lazy)...")
        import chromadb
        _chroma_client = chromadb.Client()
        print("✅ ChromaDB ready")

    if _collection is None:
        _collection = _chroma_client.get_or_create_collection(name="documents")

    return _collection

# -----------------------------------------------------------------------------
# BASIC ROUTES (FAST — NO HEAVY WORK)
# -----------------------------------------------------------------------------

@app.get("/")
def root():
    return {"status": "ok", "service": "bidagent-backend"}


@app.get("/health")
def health():
    return {"status": "healthy"}

# -----------------------------------------------------------------------------
# TEST ENDPOINTS (LOADS MODEL ONLY WHEN CALLED)
# -----------------------------------------------------------------------------

@app.get("/api/embed")
def embed(text: str = "hello world"):
    model = get_model()
    embedding = model.encode(text)

    return {
        "text": text,
        "embedding_length": len(embedding)
    }


@app.get("/api/chroma")
def chroma():
    collection = get_collection()

    return {
        "message": "ChromaDB working",
        "collection": collection.name
    }

# -----------------------------------------------------------------------------
# STARTUP LOG (NO HEAVY WORK HERE)
# -----------------------------------------------------------------------------

@app.on_event("startup")
def startup():
    print("🚀 Backend started successfully")
    print("⚠️ No heavy loading at startup (Azure-safe)")
    print("🌐 Allowed CORS origins:")

    for origin in allow_origins:
        print(f" - {origin}")

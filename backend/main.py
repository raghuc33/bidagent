import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# ✅ FIXED IMPORTS FOR AZURE (IMPORTANT)
# -----------------------------------------------------------------------------

from routes.health import router as health_router
from routes.go_no_go import router as go_no_go_router
from routes.generate import router as generate_router
from routes.knowledge import router as knowledge_router
from routes.auth import router as auth_router
from routes.bid import router as bid_router
from routes.chat import router as chat_router
from routes.sessions import router as sessions_router

# -----------------------------------------------------------------------------
# INIT
# -----------------------------------------------------------------------------

print("🔥 MAIN.PY LOADING...")

load_dotenv()
app = FastAPI()

# -----------------------------------------------------------------------------
# CORS CONFIG
# -----------------------------------------------------------------------------

def get_allowed_origins():
    env_origins = os.getenv("CORS_ORIGINS")

    if env_origins:
        return [origin.strip() for origin in env_origins.split(",")]

    return [
        "https://bidagent-frontend-raghu-ci.azurestaticapps.net",
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
# INCLUDE ROUTERS
# -----------------------------------------------------------------------------

app.include_router(health_router)
app.include_router(go_no_go_router)
app.include_router(generate_router)
app.include_router(knowledge_router)
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
        print("🔄 Loading SentenceTransformer model...")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Model loaded")
    return _model


# -----------------------------------------------------------------------------
# LAZY LOADING (CHROMADB)
# -----------------------------------------------------------------------------

_chroma_client = None
_collection = None

def get_collection():
    global _chroma_client, _collection

    if _chroma_client is None:
        print("🔄 Initializing ChromaDB...")
        import chromadb
        _chroma_client = chromadb.Client()
        print("✅ ChromaDB initialized")

    if _collection is None:
        print("🔄 Creating collection...")
        _collection = _chroma_client.get_or_create_collection(name="documents")
        print("✅ Collection ready")

    return _collection


# -----------------------------------------------------------------------------
# BASIC ROUTES
# -----------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "bidagent-backend"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


# -----------------------------------------------------------------------------
# TEST ENDPOINTS
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
# STARTUP LOG
# -----------------------------------------------------------------------------

@app.on_event("startup")
def startup():
    print("🚀 Backend started successfully")
    print("🌐 Allowed CORS origins:")
    for origin in allow_origins:
        print(f" - {origin}")

    print("⚠️ Lazy loading enabled (no heavy startup)")

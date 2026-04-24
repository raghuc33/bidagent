import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load env variables
load_dotenv()

app = FastAPI()

# -----------------------------------------------------------------------------
# CORS CONFIGURATION
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
# 🔥 LAZY LOADING: MODEL
# -----------------------------------------------------------------------------

_model = None

def get_model():
    global _model
    if _model is None:
        print("🔄 Loading SentenceTransformer model...")

        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")

        print("✅ Model loaded successfully")

    return _model


# -----------------------------------------------------------------------------
# 🔥 LAZY LOADING: CHROMADB
# -----------------------------------------------------------------------------

_chroma_client = None
_collection = None

def get_chroma_collection():
    global _chroma_client, _collection

    if _chroma_client is None:
        print("🔄 Initializing ChromaDB...")

        import chromadb
        _chroma_client = chromadb.Client()

        print("✅ ChromaDB client initialized")

    if _collection is None:
        print("🔄 Creating / loading collection...")

        _collection = _chroma_client.get_or_create_collection(name="documents")

        print("✅ Collection ready")

    return _collection


# -----------------------------------------------------------------------------
# ROUTES
# -----------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "bidagent-backend",
        "message": "Backend running 🚀"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/test")
def test():
    return {"message": "CORS working ✅"}


# -----------------------------------------------------------------------------
# 🔥 TEST ENDPOINT (FOR MODEL)
# -----------------------------------------------------------------------------

@app.get("/api/embed")
def embed_test(text: str = "hello world"):
    model = get_model()
    embedding = model.encode(text)

    return {
        "text": text,
        "embedding_length": len(embedding)
    }


# -----------------------------------------------------------------------------
# 🔥 TEST ENDPOINT (FOR CHROMA)
# -----------------------------------------------------------------------------

@app.get("/api/chroma-test")
def chroma_test():
    collection = get_chroma_collection()

    return {
        "message": "ChromaDB initialized successfully",
        "collection_name": collection.name
    }


# -----------------------------------------------------------------------------
# STARTUP LOGS
# -----------------------------------------------------------------------------

@app.on_event("startup")
def startup_log():
    print("🚀 Backend started successfully")
    print("🌐 Allowed CORS origins:")
    for origin in allow_origins:
        print(f" - {origin}")

    print("⚠️ Lazy loading enabled (models not loaded at startup)")

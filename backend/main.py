import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# ✅ FIXED IMPORTS
from backend.routes.health import router as health_router
from backend.routes.go_no_go import router as go_no_go_router
from backend.routes.generate import router as generate_router
from backend.routes.knowledge import router as knowledge_router
from backend.routes.auth import router as auth_router
from backend.routes.bid import router as bid_router
from backend.routes.chat import router as chat_router
from backend.routes.sessions import router as sessions_router

load_dotenv()

app = FastAPI()

# -----------------------------------------------------------------------------
# CORS
# -----------------------------------------------------------------------------

def get_allowed_origins():
    env_origins = os.getenv("CORS_ORIGINS")

    if env_origins:
        return [o.strip() for o in env_origins.split(",")]

    return [
        "https://bidagent-frontend-raghu-ci.azurestaticapps.net",
        "https://bidagent-backend1.azurewebsites.net",
        "http://localhost:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
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
        print("🔄 Loading model...")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

# -----------------------------------------------------------------------------
# ROOT
# -----------------------------------------------------------------------------

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# -----------------------------------------------------------------------------
# STARTUP LOG
# -----------------------------------------------------------------------------

@app.on_event("startup")
def startup():
    print("🚀 Backend started")

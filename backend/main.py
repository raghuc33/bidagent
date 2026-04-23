from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

# ✅ SAFE IMPORTS (must be backend.*)
from backend.routes import (
    health_router,
    go_no_go_router,
    generate_router,
    knowledge_router,
    auth_router,
    bid_router,
    chat_router,
    sessions_router,
)

from backend.database import init_db
from backend.seed import restore_db, start_dump_scheduler

app = FastAPI()


# ✅ FAST STARTUP (non-blocking)
@app.on_event("startup")
async def startup_event():
    print("🚀 App started")

    # Keep ONLY lightweight init here
    try:
        init_db()
    except Exception as e:
        print(f"DB init error: {e}")

    # ❗ Run heavy work in background thread (NOT blocking event loop)
    asyncio.get_event_loop().run_in_executor(None, background_tasks)


def background_tasks():
    try:
        print("⚙️ Running background tasks...")
        restore_db()
        start_dump_scheduler()
        print("✅ Background tasks completed")
    except Exception as e:
        print(f"❌ Background error: {e}")


# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # simplify for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ✅ CRITICAL: HEALTH CHECK (Azure needs this FAST)
@app.get("/")
def health():
    return {"status": "ok"}


# ✅ ROUTES
app.include_router(health_router)
app.include_router(go_no_go_router, prefix="/api/v1")
app.include_router(generate_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(bid_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")


# ✅ EXISTING ROOT
@app.get("/api/v1/")
async def root():
    return {"message": "BidAgent API"}

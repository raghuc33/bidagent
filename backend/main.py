from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

# ✅ FIXED IMPORTS
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


# ✅ NON-BLOCKING STARTUP
@app.on_event("startup")
async def startup_event():
    print("🚀 App startup initiated...")
    init_db()
    asyncio.create_task(background_tasks())


async def background_tasks():
    try:
        print("⚙️ Running background tasks...")
        restore_db()
        start_dump_scheduler()
        print("✅ Background tasks done")
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


# ✅ ROUTES
app.include_router(health_router)
app.include_router(go_no_go_router, prefix="/api/v1")
app.include_router(generate_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(bid_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")


# ✅ HEALTH CHECK (CRITICAL for Azure)
@app.get("/")
async def health():
    return {"status": "running"}

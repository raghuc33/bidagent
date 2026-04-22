from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import health_router, go_no_go_router, generate_router, knowledge_router, auth_router, bid_router, chat_router, sessions_router
from database import init_db
from seed import restore_db, start_dump_scheduler

app = FastAPI()

init_db()
restore_db()
start_dump_scheduler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://bidagent.vercel.app",
        "https://bidagent-3k30s8nc5-gitmjs-projects.vercel.app",
        "https://bidagent-git-main-gitmjs-projects.vercel.app",
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(go_no_go_router, prefix="/api/v1")
app.include_router(generate_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(bid_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")


@app.get("/api/v1/")
async def root():
    return {"message": "BidAgent API"}

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load env variables (local dev)
load_dotenv()

app = FastAPI()

# -----------------------------------------------------------------------------
# CORS CONFIGURATION
# -----------------------------------------------------------------------------

def get_allowed_origins():
    env_origins = os.getenv("CORS_ORIGINS")

    if env_origins:
        return [origin.strip() for origin in env_origins.split(",")]

    # ✅ Default (Azure + optional dual hosting + local)
    return [
        # Azure Static Web App (Frontend)
        "https://bidagent-frontend-raghu-ci.azurestaticapps.net",

        # Azure App Service (Backend)
        "https://bidagent-backend1.azurewebsites.net",

        # Optional (REMOVE if not using)
        "https://your-app.vercel.app",
        "https://your-app.onrender.com",

        # Local development
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
# ROUTES
# -----------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "bidagent-backend",
        "allowed_origins": allow_origins
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/test")
def test():
    return {"message": "CORS working ✅"}


# -----------------------------------------------------------------------------
# STARTUP LOGS (VISIBLE IN AZURE LOG STREAM)
# -----------------------------------------------------------------------------

@app.on_event("startup")
def startup_log():
    print("🚀 Backend started successfully")
    print("🌐 Allowed CORS origins:")
    for origin in allow_origins:
        print(f" - {origin}")

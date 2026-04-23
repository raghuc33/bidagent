from fastapi import FastAPI

app = FastAPI()


# ✅ MUST respond instantly (Azure health check)
@app.get("/")
def health():
    return {"status": "ok"}

from fastapi import FastAPI
from app.config import settings
app = FastAPI(title="AI Chat Support Bot")

@app.get("/")
def health_check():
    return {"status": "ok", "environment": settings.environment}
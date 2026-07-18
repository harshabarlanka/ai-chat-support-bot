from fastapi import FastAPI

from app.config import settings
from app.routers import auth, documents, search, users
app = FastAPI(title="AI Chat Support Bot")


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(documents.router)
app.include_router(search.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.environment}


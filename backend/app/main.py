from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.api.routes.ingestion import router as ingestion_router
from backend.app.api.routes.pipeline import router as pipeline_router

app = FastAPI(
    title="Lead Research & Outreach Agent",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion_router, prefix="/api/v1")
app.include_router(pipeline_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok", "env": settings.app_env}
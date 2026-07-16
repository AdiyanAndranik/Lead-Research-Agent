from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket, WebSocketDisconnect

from backend.app.core.config import settings
from backend.app.api.routes.ingestion import router as ingestion_router
from backend.app.api.routes.pipeline import router as pipeline_router
import asyncio


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


@app.websocket("/ws/pipeline/{run_id}")
async def pipeline_websocket(websocket: WebSocket, run_id: str):
    """
    WebSocket endpoint for real-time pipeline progress.
    Sends lead status updates every 2 seconds until run completes.
    """
    from backend.app.db.session import AsyncSessionLocal
    from backend.app.models.pipeline_run import PipelineRun
    from backend.app.models.lead import Lead
    from sqlalchemy import select
    import uuid

    await websocket.accept()
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        await websocket.close(code=1003)
        return
    
    try:
        while True:
            async with AsyncSessionLocal() as session:
                run_result = await session.execute(
                    select(PipelineRun).where(PipelineRun.id == run_uuid)
                )
                run = run_result.scalar_one_or_none()
                if not run:
                    break

                leads_result = await session.execute(
                    select(Lead).where(Lead.pipeline_run_id == run_uuid)
                )
                leads = leads_result.scalars().all()

                await websocket.send_json({
                    "run_status": run.status.value,
                    "total_leads": run.total_leads,
                    "processed_leads": run.processed_leads,
                    "leads": [
                        {
                            "id": str(l.id),
                            "company_name": l.company_name,
                            "status": l.status.value,
                        }
                        for l in leads
                    ],
                })

                if run.status.value in ("completed", "failed", "cancelled"):
                    break

            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
    
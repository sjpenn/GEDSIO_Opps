from fastapi import FastAPI
from fedops_core.settings import settings
from fedops_api.routers import opportunities, ingest, files, company, entities, agents, proposals, requirements, gates, competitive_intel, capture, proposal_content, reviews, submission, manual_upload, teams
from fedops_core.routers import pipeline
from fedops_core.db.engine import engine, Base
from starlette.middleware.cors import CORSMiddleware

app = FastAPI(
    title="FedOps API",
    description="API for Federal Opportunity Operations",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
import os

# Mount static files
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_dir = os.path.join(base_dir, "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include Routers
# Include Routers
app.include_router(opportunities.router, prefix="/api/v1/opportunities", tags=["opportunities"])
app.include_router(entities.router, prefix="/api/v1/entities", tags=["entities"])
app.include_router(files.router, prefix="/api/v1/files", tags=["files"])
app.include_router(company.router, prefix="/api/v1/company", tags=["company"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(proposals.router, prefix="/api/v1") # Proposals router already has /proposals prefix
app.include_router(requirements.router, prefix="/api/v1") # Requirements router already has /requirements prefix
app.include_router(gates.router, prefix="/api/v1") # Gates router already has /gates prefix
app.include_router(competitive_intel.router, prefix="/api/v1") # Competitive intel router already has /competitive_intel prefix
app.include_router(capture.router, prefix="/api/v1")
app.include_router(proposal_content.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(submission.router, prefix="/api/v1")
app.include_router(manual_upload.router, prefix="/api/v1", tags=["manual_upload"])
app.include_router(teams.router, prefix="/api/v1/teams", tags=["teams"])
app.include_router(pipeline.router)

@app.on_event("startup")
async def startup():
    # Create tables for demo purposes (use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/health")
def health_check():
    return {"status": "ok"}

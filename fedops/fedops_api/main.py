from fastapi import FastAPI
from fedops_core.settings import settings
from fedops_api.routers import (
    opportunities, ingest, files, company, entities, agents, proposals, 
    requirements, gates, competitive_intel, capture, proposal_content, 
    reviews, submission, manual_upload, teams, agency_intel, co_intel, 
    resumes, past_performance, workflow, vector_store, extraction
)
from fedops_core.routers import pipeline
from fedops_core.db.engine import engine, Base
from starlette.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(opportunities.router, prefix="/api/v1/opportunities", tags=["opportunities"])
app.include_router(ingest.router, prefix="/api/v1/ingest", tags=["ingest"])
app.include_router(files.router, prefix="/api/v1/files", tags=["files"])
app.include_router(company.router, prefix="/api/v1/company", tags=["company"])
app.include_router(entities.router, prefix="/api/v1/entities", tags=["entities"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(proposals.router, prefix="/api/v1/proposals", tags=["proposals"])
app.include_router(requirements.router, prefix="/api/v1/requirements", tags=["requirements"])
app.include_router(gates.router, prefix="/api/v1/gates", tags=["gates"])
app.include_router(competitive_intel.router, prefix="/api/v1/competitive-intel", tags=["competitive_intel"])
app.include_router(capture.router, prefix="/api/v1/capture", tags=["capture"])
app.include_router(proposal_content.router, prefix="/api/v1/proposal-content", tags=["proposal_content"])
app.include_router(reviews.router, prefix="/api/v1/reviews", tags=["reviews"])
app.include_router(submission.router, prefix="/api/v1/submission", tags=["submission"])
app.include_router(manual_upload.router, prefix="/api/v1/manual-upload", tags=["manual_upload"])
app.include_router(teams.router, prefix="/api/v1/teams", tags=["teams"])
app.include_router(agency_intel.router, prefix="/api/v1/agency-intel", tags=["agency-intel"])
app.include_router(co_intel.router, prefix="/api/v1/co-intel", tags=["co-intel"])
app.include_router(resumes.router, prefix="/api/v1/resumes", tags=["resumes"])
app.include_router(past_performance.router, prefix="/api/v1/past-performance", tags=["past_performance"])
app.include_router(workflow.router, prefix="/api/v1")
from fedops_api.routers import config
app.include_router(config.router, prefix="/api/v1")
app.include_router(vector_store.router, prefix="/api/v1/vector-store", tags=["vector_store"])
app.include_router(extraction.router, prefix="/api/v1/extraction", tags=["extraction"])
app.include_router(pipeline.router)

@app.on_event("startup")
async def startup():
    # Create tables for demo purposes (use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/health")
def health_check():
    return {"status": "ok"}

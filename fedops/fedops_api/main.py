from fastapi import FastAPI
from fedops_core.settings import settings
from fedops_api.routers import opportunities, entities, files, company, agents, proposals
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

# Include Routers
# Include Routers
app.include_router(opportunities.router, prefix="/api/v1/opportunities", tags=["opportunities"])
app.include_router(entities.router, prefix="/api/v1/entities", tags=["entities"])
app.include_router(files.router, prefix="/api/v1/files", tags=["files"])
app.include_router(company.router, prefix="/api/v1/company", tags=["company"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(proposals.router, prefix="/api/v1") # Proposals router already has /proposals prefix

@app.on_event("startup")
async def startup():
    # Create tables for demo purposes (use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/health")
def health_check():
    return {"status": "ok"}

from fastapi import FastAPI
from fedops_core.settings import settings
from fedops_api.routers import ingest, opportunities, company, entities
from fedops_core.db.engine import engine, Base

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Include Routers
app.include_router(ingest.router, prefix=f"{settings.API_V1_STR}/ingest", tags=["ingest"])
app.include_router(opportunities.router, prefix=f"{settings.API_V1_STR}/opportunities", tags=["opportunities"])
app.include_router(company.router, prefix=f"{settings.API_V1_STR}/company", tags=["company"])
app.include_router(entities.router, prefix=f"{settings.API_V1_STR}/entities", tags=["entities"])

@app.on_event("startup")
async def startup():
    # Create tables for demo purposes (use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/health")
def health_check():
    return {"status": "ok"}

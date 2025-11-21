# FedOps

FedOps is a data platform that manually ingests, normalizes, analyzes, and serves U.S. federal opportunities and awards.

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy (Async), Pydantic, Postgres
- **Frontend**: React, TypeScript, Vite, Tailwind CSS
- **Infrastructure**: Docker, Docker Compose

## Getting Started

1.  **Clone the repository**
2.  **Environment Variables**
    Copy `.env.example` to `.env` (created automatically by docker-compose if not present, but good to have).
    ```bash
    cp .env.example .env
    ```
3.  **Run with Docker Compose**
    ```bash
    cd fedops
    docker compose up --build
    ```

## API Documentation

Once running, access the API docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Frontend

Access the frontend at: http://localhost:5173

## Manual Ingest

You can trigger manual ingest via the API docs or the frontend console (coming soon).
Example:
```bash
curl -X POST "http://localhost:8000/ingest/sam/opportunities/run?limit=5"
```

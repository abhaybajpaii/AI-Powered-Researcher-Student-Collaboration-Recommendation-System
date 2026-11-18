from fastapi import APIRouter, status
from pydantic import BaseModel
from backend.app.db.session import verify_database_connection

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    database: dict
    version: str = "1.0.0"


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="System Health & Database Verification",
    description="Returns the operational status of the API, verifying database connectivity and vector support.",
)
async def check_health():
    db_status = await verify_database_connection()
    overall_status = "healthy" if db_status.get("connected") else "degraded"

    return HealthResponse(
        status=overall_status,
        database=db_status,
        version="1.0.0",
    )

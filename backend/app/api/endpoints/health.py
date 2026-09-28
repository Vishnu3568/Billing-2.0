from fastapi import APIRouter
from app.core.config import settings
from app.core.database import db_manager
from app.schemas.health import HealthResponse
from app import __version__

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """
    Health check endpoint returning application status, environment,
    database connectivity, and storage mode.
    """
    db_connected = db_manager.check_connection()
    return HealthResponse(
        status="ok",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        database_connected=db_connected,
        version=__version__,
        storage_type=settings.STORAGE_TYPE
    )

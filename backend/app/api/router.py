from fastapi import APIRouter
from app.api.endpoints import health, auth, companies, duty_slips, extractions

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router.include_router(duty_slips.router, prefix="/duty-slips", tags=["Duty Slips"])
api_router.include_router(extractions.router, prefix="/duty-slips", tags=["OCR Extraction"])

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database
from app.core.database import get_db
from app.services.storage.local import get_storage_service
from app.services.storage.base import BaseStorageService
from app.services.ocr.base import BaseOCRProvider
from app.services.ocr.factory import get_ocr_provider
from app.services.ocr.service import ExtractionService
from app.schemas.ocr import (
    ExtractionResponse,
    ExtractionReviewUpdateRequest,
    ExtractionVerifyRequest
)

router = APIRouter()


def get_extraction_service(
    db: Database = Depends(get_db),
    storage: BaseStorageService = Depends(get_storage_service),
    ocr_provider: BaseOCRProvider = Depends(get_ocr_provider)
) -> ExtractionService:
    return ExtractionService(db, storage, ocr_provider)


@router.post("/{duty_slip_id}/extract", response_model=ExtractionResponse, summary="Extract data from stored duty slip scans")
def extract_duty_slip(
    duty_slip_id: str,
    service: ExtractionService = Depends(get_extraction_service)
):
    try:
        return service.extract_duty_slip(duty_slip_id)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg or "does not exist" in msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)


@router.get("/{duty_slip_id}/extraction", response_model=ExtractionResponse, summary="Get extraction result for duty slip")
def get_duty_slip_extraction(
    duty_slip_id: str,
    service: ExtractionService = Depends(get_extraction_service)
):
    result = service.get_by_duty_slip_id(duty_slip_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No extraction found for duty slip '{duty_slip_id}'. Run extract first."
        )
    return result


@router.put("/{duty_slip_id}/extraction", response_model=ExtractionResponse, summary="Update extraction fields during human review")
def update_duty_slip_extraction(
    duty_slip_id: str,
    data: ExtractionReviewUpdateRequest,
    service: ExtractionService = Depends(get_extraction_service)
):
    try:
        return service.update_review_corrections(
            duty_slip_id=duty_slip_id,
            field_updates=data.fields,
            reviewer=data.reviewer or "reviewer",
            notes=data.notes
        )
    except ValueError as e:
        msg = str(e)
        if "not found" in msg or "does not exist" in msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)


@router.post("/{duty_slip_id}/verify", response_model=ExtractionResponse, summary="Approve and mark extraction as verified")
def verify_duty_slip_extraction(
    duty_slip_id: str,
    data: ExtractionVerifyRequest = ExtractionVerifyRequest(),
    service: ExtractionService = Depends(get_extraction_service)
):
    try:
        return service.verify_extraction(
            duty_slip_id=duty_slip_id,
            reviewer=data.reviewer or "reviewer",
            notes=data.notes
        )
    except ValueError as e:
        msg = str(e)
        if "not found" in msg or "does not exist" in msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)


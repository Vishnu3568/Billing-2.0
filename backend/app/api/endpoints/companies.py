from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from pymongo.database import Database
from app.core.database import get_db
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse
from app.schemas.word import CompanyMasterDocInfo
from app.services.company import CompanyService
from app.services.storage.base import BaseStorageService
from app.services.storage.local import get_storage_service
from app.services.word.service import WordBillService

router = APIRouter()


def get_company_service(db: Database = Depends(get_db)) -> CompanyService:
    return CompanyService(db)


def get_word_bill_service(
    db: Database = Depends(get_db),
    storage: BaseStorageService = Depends(get_storage_service)
) -> WordBillService:
    return WordBillService(db, storage)


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED, summary="Create a new company")
def create_company(
    data: CompanyCreate,
    service: CompanyService = Depends(get_company_service)
):
    try:
        return service.create(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.get("", response_model=List[CompanyResponse], summary="List all companies")
def list_companies(
    include_inactive: bool = Query(True, description="Include deactivated companies"),
    service: CompanyService = Depends(get_company_service)
):
    return service.list_all(include_inactive=include_inactive)


@router.get("/{company_id}", response_model=CompanyResponse, summary="Get company by ID")
def get_company(
    company_id: str,
    service: CompanyService = Depends(get_company_service)
):
    company = service.get_by_id(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID '{company_id}' not found."
        )
    return company


@router.put("/{company_id}", response_model=CompanyResponse, summary="Update company")
def update_company(
    company_id: str,
    data: CompanyUpdate,
    service: CompanyService = Depends(get_company_service)
):
    try:
        updated = service.update(company_id, data)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company with ID '{company_id}' not found."
            )
        return updated
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.delete("/{company_id}", response_model=CompanyResponse, summary="Deactivate company")
def deactivate_company(
    company_id: str,
    service: CompanyService = Depends(get_company_service)
):
    company = service.deactivate(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID '{company_id}' not found."
        )
    return company


# --------------------------------------------------------------------------
# COMPANY MASTER WORD & PDF DOCUMENT ENDPOINTS
# --------------------------------------------------------------------------

@router.get("/{company_id}/document/info", response_model=CompanyMasterDocInfo, summary="Get company master document info")
def get_company_master_info(
    company_id: str,
    service: WordBillService = Depends(get_word_bill_service)
):
    info = service.get_company_master_info(company_id)
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID '{company_id}' not found."
        )
    return info


@router.get("/{company_id}/document/word", summary="Download Company Master Word (.docx) document")
def download_company_master_docx(
    company_id: str,
    service: WordBillService = Depends(get_word_bill_service)
):
    result = service.get_company_master_docx(company_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Master Word document for company '{company_id}' not found. Generate verified bills first."
        )
    file_bytes, filename = result
    return Response(
        content=file_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/{company_id}/document/pdf", summary="Stream Company Master PDF for in-browser multi-page viewer")
def view_company_master_pdf(
    company_id: str,
    service: WordBillService = Depends(get_word_bill_service)
):
    pdf_bytes = service.get_company_master_pdf(company_id)
    if not pdf_bytes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unable to render PDF preview for company '{company_id}'. Ensure Word document exists."
        )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=master_billing_preview.pdf"}
    )

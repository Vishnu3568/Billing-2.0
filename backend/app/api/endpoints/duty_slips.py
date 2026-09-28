from typing import List, Optional
from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    status, 
    UploadFile, 
    File, 
    Form, 
    Query, 
    Response
)
from pymongo.database import Database
from app.core.database import get_db
from app.services.storage.local import get_storage_service
from app.services.storage.base import BaseStorageService
from app.services.duty_slip import DutySlipService
from app.schemas.duty_slip import DutySlipResponse, DutySlipUpdate

router = APIRouter()


def get_duty_slip_service(
    db: Database = Depends(get_db),
    storage: BaseStorageService = Depends(get_storage_service)
) -> DutySlipService:
    return DutySlipService(db, storage)


@router.post("", response_model=DutySlipResponse, status_code=status.HTTP_201_CREATED, summary="Create and upload duty slip (Front required, Back optional)")
async def create_duty_slip(
    company_id: str = Form(..., description="Target company ID"),
    duty_slip_no: str = Form(..., description="Plain numeric duty slip number (e.g. 1, 2, 3)"),
    notes: Optional[str] = Form(None, description="Optional notes"),
    front_file: UploadFile = File(..., description="Front scan image or PDF (Required)"),
    back_file: Optional[UploadFile] = File(None, description="Back scan image or PDF (Optional)"),
    service: DutySlipService = Depends(get_duty_slip_service)
):
    try:
        front_bytes = await front_file.read()
        back_bytes = None
        back_filename = None
        back_content_type = None

        if back_file and back_file.filename:
            back_bytes = await back_file.read()
            if len(back_bytes) > 0:
                back_filename = back_file.filename
                back_content_type = back_file.content_type or "image/jpeg"
            else:
                back_bytes = None

        return service.create_duty_slip(
            company_id_str=company_id,
            duty_slip_no=duty_slip_no,
            front_filename=front_file.filename or "front_scan.jpg",
            front_content_type=front_file.content_type or "image/jpeg",
            front_bytes=front_bytes,
            back_filename=back_filename,
            back_content_type=back_content_type,
            back_bytes=back_bytes,
            notes=notes
        )
    except ValueError as e:
        msg = str(e)
        if "already exists" in msg or "already used" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        if "does not exist" in msg or "Invalid company ID" in msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("", response_model=List[DutySlipResponse], summary="List duty slips")
def list_duty_slips(
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by duty slip number"),
    service: DutySlipService = Depends(get_duty_slip_service)
):
    return service.list_duty_slips(
        company_id_str=company_id,
        status_filter=status,
        search_query=search
    )


@router.get("/{duty_slip_id}", response_model=DutySlipResponse, summary="Get duty slip metadata")
def get_duty_slip(
    duty_slip_id: str,
    service: DutySlipService = Depends(get_duty_slip_service)
):
    ds = service.get_by_id(duty_slip_id)
    if not ds:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Duty slip with ID '{duty_slip_id}' not found."
        )
    return ds


@router.put("/{duty_slip_id}", response_model=DutySlipResponse, summary="Update duty slip metadata")
def update_duty_slip(
    duty_slip_id: str,
    data: DutySlipUpdate,
    service: DutySlipService = Depends(get_duty_slip_service)
):
    try:
        updated = service.update_metadata(duty_slip_id, data)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Duty slip with ID '{duty_slip_id}' not found."
            )
        return updated
    except ValueError as e:
        msg = str(e)
        if "already used" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)


@router.get("/{duty_slip_id}/front", summary="Retrieve front scan file")
def get_front_scan(
    duty_slip_id: str,
    service: DutySlipService = Depends(get_duty_slip_service)
):
    result = service.get_scan_file(duty_slip_id, side="front")
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Front scan for duty slip ID '{duty_slip_id}' not found."
        )
    file_bytes, content_type, filename = result
    return Response(
        content=file_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'}
    )


@router.get("/{duty_slip_id}/back", summary="Retrieve back scan file")
def get_back_scan(
    duty_slip_id: str,
    service: DutySlipService = Depends(get_duty_slip_service)
):
    result = service.get_scan_file(duty_slip_id, side="back")
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No back scan attached to duty slip ID '{duty_slip_id}'."
        )
    file_bytes, content_type, filename = result
    return Response(
        content=file_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'}
    )


from app.services.word import WordBillService
from app.schemas.word import WordBillResponse, WordBillGenerateRequest


def get_word_bill_service(
    db: Database = Depends(get_db),
    storage: BaseStorageService = Depends(get_storage_service)
) -> WordBillService:
    return WordBillService(db, storage)


@router.post("/{duty_slip_id}/generate-word", response_model=WordBillResponse, summary="Generate Word (.docx) billing document from verified extraction")
def generate_word_bill(
    duty_slip_id: str,
    payload: Optional[WordBillGenerateRequest] = None,
    service: WordBillService = Depends(get_word_bill_service)
):
    bill_no = payload.bill_no if payload else None
    try:
        return service.generate_word_bill(duty_slip_id, bill_no=bill_no)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg or "does not exist" in msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)


@router.get("/{duty_slip_id}/word-bill", summary="Download generated Word (.docx) billing document")
def download_word_bill(
    duty_slip_id: str,
    service: WordBillService = Depends(get_word_bill_service)
):
    result = service.get_word_bill_file(duty_slip_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Word bill for duty slip '{duty_slip_id}' not found. Generate it first."
        )
    file_bytes, filename = result
    return Response(
        content=file_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.delete("/{duty_slip_id}", summary="Delete duty slip")
def delete_duty_slip(
    duty_slip_id: str,
    service: DutySlipService = Depends(get_duty_slip_service)
):
    deleted = service.delete_duty_slip(duty_slip_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Duty slip with ID '{duty_slip_id}' not found."
        )
    return {"status": "ok", "message": f"Duty slip '{duty_slip_id}' deleted."}


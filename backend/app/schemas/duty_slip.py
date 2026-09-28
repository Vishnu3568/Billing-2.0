from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class ScanMetadata(BaseModel):
    original_filename: str
    stored_filename: str
    storage_path: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime
    url: Optional[str] = None


class DutySlipBase(BaseModel):
    duty_slip_no: str = Field(..., description="Duty slip number (e.g. 1, 2, 3)", min_length=1, max_length=100)
    company_id: str = Field(..., description="Referenced company ID")
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator("duty_slip_no")
    @classmethod
    def validate_duty_slip_no(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Duty slip number cannot be empty or only whitespace")
        return cleaned


class DutySlipUpdate(BaseModel):
    duty_slip_no: Optional[str] = Field(None, min_length=1, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, min_length=1, max_length=50)

    @field_validator("duty_slip_no")
    @classmethod
    def validate_optional_duty_slip_no(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Duty slip number cannot be empty or only whitespace")
            return cleaned
        return v


class DutySlipResponse(BaseModel):
    id: str
    company_id: str
    company_name: Optional[str] = None
    duty_slip_no: str
    front_scan: ScanMetadata
    back_scan: Optional[ScanMetadata] = None
    has_back_scan: bool = False
    has_word_bill: bool = False
    word_bill_url: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


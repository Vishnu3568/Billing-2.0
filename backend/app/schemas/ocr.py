from pydantic import BaseModel, Field
from typing import Optional, List, Union
from datetime import datetime


class ExtractedField(BaseModel):
    value: Optional[Union[str, int, float]] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    needs_review: bool = False
    review_reason: Optional[str] = None
    raw_text: Optional[str] = None
    source_side: Optional[str] = None  # "front", "back", "both"
    original_value: Optional[Union[str, int, float]] = None
    edited: bool = False
    edited_at: Optional[datetime] = None
    edited_by: Optional[str] = None


class FieldAuditEntry(BaseModel):
    field_name: str
    original_value: Optional[Union[str, int, float]] = None
    corrected_value: Optional[Union[str, int, float]] = None
    edited_at: datetime
    edited_by: str = "reviewer"
    notes: Optional[str] = None


class DutySlipExtractedFields(BaseModel):
    # Front-side transport metadata
    duty_slip_no: ExtractedField = Field(default_factory=ExtractedField)
    date: ExtractedField = Field(default_factory=ExtractedField)
    driver_name: ExtractedField = Field(default_factory=ExtractedField)
    vehicle_number: ExtractedField = Field(default_factory=ExtractedField)
    meter_start: ExtractedField = Field(default_factory=ExtractedField)
    meter_return: ExtractedField = Field(default_factory=ExtractedField)
    total_km: ExtractedField = Field(default_factory=ExtractedField)
    starting_time: ExtractedField = Field(default_factory=ExtractedField)
    closing_time: ExtractedField = Field(default_factory=ExtractedField)
    extra_km: ExtractedField = Field(default_factory=ExtractedField)
    extra_hours: ExtractedField = Field(default_factory=ExtractedField)
    reporting_place: ExtractedField = Field(default_factory=ExtractedField)
    tour_location: ExtractedField = Field(default_factory=ExtractedField)
    party_name: ExtractedField = Field(default_factory=ExtractedField)
    customer_name: ExtractedField = Field(default_factory=ExtractedField)
    remarks: ExtractedField = Field(default_factory=ExtractedField)

    # Back-side handwritten billing calculation line-items (as document values)
    base_package: ExtractedField = Field(default_factory=ExtractedField)      # e.g. "8/80 = 2500"
    extra_km_charge: ExtractedField = Field(default_factory=ExtractedField)   # e.g. "67 x 15 = 1005"
    extra_hour_charge: ExtractedField = Field(default_factory=ExtractedField) # e.g. "1.5 x 150 = 225"
    bata: ExtractedField = Field(default_factory=ExtractedField)              # e.g. "250"
    toll: ExtractedField = Field(default_factory=ExtractedField)              # e.g. "40"
    total_amount: ExtractedField = Field(default_factory=ExtractedField)      # e.g. "4020"


class CalculatedValidationSummary(BaseModel):
    calculated_total_km: Optional[float] = None
    calculated_total_hours: Optional[float] = None
    calculated_extra_km: Optional[float] = None
    calculated_extra_hours: Optional[float] = None
    calculated_extra_km_amount: Optional[float] = None
    calculated_extra_hour_amount: Optional[float] = None
    calculated_total_amount: Optional[float] = None
    is_km_consistent: bool = True
    is_time_consistent: bool = True
    is_math_consistent: bool = True


class ExtractionReviewUpdateRequest(BaseModel):
    fields: dict
    reviewer: Optional[str] = "reviewer"
    notes: Optional[str] = None


class ExtractionVerifyRequest(BaseModel):
    reviewer: Optional[str] = "reviewer"
    notes: Optional[str] = None


class ExtractionResponse(BaseModel):
    id: str
    duty_slip_id: str
    company_id: str
    stored_duty_slip_no: Optional[str] = None
    status: str  # "pending", "processing", "completed", "needs_review", "verified"
    fields: DutySlipExtractedFields
    validation_summary: Optional[CalculatedValidationSummary] = None
    overall_confidence: float
    needs_review: bool
    review_reasons: List[str] = Field(default_factory=list)
    raw_extracted_text: Optional[str] = None
    provider_used: str
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    audit_log: List[FieldAuditEntry] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


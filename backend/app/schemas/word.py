from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class WordBillGenerateRequest(BaseModel):
    bill_no: Optional[str] = None


class WordBillResponse(BaseModel):
    duty_slip_id: str
    company_id: str
    company_name: Optional[str] = None
    duty_slip_no: str
    bill_no: Optional[str] = None
    filename: str
    storage_path: str
    download_url: str
    company_master_doc_url: str
    pdf_preview_url: str
    file_size_bytes: int
    total_bills_in_doc: int
    customer_name: Optional[str] = None
    total_amount: Optional[float] = None
    amount_in_words: Optional[str] = None
    generated_at: datetime


class CompanyBillItem(BaseModel):
    duty_slip_id: str
    duty_slip_no: str
    bill_no: str
    bill_date: Optional[str] = None
    customer_name: Optional[str] = None
    total_amount: Optional[float] = None
    generated_at: Optional[datetime] = None


class CompanyMasterDocInfo(BaseModel):
    company_id: str
    company_name: str
    has_master_doc: bool
    filename: Optional[str] = None
    docx_url: Optional[str] = None
    pdf_url: Optional[str] = None
    total_bills: int = 0
    bills: List[CompanyBillItem] = []
    updated_at: Optional[datetime] = None


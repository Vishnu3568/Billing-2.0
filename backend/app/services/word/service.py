import logging
import io
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
from pymongo.collection import Collection
from pymongo.database import Database

from app.schemas.word import WordBillResponse, CompanyMasterDocInfo, CompanyBillItem
from app.services.storage.base import BaseStorageService
from app.services.word.generator import WordBillGenerator
from app.services.word.num_to_words import amount_to_words_inr
from app.services.word.converter import convert_docx_bytes_to_pdf_bytes

logger = logging.getLogger(__name__)


class WordBillService:
    """
    Service for managing authoritative Company Master Word Documents (.docx),
    appending multi-page verified bills, and rendering server-side PDF representations.
    """

    def __init__(self, db: Database, storage: BaseStorageService):
        self.db = db
        self.storage = storage
        self.duty_slips_collection: Collection = db["duty_slips"]
        self.extractions_collection: Collection = db["extractions"]
        self.companies_collection: Collection = db["companies"]

    def generate_word_bill(
        self,
        duty_slip_id_str: str,
        bill_no: Optional[str] = None
    ) -> WordBillResponse:
        """
        Generate a bill page from a VERIFIED duty slip extraction and append/insert it
        into the authoritative Company Master Word Document.
        """
        if not ObjectId.is_valid(duty_slip_id_str):
            raise ValueError(f"Invalid duty slip ID format: '{duty_slip_id_str}'.")

        ds_id = ObjectId(duty_slip_id_str)
        duty_slip = self.duty_slips_collection.find_one({"_id": ds_id})
        if not duty_slip:
            raise ValueError(f"Duty slip with ID '{duty_slip_id_str}' not found.")

        extraction = self.extractions_collection.find_one({"duty_slip_id": ds_id})
        if not extraction:
            raise ValueError(
                f"No extraction found for duty slip '{duty_slip_id_str}'. Run OCR and review first."
            )

        # Enforce strict verification requirement
        extraction_status = extraction.get("status")
        if extraction_status != "verified":
            raise ValueError(
                f"Cannot generate Word bill: Duty slip extraction status is '{extraction_status}'. "
                "Extraction must be 'verified' through human review before generating bills."
            )

        # Retrieve company details
        company_id = duty_slip["company_id"]
        company = self.companies_collection.find_one({"_id": company_id})
        company_name = company["name"] if company else "Company"

        fields_dict = extraction.get("fields", {})
        val_summary = extraction.get("validation_summary", {})
        total_hours = val_summary.get("calculated_total_hours")
        duty_slip_no = str(duty_slip["duty_slip_no"])
        now = datetime.now(timezone.utc)

        # ----------------------------------------------------
        # BILL NUMBERING LOGIC
        # ----------------------------------------------------
        if not bill_no:
            # Count existing generated bills for this company
            existing_count = self.duty_slips_collection.count_documents({
                "company_id": company_id,
                "has_word_bill": True,
                "_id": {"$ne": ds_id}
            })
            bill_no = f"Bill {existing_count + 1:02d}"

        # ----------------------------------------------------
        # COMPANY MASTER DOCUMENT STORAGE & UPDATE
        # ----------------------------------------------------
        # Sanitized company filename for master document
        safe_company_name = "".join(c for c in company_name if c.isalnum() or c in (" ", "_", "-")).strip()
        if not safe_company_name:
            safe_company_name = "Company"
        master_filename = f"{safe_company_name}.docx"
        master_storage_path = f"companies/{str(company_id)}/master/{master_filename}"

        # Fetch existing master document if present
        existing_master_bytes = self.storage.get_file(master_storage_path)

        # Generate or append bill page to master document
        updated_master_bytes = WordBillGenerator.create_or_append_bill_to_master(
            existing_docx_bytes=existing_master_bytes,
            duty_slip_no=duty_slip_no,
            fields_dict=fields_dict,
            company_name=company_name,
            bill_no=bill_no,
            total_hours=total_hours,
        )

        # Save authoritative company master DOCX back to storage
        self.storage.save_file(updated_master_bytes, master_storage_path)

        # Compute total bills in document
        total_bills_in_doc = self.duty_slips_collection.count_documents({
            "company_id": company_id,
            "has_word_bill": True,
            "_id": {"$ne": ds_id}
        }) + 1

        # Update duty slip metadata
        self.duty_slips_collection.update_one(
            {"_id": ds_id},
            {
                "$set": {
                    "has_word_bill": True,
                    "word_bill": {
                        "stored_filename": master_filename,
                        "storage_path": master_storage_path,
                        "bill_no": bill_no,
                        "generated_at": now,
                    },
                    "updated_at": now,
                }
            },
        )

        # Update company metadata
        self.companies_collection.update_one(
            {"_id": company_id},
            {
                "$set": {
                    "master_document": {
                        "filename": master_filename,
                        "storage_path": master_storage_path,
                        "total_bills": total_bills_in_doc,
                        "last_bill_no": bill_no,
                        "updated_at": now,
                    },
                    "updated_at": now,
                }
            }
        )

        total_val = fields_dict.get("total_amount", {}).get("value")
        cust_name = fields_dict.get("customer_name", {}).get("value")
        amt_words = amount_to_words_inr(total_val)

        return WordBillResponse(
            duty_slip_id=duty_slip_id_str,
            company_id=str(company_id),
            company_name=company_name,
            duty_slip_no=duty_slip_no,
            bill_no=bill_no,
            filename=master_filename,
            storage_path=master_storage_path,
            download_url=f"/api/v1/companies/{str(company_id)}/document/word",
            company_master_doc_url=f"/api/v1/companies/{str(company_id)}/document/word",
            pdf_preview_url=f"/api/v1/companies/{str(company_id)}/document/pdf",
            file_size_bytes=len(updated_master_bytes),
            total_bills_in_doc=total_bills_in_doc,
            customer_name=str(cust_name) if cust_name else None,
            total_amount=float(total_val) if total_val is not None else None,
            amount_in_words=amt_words,
            generated_at=now,
        )

    def get_company_master_docx(self, company_id_str: str) -> Optional[Tuple[bytes, str]]:
        """
        Retrieve authoritative Company Master DOCX bytes and filename for download.
        """
        if not ObjectId.is_valid(company_id_str):
            return None

        comp_id = ObjectId(company_id_str)
        company = self.companies_collection.find_one({"_id": comp_id})
        if not company:
            return None

        safe_name = "".join(c for c in company["name"] if c.isalnum() or c in (" ", "_", "-")).strip() or "Company"
        filename = f"{safe_name}.docx"
        storage_path = f"companies/{company_id_str}/master/{filename}"

        file_bytes = self.storage.get_file(storage_path)
        if not file_bytes:
            return None

        return file_bytes, filename

    def get_company_master_pdf(self, company_id_str: str) -> Optional[bytes]:
        """
        Renders the authoritative Company Master DOCX to PDF for in-browser multi-page viewing.
        """
        result = self.get_company_master_docx(company_id_str)
        if not result:
            return None
        docx_bytes, _ = result
        return convert_docx_bytes_to_pdf_bytes(docx_bytes)

    def get_company_master_info(self, company_id_str: str) -> Optional[CompanyMasterDocInfo]:
        """
        Get metadata about a company's master document and its contained bills.
        """
        if not ObjectId.is_valid(company_id_str):
            return None

        comp_id = ObjectId(company_id_str)
        company = self.companies_collection.find_one({"_id": comp_id})
        if not company:
            return None

        master_doc = company.get("master_document")
        has_doc = master_doc is not None
        safe_name = "".join(c for c in company["name"] if c.isalnum() or c in (" ", "_", "-")).strip() or "Company"
        filename = f"{safe_name}.docx" if has_doc else None

        # Fetch all bills belonging to this company
        bills_data: List[CompanyBillItem] = []
        slips_with_bills = list(self.duty_slips_collection.find(
            {"company_id": comp_id, "has_word_bill": True}
        ))
        for s in slips_with_bills:
            wb = s.get("word_bill", {})
            ext = self.extractions_collection.find_one({"duty_slip_id": s["_id"]})
            fields = ext.get("fields", {}) if ext else {}
            
            raw_amt = fields.get("total_amount", {}).get("value")
            parsed_amt = None
            if raw_amt is not None:
                try:
                    parsed_amt = float(raw_amt)
                except (ValueError, TypeError):
                    parsed_amt = None

            bills_data.append(CompanyBillItem(
                duty_slip_id=str(s["_id"]),
                duty_slip_no=str(s.get("duty_slip_no", "")),
                bill_no=str(wb.get("bill_no") or "Bill"),
                bill_date=str(fields.get("date", {}).get("value") or ""),
                customer_name=str(fields.get("customer_name", {}).get("value") or ""),
                total_amount=parsed_amt,
                generated_at=wb.get("generated_at")
            ))

        # Sort bills by bill_no
        bills_data.sort(key=lambda b: b.bill_no)

        return CompanyMasterDocInfo(
            company_id=company_id_str,
            company_name=company["name"],
            has_master_doc=has_doc,
            filename=filename,
            docx_url=f"/api/v1/companies/{company_id_str}/document/word" if has_doc else None,
            pdf_url=f"/api/v1/companies/{company_id_str}/document/pdf" if has_doc else None,
            total_bills=len(bills_data) if bills_data else (master_doc.get("total_bills", 0) if master_doc else 0),
            bills=bills_data,
            updated_at=master_doc.get("updated_at") if master_doc else None,
        )


    def get_word_bill_file(self, duty_slip_id_str: str) -> Optional[Tuple[bytes, str]]:
        """
        Legacy/duty slip direct endpoint: retrieves the company master document containing this bill.
        """
        if not ObjectId.is_valid(duty_slip_id_str):
            return None

        ds_id = ObjectId(duty_slip_id_str)
        duty_slip = self.duty_slips_collection.find_one({"_id": ds_id})
        if not duty_slip or not duty_slip.get("word_bill"):
            return None

        return self.get_company_master_docx(str(duty_slip["company_id"]))

import logging
from typing import Optional
from datetime import datetime, timezone
from bson import ObjectId
from pymongo.collection import Collection
from pymongo.database import Database
from app.schemas.ocr import ExtractionResponse, DutySlipExtractedFields
from app.services.ocr.base import BaseOCRProvider
from app.services.ocr.validator import normalize_and_validate_extraction
from app.services.storage.base import BaseStorageService


logger = logging.getLogger(__name__)


class ExtractionService:
    def __init__(self, db: Database, storage: BaseStorageService, ocr_provider: BaseOCRProvider):
        self.db = db
        self.storage = storage
        self.ocr_provider = ocr_provider
        self.collection: Collection = db["extractions"]
        self.duty_slips_collection: Collection = db["duty_slips"]
        self.ensure_indexes()

    def ensure_indexes(self) -> None:
        """Create unique index on duty_slip_id."""
        try:
            self.collection.create_index([("duty_slip_id", 1)], unique=True, name="unique_duty_slip_extraction")
        except Exception as e:
            logger.error("Failed to create extraction indexes: %s", str(e))

    def _doc_to_response(self, doc: dict) -> ExtractionResponse:
        stored_no = doc.get("stored_duty_slip_no")
        if not stored_no:
            ds = self.duty_slips_collection.find_one({"_id": doc["duty_slip_id"]})
            if ds:
                stored_no = ds.get("duty_slip_no")

        return ExtractionResponse(
            id=str(doc["_id"]),
            duty_slip_id=str(doc["duty_slip_id"]),
            company_id=str(doc["company_id"]),
            stored_duty_slip_no=stored_no,
            status=doc.get("status", "completed"),
            fields=doc["fields"],
            validation_summary=doc.get("validation_summary"),
            overall_confidence=doc.get("overall_confidence", 0.0),
            needs_review=doc.get("needs_review", False),
            review_reasons=doc.get("review_reasons", []),
            raw_extracted_text=doc.get("raw_extracted_text"),
            provider_used=doc.get("provider_used", "unknown"),
            verified_at=doc.get("verified_at"),
            verified_by=doc.get("verified_by"),
            audit_log=doc.get("audit_log", []),
            created_at=doc.get("created_at", datetime.now(timezone.utc)),
            updated_at=doc.get("updated_at", datetime.now(timezone.utc))
        )

    def extract_duty_slip(self, duty_slip_id_str: str) -> ExtractionResponse:
        if not ObjectId.is_valid(duty_slip_id_str):
            raise ValueError(f"Invalid duty slip ID format: '{duty_slip_id_str}'.")

        ds_id = ObjectId(duty_slip_id_str)
        duty_slip = self.duty_slips_collection.find_one({"_id": ds_id})
        if not duty_slip:
            raise ValueError(f"Duty slip with ID '{duty_slip_id_str}' not found.")

        # Retrieve front scan file from storage
        front_path = duty_slip["front_scan"]["storage_path"]
        front_mime = duty_slip["front_scan"]["content_type"]

        front_bytes = self.storage.get_file(front_path)
        if front_bytes is None:
            raise ValueError(f"Front scan file at '{front_path}' could not be read from storage.")

        # Optional back scan
        has_back = bool(duty_slip.get("has_back_scan")) or (duty_slip.get("back_scan") is not None)
        back_bytes = None
        back_mime = None
        if has_back and duty_slip.get("back_scan"):
            back_path = duty_slip["back_scan"]["storage_path"]
            back_mime = duty_slip["back_scan"]["content_type"]
            back_bytes = self.storage.get_file(back_path)
            if back_bytes is None:
                raise ValueError(f"Back scan file at '{back_path}' could not be read from storage.")

        # Execute OCR Provider
        raw_result = self.ocr_provider.extract(
            front_bytes=front_bytes,
            front_content_type=front_mime,
            back_bytes=back_bytes,
            back_content_type=back_mime
        )

        if raw_result.error:
            raise ValueError(f"OCR Extraction failed: {raw_result.error}")

        # Normalize and Validate
        fields_obj, val_summary, overall_conf, needs_review, review_reasons = normalize_and_validate_extraction(
            raw_fields=raw_result.extracted_fields,
            stored_duty_slip_no=duty_slip["duty_slip_no"],
            has_back_scan=has_back
        )

        status_str = "needs_review" if needs_review else "completed"
        now = datetime.now(timezone.utc)

        doc = {
            "duty_slip_id": ds_id,
            "company_id": duty_slip["company_id"],
            "stored_duty_slip_no": duty_slip["duty_slip_no"],
            "status": status_str,
            "fields": fields_obj.model_dump(),
            "validation_summary": val_summary.model_dump(),
            "overall_confidence": overall_conf,
            "needs_review": needs_review,
            "review_reasons": review_reasons,
            "raw_extracted_text": raw_result.raw_text,
            "provider_used": raw_result.provider_name,
            "verified_at": None,
            "verified_by": None,
            "audit_log": [],
            "updated_at": now
        }

        # Upsert extraction document
        res = self.collection.find_one_and_update(
            {"duty_slip_id": ds_id},
            {
                "$set": doc,
                "$setOnInsert": {"created_at": now}
            },
            upsert=True,
            return_document=True
        )

        # Update duty slip status
        self.duty_slips_collection.update_one(
            {"_id": ds_id},
            {"$set": {"status": "needs_review" if needs_review else "extracted", "updated_at": now}}
        )

        return self._doc_to_response(res)

    def update_review_corrections(
        self,
        duty_slip_id: str,
        field_updates: dict,
        reviewer: str = "reviewer",
        notes: Optional[str] = None
    ) -> ExtractionResponse:
        if not ObjectId.is_valid(duty_slip_id):
            raise ValueError(f"Invalid duty slip ID format: '{duty_slip_id}'.")

        ds_id = ObjectId(duty_slip_id)
        extraction = self.collection.find_one({"duty_slip_id": ds_id})
        if not extraction:
            raise ValueError(f"No extraction found for duty slip '{duty_slip_id}'. Run extract first.")

        duty_slip = self.duty_slips_collection.find_one({"_id": ds_id})
        if not duty_slip:
            raise ValueError(f"Duty slip '{duty_slip_id}' not found.")

        current_fields_dict = extraction.get("fields", {})
        audit_entries = extraction.get("audit_log", [])
        now = datetime.now(timezone.utc)

        # Apply updates while preserving original OCR metadata
        for field_name, new_val in field_updates.items():
            if field_name not in DutySlipExtractedFields.model_fields:
                continue

            current_field_data = current_fields_dict.get(field_name, {})
            current_val = current_field_data.get("value")

            # Check if this field had an original value recorded
            orig_val = current_field_data.get("original_value")
            if orig_val is None and not current_field_data.get("edited", False):
                orig_val = current_val

            # Check if value changed
            if new_val != current_val:
                audit_entry = {
                    "field_name": field_name,
                    "original_value": orig_val,
                    "corrected_value": new_val,
                    "edited_at": now,
                    "edited_by": reviewer,
                    "notes": notes
                }
                audit_entries.append(audit_entry)

                current_fields_dict[field_name] = {
                    "value": new_val,
                    "confidence": 1.0 if new_val is not None else 0.0,
                    "needs_review": False if new_val is not None else True,
                    "review_reason": None if new_val is not None else "manually_set_null",
                    "raw_text": current_field_data.get("raw_text"),
                    "source_side": current_field_data.get("source_side", "front"),
                    "original_value": orig_val,
                    "edited": True,
                    "edited_at": now,
                    "edited_by": reviewer
                }

        # Re-run consistency validation
        has_back = bool(duty_slip.get("has_back_scan")) or (duty_slip.get("back_scan") is not None)
        fields_obj, val_summary, overall_conf, needs_review, review_reasons = normalize_and_validate_extraction(
            raw_fields=current_fields_dict,
            stored_duty_slip_no=duty_slip["duty_slip_no"],
            has_back_scan=has_back
        )

        status_str = "verified" if extraction.get("status") == "verified" else ("needs_review" if needs_review else "extracted")


        updated_doc = self.collection.find_one_and_update(
            {"duty_slip_id": ds_id},
            {
                "$set": {
                    "fields": fields_obj.model_dump(),
                    "validation_summary": val_summary.model_dump(),
                    "overall_confidence": overall_conf,
                    "needs_review": needs_review,
                    "review_reasons": review_reasons,
                    "audit_log": audit_entries,
                    "status": status_str,
                    "updated_at": now
                }
            },
            return_document=True
        )

        self.duty_slips_collection.update_one(
            {"_id": ds_id},
            {"$set": {"status": status_str, "updated_at": now}}
        )

        return self._doc_to_response(updated_doc)

    def verify_extraction(
        self,
        duty_slip_id: str,
        reviewer: str = "reviewer",
        notes: Optional[str] = None
    ) -> ExtractionResponse:
        if not ObjectId.is_valid(duty_slip_id):
            raise ValueError(f"Invalid duty slip ID format: '{duty_slip_id}'.")

        ds_id = ObjectId(duty_slip_id)
        extraction = self.collection.find_one({"duty_slip_id": ds_id})
        if not extraction:
            raise ValueError(f"No extraction found for duty slip '{duty_slip_id}'. Run extract first.")


        fields = extraction.get("fields", {})
        val_summary = extraction.get("validation_summary", {})

        # 1. Validate required fields
        required_fields = [
            "date",
            "driver_name",
            "vehicle_number",
            "meter_start",
            "meter_return",
            "total_km",
            "starting_time",
            "closing_time",
        ]
        missing_fields = []
        for rf in required_fields:
            field_val = fields.get(rf, {}).get("value")
            if field_val is None or str(field_val).strip() == "":
                missing_fields.append(rf)

        if missing_fields:
            raise ValueError(f"Cannot verify duty slip: Required fields missing or unreadable ({', '.join(missing_fields)}).")

        # 2. Check validation consistency checks
        if not val_summary.get("is_km_consistent", True):
            raise ValueError("Cannot verify duty slip: KM consistency conflict (total_km != meter_return - meter_start).")
        if not val_summary.get("is_time_consistent", True):
            raise ValueError("Cannot verify duty slip: Time consistency conflict (extra_hours != closing_time - starting_time - 8hr).")
        if not val_summary.get("is_math_consistent", True):
            raise ValueError("Cannot verify duty slip: Math charge conflict (total_amount does not match sum of charges).")

        # 3. Check for any unresolved validation failures
        if extraction.get("needs_review"):
            reasons = extraction.get("review_reasons", [])
            # If there are unresolved package validation failures
            if any("validation_failure" in r for r in reasons):
                raise ValueError(f"Cannot verify duty slip: Unresolved review conflicts ({', '.join(reasons)}).")


        now = datetime.now(timezone.utc)
        update_doc = {
            "status": "verified",
            "needs_review": False,
            "review_reasons": [],
            "verified_at": now,
            "verified_by": reviewer,
            "updated_at": now
        }

        res = self.collection.find_one_and_update(
            {"duty_slip_id": ds_id},
            {"$set": update_doc},
            return_document=True
        )

        self.duty_slips_collection.update_one(
            {"_id": ds_id},
            {"$set": {"status": "verified", "updated_at": now}}
        )

        return self._doc_to_response(res)

    def get_by_duty_slip_id(self, duty_slip_id_str: str) -> Optional[ExtractionResponse]:
        if not ObjectId.is_valid(duty_slip_id_str):
            return None
        doc = self.collection.find_one({"duty_slip_id": ObjectId(duty_slip_id_str)})
        if not doc:
            return None
        return self._doc_to_response(doc)

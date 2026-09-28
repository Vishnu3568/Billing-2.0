import logging
import uuid
from typing import List, Optional, Tuple
from datetime import datetime, timezone
from pathlib import Path
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.collation import Collation
from app.schemas.duty_slip import DutySlipResponse, DutySlipUpdate, ScanMetadata
from app.services.storage.base import BaseStorageService

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/jpg",
    "application/pdf",
    "image/pjpeg"
}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB


class DutySlipService:
    def __init__(self, db: Database, storage: BaseStorageService):
        self.db = db
        self.storage = storage
        self.collection: Collection = db["duty_slips"]
        self.companies_collection: Collection = db["companies"]
        self.ensure_indexes()

    def ensure_indexes(self) -> None:
        """Create compound unique index on (company_id, duty_slip_no)."""
        try:
            self.collection.create_index(
                [("company_id", 1), ("duty_slip_no", 1)],
                unique=True,
                collation=Collation(locale="en", strength=2),
                name="unique_company_duty_slip_no"
            )
        except Exception as e:
            logger.warning("Collation index creation failed, falling back to standard index: %s", str(e))
            try:
                self.collection.create_index(
                    [("company_id", 1), ("duty_slip_no", 1)],
                    unique=True,
                    name="unique_company_duty_slip_no_std"
                )
            except Exception as ex:
                logger.error("Failed to create duty slip indexes: %s", str(ex))

    def _get_company_name(self, company_id: ObjectId) -> Optional[str]:
        company = self.companies_collection.find_one({"_id": company_id})
        return company["name"] if company else None

    def _doc_to_response(self, doc: dict) -> DutySlipResponse:
        company_id_obj = doc["company_id"]
        company_name = self._get_company_name(company_id_obj)
        ds_id_str = str(doc["_id"])

        front_meta = doc["front_scan"]
        back_meta = doc.get("back_scan")

        back_scan_obj = None
        if back_meta:
            back_scan_obj = ScanMetadata(
                original_filename=back_meta["original_filename"],
                stored_filename=back_meta["stored_filename"],
                storage_path=back_meta["storage_path"],
                content_type=back_meta["content_type"],
                size_bytes=back_meta["size_bytes"],
                uploaded_at=back_meta["uploaded_at"],
                url=f"/api/v1/duty-slips/{ds_id_str}/back"
            )

        has_wb = bool(doc.get("has_word_bill"))
        wb_url = f"/api/v1/duty-slips/{ds_id_str}/word-bill" if has_wb else None

        return DutySlipResponse(
            id=ds_id_str,
            company_id=str(company_id_obj),
            company_name=company_name,
            duty_slip_no=str(doc["duty_slip_no"]),
            front_scan=ScanMetadata(
                original_filename=front_meta["original_filename"],
                stored_filename=front_meta["stored_filename"],
                storage_path=front_meta["storage_path"],
                content_type=front_meta["content_type"],
                size_bytes=front_meta["size_bytes"],
                uploaded_at=front_meta["uploaded_at"],
                url=f"/api/v1/duty-slips/{ds_id_str}/front"
            ),
            back_scan=back_scan_obj,
            has_back_scan=back_scan_obj is not None,
            has_word_bill=has_wb,
            word_bill_url=wb_url,
            status=doc.get("status", "uploaded"),
            notes=doc.get("notes"),
            created_at=doc.get("created_at", datetime.now(timezone.utc)),
            updated_at=doc.get("updated_at", datetime.now(timezone.utc))
        )


    def validate_file(self, filename: str, content_type: str, file_bytes: bytes) -> str:
        """Validate file extension, mime type, and file size. Returns clean extension."""
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

        if content_type.lower() not in ALLOWED_MIME_TYPES:
            raise ValueError(f"Unsupported content type '{content_type}'.")

        if len(file_bytes) == 0:
            raise ValueError("Uploaded file cannot be empty.")

        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File size exceeds limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB.")

        return ext

    def create_duty_slip(
        self,
        company_id_str: str,
        duty_slip_no: str,
        front_filename: str,
        front_content_type: str,
        front_bytes: bytes,
        back_filename: Optional[str] = None,
        back_content_type: Optional[str] = None,
        back_bytes: Optional[bytes] = None,
        notes: Optional[str] = None
    ) -> DutySlipResponse:
        # 1. Validate Company ID
        if not ObjectId.is_valid(company_id_str):
            raise ValueError(f"Invalid company ID format: '{company_id_str}'.")
        company_id = ObjectId(company_id_str)
        company = self.companies_collection.find_one({"_id": company_id})
        if not company:
            raise ValueError(f"Company with ID '{company_id_str}' does not exist.")

        # 2. Validate Duty Slip No (plain number format)
        clean_ds_no = duty_slip_no.strip()
        if not clean_ds_no:
            raise ValueError("Duty slip number cannot be empty or only whitespace.")

        # 3. Check for existing duty slip with same number for this company
        existing = self.collection.find_one(
            {"company_id": company_id, "duty_slip_no": clean_ds_no},
            collation=Collation(locale="en", strength=2)
        )
        if existing:
            raise ValueError(f"Duty slip '{clean_ds_no}' already exists for company '{company['name']}'.")

        # 4. Validate Front File (required)
        front_ext = self.validate_file(front_filename, front_content_type, front_bytes)

        # 5. Validate Back File (optional)
        back_ext = None
        has_back = back_bytes is not None and len(back_bytes) > 0 and back_filename is not None
        if has_back:
            back_ext = self.validate_file(back_filename, back_content_type or "image/jpeg", back_bytes)

        # 6. Generate unique IDs and storage paths
        duty_slip_id = ObjectId()
        now = datetime.now(timezone.utc)
        unique_front_id = uuid.uuid4().hex[:12]
        front_stored_name = f"front_{unique_front_id}{front_ext}"
        front_storage_path = f"companies/{company_id_str}/duty_slips/{str(duty_slip_id)}/{front_stored_name}"

        # 7. Save front file
        self.storage.save_file(front_bytes, front_storage_path)

        # 8. Save back file if present
        back_doc = None
        back_storage_path = None
        if has_back:
            try:
                unique_back_id = uuid.uuid4().hex[:12]
                back_stored_name = f"back_{unique_back_id}{back_ext}"
                back_storage_path = f"companies/{company_id_str}/duty_slips/{str(duty_slip_id)}/{back_stored_name}"
                self.storage.save_file(back_bytes, back_storage_path)
                back_doc = {
                    "original_filename": back_filename,
                    "stored_filename": back_stored_name,
                    "storage_path": back_storage_path,
                    "content_type": back_content_type or "image/jpeg",
                    "size_bytes": len(back_bytes),
                    "uploaded_at": now
                }
            except Exception as e:
                self.storage.delete_file(front_storage_path)
                raise e

        # 9. Create MongoDB Document
        doc = {
            "_id": duty_slip_id,
            "company_id": company_id,
            "duty_slip_no": clean_ds_no,
            "front_scan": {
                "original_filename": front_filename,
                "stored_filename": front_stored_name,
                "storage_path": front_storage_path,
                "content_type": front_content_type,
                "size_bytes": len(front_bytes),
                "uploaded_at": now
            },
            "back_scan": back_doc,
            "has_back_scan": has_back,
            "status": "uploaded",
            "notes": notes.strip() if notes else None,
            "created_at": now,
            "updated_at": now
        }

        try:
            self.collection.insert_one(doc)
            return self._doc_to_response(doc)
        except DuplicateKeyError:
            self.storage.delete_file(front_storage_path)
            if back_storage_path:
                self.storage.delete_file(back_storage_path)
            raise ValueError(f"Duty slip '{clean_ds_no}' already exists for company '{company['name']}'.")

    def list_duty_slips(
        self,
        company_id_str: Optional[str] = None,
        status_filter: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> List[DutySlipResponse]:
        query = {}
        if company_id_str and ObjectId.is_valid(company_id_str):
            query["company_id"] = ObjectId(company_id_str)
        if status_filter:
            query["status"] = status_filter
        if search_query:
            query["duty_slip_no"] = {"$regex": search_query.strip(), "$options": "i"}

        cursor = self.collection.find(query).sort("created_at", -1)
        return [self._doc_to_response(doc) for doc in cursor]

    def get_by_id(self, duty_slip_id_str: str) -> Optional[DutySlipResponse]:
        if not ObjectId.is_valid(duty_slip_id_str):
            return None
        doc = self.collection.find_one({"_id": ObjectId(duty_slip_id_str)})
        if not doc:
            return None
        return self._doc_to_response(doc)

    def update_metadata(self, duty_slip_id_str: str, data: DutySlipUpdate) -> Optional[DutySlipResponse]:
        if not ObjectId.is_valid(duty_slip_id_str):
            return None

        update_fields = {}
        if data.duty_slip_no is not None:
            update_fields["duty_slip_no"] = data.duty_slip_no
        if data.notes is not None:
            update_fields["notes"] = data.notes
        if data.status is not None:
            update_fields["status"] = data.status

        if not update_fields:
            return self.get_by_id(duty_slip_id_str)

        update_fields["updated_at"] = datetime.now(timezone.utc)

        try:
            result = self.collection.find_one_and_update(
                {"_id": ObjectId(duty_slip_id_str)},
                {"$set": update_fields},
                return_document=True
            )
            if not result:
                return None
            return self._doc_to_response(result)
        except DuplicateKeyError:
            raise ValueError(f"Duty slip number '{data.duty_slip_no}' is already used for this company.")

    def get_scan_file(self, duty_slip_id_str: str, side: str) -> Optional[Tuple[bytes, str, str]]:
        """
        Retrieve scan bytes and content type for a given side ('front' or 'back').
        Returns (file_bytes, content_type, original_filename) or None.
        """
        if not ObjectId.is_valid(duty_slip_id_str):
            return None
        doc = self.collection.find_one({"_id": ObjectId(duty_slip_id_str)})
        if not doc:
            return None

        if side not in ("front", "back"):
            return None

        scan_meta = doc.get(f"{side}_scan")
        if not scan_meta:
            return None

        file_bytes = self.storage.get_file(scan_meta["storage_path"])
        if file_bytes is None:
            return None
        return file_bytes, scan_meta["content_type"], scan_meta["original_filename"]

    def delete_duty_slip(self, duty_slip_id_str: str) -> bool:
        if not ObjectId.is_valid(duty_slip_id_str):
            return False
        doc = self.collection.find_one({"_id": ObjectId(duty_slip_id_str)})
        if not doc:
            return False

        # Delete stored files
        if doc.get("front_scan"):
            self.storage.delete_file(doc["front_scan"]["storage_path"])
        if doc.get("back_scan"):
            self.storage.delete_file(doc["back_scan"]["storage_path"])

        # Delete database record
        res = self.collection.delete_one({"_id": ObjectId(duty_slip_id_str)})
        return res.deleted_count > 0

import logging
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.collation import Collation
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse

logger = logging.getLogger(__name__)


class CompanyService:
    def __init__(self, db: Database):
        self.db = db
        self.collection: Collection = db["companies"]
        self.ensure_indexes()

    def ensure_indexes(self) -> None:
        """Create unique index on company name."""
        try:
            # Case-insensitive unique index on name
            self.collection.create_index(
                [("name", 1)],
                unique=True,
                collation=Collation(locale="en", strength=2),
                name="unique_company_name_case_insensitive"
            )
        except Exception as e:
            logger.warning("Could not create collation index, falling back to standard index: %s", str(e))
            try:
                self.collection.create_index([("name", 1)], unique=True, name="unique_company_name")
            except Exception as ex:
                logger.error("Failed to create company indexes: %s", str(ex))

    def _doc_to_response(self, doc: dict) -> CompanyResponse:
        billing_rates = doc.get("billing_rates")
        parsed_rates = None
        if billing_rates and isinstance(billing_rates, list):
            from app.schemas.company import RateConfig
            parsed_rates = [RateConfig(**r) if isinstance(r, dict) else r for r in billing_rates]

        return CompanyResponse(
            id=str(doc["_id"]),
            name=doc["name"],
            is_active=doc.get("is_active", True),
            billing_rates=parsed_rates,
            created_at=doc.get("created_at", datetime.now(timezone.utc)),
            updated_at=doc.get("updated_at", datetime.now(timezone.utc))
        )

    def create(self, data: CompanyCreate) -> CompanyResponse:
        now = datetime.now(timezone.utc)
        doc = {
            "name": data.name,
            "is_active": True,
            "billing_rates": [r.model_dump() for r in data.billing_rates] if data.billing_rates is not None else None,
            "created_at": now,
            "updated_at": now
        }
        try:
            result = self.collection.insert_one(doc)
            doc["_id"] = result.inserted_id
            return self._doc_to_response(doc)
        except DuplicateKeyError:
            raise ValueError(f"Company with name '{data.name}' already exists.")

    def list_all(self, include_inactive: bool = True) -> List[CompanyResponse]:
        query = {} if include_inactive else {"is_active": True}
        cursor = self.collection.find(query).sort("name", 1)
        return [self._doc_to_response(doc) for doc in cursor]

    def get_by_id(self, company_id: str) -> Optional[CompanyResponse]:
        if not ObjectId.is_valid(company_id):
            return None
        doc = self.collection.find_one({"_id": ObjectId(company_id)})
        if not doc:
            return None
        return self._doc_to_response(doc)

    def get_by_name(self, name: str) -> Optional[CompanyResponse]:
        doc = self.collection.find_one(
            {"name": name.strip()},
            collation=Collation(locale="en", strength=2)
        )
        if not doc:
            return None
        return self._doc_to_response(doc)

    def update(self, company_id: str, data: CompanyUpdate) -> Optional[CompanyResponse]:
        if not ObjectId.is_valid(company_id):
            return None

        update_fields = {}
        if data.name is not None:
            update_fields["name"] = data.name
        if data.is_active is not None:
            update_fields["is_active"] = data.is_active
        if data.billing_rates is not None:
            update_fields["billing_rates"] = [r.model_dump() for r in data.billing_rates]

        if not update_fields:
            return self.get_by_id(company_id)

        update_fields["updated_at"] = datetime.now(timezone.utc)

        try:
            result = self.collection.find_one_and_update(
                {"_id": ObjectId(company_id)},
                {"$set": update_fields},
                return_document=True
            )
            if not result:
                return None
            return self._doc_to_response(result)
        except DuplicateKeyError:
            raise ValueError(f"Company with name '{data.name}' already exists.")

    def deactivate(self, company_id: str) -> Optional[CompanyResponse]:
        """Soft deactivation of a company."""
        return self.update(company_id, CompanyUpdate(is_active=False))

    def delete(self, company_id: str, soft: bool = True) -> bool:
        if not ObjectId.is_valid(company_id):
            return False
        if soft:
            updated = self.deactivate(company_id)
            return updated is not None
        else:
            result = self.collection.delete_one({"_id": ObjectId(company_id)})
            return result.deleted_count > 0

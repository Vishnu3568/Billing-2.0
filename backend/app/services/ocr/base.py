from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel


class RawExtractionResult(BaseModel):
    raw_text: Optional[str] = None
    extracted_fields: Dict[str, Any]
    provider_name: str
    error: Optional[str] = None


class BaseOCRProvider(ABC):
    """
    Abstract interface for OCR / Vision AI providers.
    Processes Front scan (required) and Back scan (optional if available) of a duty slip as one document.
    """

    @abstractmethod
    def extract(
        self,
        front_bytes: bytes,
        front_content_type: str,
        back_bytes: Optional[bytes] = None,
        back_content_type: Optional[str] = None
    ) -> RawExtractionResult:
        """
        Execute OCR / Vision extraction on front and optional back scan bytes.
        """
        pass

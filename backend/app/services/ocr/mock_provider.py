import logging
from typing import Dict, Any, Optional
from app.services.ocr.base import BaseOCRProvider, RawExtractionResult

logger = logging.getLogger(__name__)


class MockOCRProvider(BaseOCRProvider):
    """
    Mock OCR / Vision Provider for testing and local development.
    Uses ground-truth field structure based on real duty slip documents.
    """

    def __init__(self, simulated_fields: Optional[Dict[str, Any]] = None):
        self.simulated_fields = simulated_fields

    def extract(
        self,
        front_bytes: bytes,
        front_content_type: str,
        back_bytes: Optional[bytes] = None,
        back_content_type: Optional[str] = None
    ) -> RawExtractionResult:
        logger.info("Running Mock OCR extraction on %d bytes (front) and %s (back)", len(front_bytes), f"{len(back_bytes)} bytes" if back_bytes else "None")

        # Ground-truth realistic fields from the real sample document
        fields = self.simulated_fields or {
            "duty_slip_no": {
                "value": None,
                "confidence": 0.0,
                "needs_review": True,
                "review_reason": "unreadable_field",
                "raw_text": None,
                "source_side": "front"
            },
            "date": {
                "value": "02-09-2026",
                "confidence": 0.95,
                "needs_review": False,
                "raw_text": "02-09-2026",
                "source_side": "front"
            },
            "driver_name": {
                "value": "K. Mohan Krishna",
                "confidence": 0.92,
                "needs_review": False,
                "raw_text": "K. Mohan Krishna",
                "source_side": "front"
            },
            "vehicle_number": {
                "value": "TS09GC6246 A/c Sedan",
                "confidence": 0.94,
                "needs_review": False,
                "raw_text": "TS09GC6246 A/c Sedan",
                "source_side": "front"
            },

            "meter_start": {
                "value": 432435,
                "confidence": 0.96,
                "needs_review": False,
                "raw_text": "432435",
                "source_side": "front"
            },
            "meter_return": {
                "value": 432582,
                "confidence": 0.96,
                "needs_review": False,
                "raw_text": "432582",
                "source_side": "front"
            },
            "total_km": {
                "value": 147,
                "confidence": 0.97,
                "needs_review": False,
                "raw_text": "147",
                "source_side": "front"
            },
            "starting_time": {
                "value": "08:00 AM",
                "confidence": 0.93,
                "needs_review": False,
                "raw_text": "08:00 AM",
                "source_side": "front"
            },
            "closing_time": {
                "value": "05:30 PM",
                "confidence": 0.93,
                "needs_review": False,
                "raw_text": "05:30 PM",
                "source_side": "front"
            },
            "extra_km": {
                "value": 67,
                "confidence": 0.90,
                "needs_review": False,
                "raw_text": "67",
                "source_side": "front"
            },
            "extra_hours": {
                "value": 1.5,
                "confidence": 0.90,
                "needs_review": False,
                "raw_text": "1.5",
                "source_side": "front"
            },
            "reporting_place": {
                "value": "Office",
                "confidence": 0.91,
                "needs_review": False,
                "raw_text": "Office",
                "source_side": "front"
            },
            "tour_location": {
                "value": "To Local",
                "confidence": 0.90,
                "needs_review": False,
                "raw_text": "To Local",
                "source_side": "front"
            },
            "party_name": {
                "value": "Mr Uday Kumar",
                "confidence": 0.94,
                "needs_review": False,
                "raw_text": "Party's Name: Mr Uday Kumar",
                "source_side": "front"
            },
            "customer_name": {
                "value": "Mr Uday Kumar",
                "confidence": 0.94,
                "needs_review": False,
                "raw_text": "Party's Name: Mr Uday Kumar",
                "source_side": "front"
            },
            "remarks": {
                "value": None,
                "confidence": 0.90,
                "needs_review": False,
                "raw_text": None,
                "source_side": "front"
            },
            "base_package": {
                "value": "8/80 = 2500",
                "confidence": 0.95,
                "needs_review": False,
                "raw_text": "8/80 = 2500",
                "source_side": "back" if back_bytes else "front"
            },
            "extra_km_charge": {
                "value": "67 x 15 = 1005",
                "confidence": 0.94,
                "needs_review": False,
                "raw_text": "67 x 15 = 1005",
                "source_side": "back" if back_bytes else "front"
            },
            "extra_hour_charge": {
                "value": "1.5 x 150 = 225",
                "confidence": 0.94,
                "needs_review": False,
                "raw_text": "1.5 x 150 = 225",
                "source_side": "back" if back_bytes else "front"
            },
            "bata": {
                "value": 250,
                "confidence": 0.95,
                "needs_review": False,
                "raw_text": "Bata = 250",
                "source_side": "back" if back_bytes else "front"
            },
            "toll": {
                "value": 40,
                "confidence": 0.95,
                "needs_review": False,
                "raw_text": "Toll = 40",
                "source_side": "back" if back_bytes else "front"
            },
            "total_amount": {
                "value": 4020,
                "confidence": 0.98,
                "needs_review": False,
                "raw_text": "Total = 4020",
                "source_side": "back" if back_bytes else "front"
            }
        }

        return RawExtractionResult(
            raw_text="[Mock Ground Truth OCR Extracted Text]",
            extracted_fields=fields,
            provider_name="mock"
        )

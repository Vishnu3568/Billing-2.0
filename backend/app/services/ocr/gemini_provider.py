import base64
import json
import logging
from typing import Dict, Any, Optional
import httpx
from app.services.ocr.base import BaseOCRProvider, RawExtractionResult
from app.core.config import settings

logger = logging.getLogger(__name__)

GEMINI_EXTRACTION_PROMPT = """
You are a precision OCR and document data extractor for transport/vehicle duty slips.
You are given one or two images representing the FRONT (and optional BACK) side of ONE duty slip.

Carefully examine the image(s) and extract the following fields.

CRITICAL ACCURACY RULES:
1. Extract ONLY what is visibly written on the physical document.
2. DO NOT GUESS or replace unreadable handwriting with plausible/common values.
3. For duty_slip_no: Extract ONLY the number physically printed or written in the "No." / "Duty Slip No." field on the document. If the physical "No." field is empty, blank, or not filled in, you MUST set "value": null, "confidence": 0.0, "needs_review": true, "review_reason": "unreadable_field", and "raw_text": null. Never guess or invent a duty slip number.
4. If any field is not present, blurry, or unreadable, set "value": null, "confidence": 0.0, and "needs_review": true with "review_reason": "unreadable_field" or "missing_field".
5. Determine the source side ("front", "back", or "both") for each extracted field.
6. Provide a confidence score between 0.0 and 1.0 for each extracted field.
7. Preserve exact raw document text for names, times, meters, locations, and handwritten calculations without silent modification or guessing.

Fields to extract:
- duty_slip_no (the number physically written/printed in the document's 'No.' field. If blank on paper, return value: null, needs_review: true)
- date (e.g. '02-09-2026' or raw date on document)
- driver_name (e.g. 'K.Mohana krishna' - preserve exact handwritten name)
- vehicle_number (e.g. 'TS09GC6246 A/c Sedan' - preserve exact handwritten text)
- meter_start (opening meter number e.g. 432435)
- meter_return (closing meter number e.g. 432582)
- total_km (the written total KM e.g. 147)
- starting_time (starting time e.g. '08:00 AM')
- closing_time (closing time e.g. '5:30 PM' or '05:30 PM')
- extra_km (written extra KM e.g. 67)
- extra_hours (written extra hours e.g. '1 1/2' or 1.5)
- reporting_place (e.g. 'office')
- tour_location (e.g. 'To Local')
- party_name (Party's Name written on document e.g. 'Uday Kumar' - do NOT guess or prepend prefixes)
- customer_name (same as party_name or customer name if written)
- remarks (any remarks / notes)

Back-side handwritten calculations (if back image is provided):
- base_package (e.g. '8/80 = 2500' or 2500)
- extra_km_charge (e.g. '67 x 15 = 1005' or 1005)
- extra_hour_charge (e.g. '1 1/2 x 150 = 225' or 225)
- bata (e.g. 250)
- toll (e.g. 40)
- total_amount (e.g. 4020)

Return your output as a STRICT, VALID JSON OBJECT matching this exact structure:
{
  "duty_slip_no": {"value": null, "confidence": 0.0, "needs_review": true, "review_reason": "unreadable_field", "source_side": "front", "raw_text": null},
  "date": {"value": "...", "confidence": 0.95, "needs_review": false, "review_reason": null, "source_side": "front", "raw_text": "..."},
  "driver_name": {"value": "...", "confidence": 0.95, "needs_review": false, "review_reason": null, "source_side": "front", "raw_text": "..."},
  "vehicle_number": {"value": "...", "confidence": 0.95, "needs_review": false, "review_reason": null, "source_side": "front", "raw_text": "..."},
  "meter_start": {"value": 432435, "confidence": 0.95, "needs_review": false, "review_reason": null, "source_side": "front", "raw_text": "..."},
  "meter_return": {"value": 432582, "confidence": 0.95, "needs_review": false, "review_reason": null, "source_side": "front", "raw_text": "..."},
  "total_km": {"value": 147, "confidence": 0.95, "needs_review": false, "review_reason": null, "source_side": "front", "raw_text": "..."},
  "starting_time": {"value": "08:00 AM", "confidence": 0.95, "needs_review": false, "review_reason": null, "source_side": "front", "raw_text": "..."},
  "closing_time": {"value": "05:30 PM", "confidence": 0.95, "needs_review": false, "review_reason": null, "source_side": "front", "raw_text": "..."},
  "extra_km": {"value": 67, "confidence": 0.95, "needs_review": false, "review_reason": null, "source_side": "front", "raw_text": "..."},
  "extra_hours": {"value": 1.5, "confidence": 0.95, "needs_review": false, "review_reason": null, "source_side": "front", "raw_text": "..."},
  "reporting_place": {"value": "Office", "confidence": 0.95, "needs_review": false, "review_reason": null, "source_side": "front", "raw_text": "..."},
  "tour_location": {"value": "To Local", "confidence": 0.95, "needs_review": false, "review_reason": null, "source_side": "front", "raw_text": "..."},
  "party_name": {"value": "Mr Uday Kumar", "confidence": 0.95, "needs_review": false, "review_reason": null, "source_side": "front", "raw_text": "..."},
  "customer_name": {"value": "Mr Uday Kumar", "confidence": 0.95, "needs_review": false, "review_reason": null, "source_side": "front", "raw_text": "..."},
  "remarks": {"value": "...", "confidence": 0.95, "needs_review": false, "review_reason": null, "source_side": "front", "raw_text": "..."},
  "base_package": {"value": "8/80 = 2500", "confidence": 0.95, "needs_review": false, "review_reason": null, "source_side": "back", "raw_text": "..."},
  "extra_km_charge": {"value": "67 x 15 = 1005", "confidence": 0.95, "needs_review": false, "review_reason": null, "source_side": "back", "raw_text": "..."},
  "extra_hour_charge": {"value": "1.5 x 150 = 225", "confidence": 0.95, "needs_review": false, "review_reason": null, "source_side": "back", "raw_text": "..."},
  "bata": {"value": 250, "confidence": 0.95, "needs_review": false, "review_reason": null, "source_side": "back", "raw_text": "..."},
  "toll": {"value": 40, "confidence": 0.95, "needs_review": false, "review_reason": null, "source_side": "back", "raw_text": "..."},
  "total_amount": {"value": 4020, "confidence": 0.95, "needs_review": false, "review_reason": null, "source_side": "back", "raw_text": "..."}
}
"""


class GeminiVisionOCRProvider(BaseOCRProvider):
    """
    Live Vision AI extraction using Gemini multimodal API.
    Sends front and optional back scans simultaneously to extract unified document fields.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL or "gemini-2.5-flash"

    def extract(
        self,
        front_bytes: bytes,
        front_content_type: str,
        back_bytes: Optional[bytes] = None,
        back_content_type: Optional[str] = None
    ) -> RawExtractionResult:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in environment.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        front_b64 = base64.b64encode(front_bytes).decode("utf-8")

        parts = [
            {"text": GEMINI_EXTRACTION_PROMPT},
            {
                "inline_data": {
                    "mime_type": front_content_type,
                    "data": front_b64
                }
            }
        ]

        if back_bytes and back_content_type:
            back_b64 = base64.b64encode(back_bytes).decode("utf-8")
            parts.append({
                "inline_data": {
                    "mime_type": back_content_type,
                    "data": back_b64
                }
            })

        payload = {
            "contents": [
                {
                    "parts": parts
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
                "response_mime_type": "application/json"
            }
        }

        with httpx.Client(timeout=45.0) as client:
            response = client.post(url, json=payload)
            if response.status_code != 200:
                logger.error("Gemini API error (%d): %s", response.status_code, response.text)
                raise ValueError(f"Gemini API error ({response.status_code}): {response.text}")

            res_json = response.json()
            candidates = res_json.get("candidates", [])
            if not candidates:
                raise ValueError("No extraction content returned by Gemini Vision API.")

            text_content = candidates[0]["content"]["parts"][0]["text"]
            parsed_fields = json.loads(text_content)

            return RawExtractionResult(
                raw_text=text_content,
                extracted_fields=parsed_fields,
                provider_name=f"gemini-{self.model}"
            )


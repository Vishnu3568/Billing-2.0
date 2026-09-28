from app.core.config import settings
from app.services.ocr.base import BaseOCRProvider
from app.services.ocr.mock_provider import MockOCRProvider
from app.services.ocr.gemini_provider import GeminiVisionOCRProvider


def get_ocr_provider() -> BaseOCRProvider:
    """
    Factory to resolve the configured OCR provider.
    Defaults to MockOCRProvider if provider is 'mock' or if API key is not present.
    """
    if settings.OCR_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
        return GeminiVisionOCRProvider(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_MODEL
        )
    return MockOCRProvider()

import os
from typing import Optional
from pathlib import Path
from app.services.storage.base import BaseStorageService
from app.core.config import settings


class LocalStorageService(BaseStorageService):
    """
    Local filesystem storage implementation for managing duty slips,
    Word documents, and templates.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or settings.LOCAL_STORAGE_BASE_DIR).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, destination_path: str) -> Path:
        clean_path = destination_path.lstrip("/\\")
        full_path = (self.base_dir / clean_path).resolve()
        if not str(full_path).startswith(str(self.base_dir)):
            raise ValueError("Path traversal attempt detected.")
        return full_path

    def save_file(self, file_content: bytes, destination_path: str) -> str:
        target_path = self._get_full_path(destination_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(file_content)
        return str(target_path)

    def get_file(self, file_path: str) -> Optional[bytes]:
        target_path = self._get_full_path(file_path)
        if not target_path.exists() or not target_path.is_file():
            return None
        with open(target_path, "rb") as f:
            return f.read()

    def delete_file(self, file_path: str) -> bool:
        target_path = self._get_full_path(file_path)
        if target_path.exists() and target_path.is_file():
            target_path.unlink()
            return True
        return False

    def exists(self, file_path: str) -> bool:
        target_path = self._get_full_path(file_path)
        return target_path.exists() and target_path.is_file()


def get_storage_service() -> BaseStorageService:
    """Storage provider factory."""
    if settings.STORAGE_TYPE == "local":
        return LocalStorageService()
    raise NotImplementedError(f"Storage type '{settings.STORAGE_TYPE}' is not supported yet.")

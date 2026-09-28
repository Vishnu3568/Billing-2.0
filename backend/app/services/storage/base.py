from abc import ABC, abstractmethod
from typing import BinaryIO, Optional


class BaseStorageService(ABC):
    """
    Abstract file storage interface for duty-slip scans, Word documents,
    and company templates.
    """

    @abstractmethod
    def save_file(self, file_content: bytes, destination_path: str) -> str:
        """Save raw bytes to a target destination path and return the stored file path/key."""
        pass

    @abstractmethod
    def get_file(self, file_path: str) -> Optional[bytes]:
        """Retrieve file content as bytes."""
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        """Delete file at the specified path."""
        pass

    @abstractmethod
    def exists(self, file_path: str) -> bool:
        """Check if file exists at the specified path."""
        pass

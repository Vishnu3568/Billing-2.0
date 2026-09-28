import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from app.core.config import settings

logger = logging.getLogger(__name__)


class MongoDBManager:
    client: Optional[MongoClient] = None
    db: Optional[Database] = None

    def connect(self) -> None:
        """Initialize MongoDB client connection."""
        try:
            self.client = MongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=2000
            )
            self.db = self.client[settings.MONGODB_DB_NAME]
            logger.info("MongoDB client initialized for database: %s", settings.MONGODB_DB_NAME)
        except Exception as e:
            logger.error("Failed to initialize MongoDB client: %s", str(e))

    def close(self) -> None:
        """Close MongoDB client connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")

    def check_connection(self) -> bool:
        """Verify if MongoDB is reachable."""
        if not self.client:
            return False
        try:
            self.client.admin.command("ping")
            return True
        except Exception:
            return False

    def get_database(self) -> Database:
        """Get database instance."""
        if self.db is None:
            self.connect()
        return self.db


db_manager = MongoDBManager()


def get_db() -> Database:
    """Dependency provider for database instance."""
    return db_manager.get_database()

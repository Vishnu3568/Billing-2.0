from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    database_connected: bool
    version: str
    storage_type: str

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Any
from datetime import datetime


class RateConfig(BaseModel):
    vehicle_category: str = Field("sedan", description="Vehicle category: e.g. sedan, crysta, innova")
    service_type: str = Field("local", description="Service type: local or outstation")
    base_package_rate: Optional[float] = Field(None, description="Base package amount (e.g. 2500 for local 8/80 sedan)")
    base_rate: Optional[float] = Field(None, description="Base package amount (alias)")
    base_km: Optional[float] = Field(None, description="Base package kilometers (e.g. 80.0)")
    base_hours: Optional[float] = Field(None, description="Base package hours (e.g. 8.0)")
    extra_km_rate: Optional[float] = Field(None, description="Charge per extra kilometer (e.g. 15.0)")
    extra_hour_rate: Optional[float] = Field(None, description="Charge per extra hour (e.g. 150.0)")
    driver_bata_rate: Optional[float] = Field(None, description="Driver allowance / bata rate (e.g. 250.0)")
    min_km_per_day: Optional[float] = Field(None, description="Minimum KM per day for outstation trips")

    @model_validator(mode="before")
    @classmethod
    def sync_base_rates(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "base_rate" in data and "base_package_rate" not in data:
                data["base_package_rate"] = data["base_rate"]
            elif "base_package_rate" in data and "base_rate" not in data:
                data["base_rate"] = data["base_package_rate"]
        return data


class CompanyBase(BaseModel):
    name: str = Field(..., description="Unique company name", min_length=1, max_length=200)
    billing_rates: Optional[List[RateConfig]] = Field(default=None, description="Optional company-specific rate configurations")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Company name cannot be empty or only whitespace")
        return cleaned


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    is_active: Optional[bool] = None
    billing_rates: Optional[List[RateConfig]] = None

    @field_validator("name")
    @classmethod
    def validate_optional_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Company name cannot be empty or only whitespace")
            return cleaned
        return v


class CompanyResponse(BaseModel):
    id: str
    name: str
    is_active: bool
    billing_rates: Optional[List[RateConfig]] = None
    created_at: datetime
    updated_at: datetime

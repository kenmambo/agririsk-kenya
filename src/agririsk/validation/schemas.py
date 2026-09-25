"""Pydantic validation schemas for domain entities and API contracts."""

import datetime as dt
from typing import Literal, List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from agririsk.core.constants import COUNTY_CODE_MAP


class CountyBase(BaseModel):
    """Base schema for county attributes.

    Attributes:
        code: 3-digit official code (e.g. '001' to '047').
        name: Official name of the county.
        asal_category: ASAL ecological classification.
        centroid_lat: Centroid latitude within Kenya borders.
        centroid_lon: Centroid longitude within Kenya borders.
    """

    code: str = Field(..., description="County 3-digit code e.g. '001'")
    name: str = Field(..., description="Official county name")
    asal_category: Literal["Arid", "Semi-Arid", "Non-ASAL"] = Field(
        ..., description="ASAL ecological classification"
    )
    centroid_lat: float = Field(
        ..., ge=-5.0, le=5.5, description="Centroid latitude within Kenya bounds (-5.0 to 5.5)"
    )
    centroid_lon: float = Field(
        ..., ge=33.5, le=42.5, description="Centroid longitude within Kenya bounds (33.5 to 42.5)"
    )

    @field_validator("code")
    @classmethod
    def validate_county_code(cls, v: str) -> str:
        """Validate that the county code corresponds to one of Kenya's 47 counties."""
        code_str = v.zfill(3)
        if code_str not in COUNTY_CODE_MAP:
            raise ValueError(f"Invalid Kenya county code '{v}'. Must be one of 001-047.")
        return code_str


class CountyCreate(CountyBase):
    """Schema for creating a new county record."""
    pass


class CountyRead(CountyBase):
    """Schema for returning county information from the database or API."""

    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    """API health response payload.

    Attributes:
        status: Overall service health status ('healthy' or 'degraded').
        app_name: Name of the application.
        version: Application semantic version.
        app_version: Application semantic version.
        model_version: Serialized model artifact version.
        dataset_version: Underlying panel dataset version.
        environment: Active operational environment (e.g. 'development', 'test', 'production').
        database_status: Connectivity status to the SQLite/PostgreSQL database.
        timestamp: Time of health check in UTC.
    """

    status: str = Field(..., description="Service health status ('healthy' or 'degraded')")
    app_name: str = Field(..., description="Registered application name")
    version: str = Field(..., description="Application semantic version")
    app_version: str = Field(default="0.1.0", description="Application semantic version")
    model_version: str = Field(default="v1.0.0-rf-calibrated", description="Active model artifact version")
    dataset_version: str = Field(default="2024.12-asal-v1", description="Underlying dataset version")
    environment: str = Field(..., description="Active operational environment")
    database_status: str = Field(..., description="Status of database connection")
    timestamp: dt.datetime = Field(..., description="UTC timestamp of the health check")


class VersionResponse(BaseModel):
    """Application version and build metadata."""
    app_name: str
    app_version: str
    model_version: str
    dataset_version: str
    release_date: str
    environment: str
    repository: str


class RiskScoreItem(BaseModel):
    """Individual county risk assessment score."""
    county: str
    date: str
    horizon_months: int
    calibrated_probability: float
    confidence_interval: List[float]
    risk_band: str
    action_trigger: str
    disclaimer: str = "Research prototype — not an official humanitarian early-warning alert."


class RiskLatestResponse(BaseModel):
    """Latest risk summary across monitored counties."""
    counties_monitored: int
    latest_period: str
    model_version: str
    dataset_version: str
    scores: List[RiskScoreItem]


class ForecastItem(BaseModel):
    """Multi-horizon forecast for a county."""
    horizon: str
    horizon_months: int
    target_date: str
    calibrated_probability: float
    confidence_interval: List[float]
    risk_band: str
    action_trigger: str


class CountyForecastResponse(BaseModel):
    """Multi-horizon forecast response for a single county."""
    county: str
    observation_date: str
    model_version: str
    forecasts: List[ForecastItem]
    disclaimer: str = "Research prototype — not an official IPC classification."


class DataStatusResponse(BaseModel):
    """Data source freshness and operational status."""
    overall_status: str
    climate_latest: str
    vegetation_latest: str
    market_latest: str
    food_security_latest: str
    snapshot_date: str
    operational_mode: str

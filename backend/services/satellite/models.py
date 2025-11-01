"""
Data Models for Satellite Service

Pydantic models for satellite signals and hotspots with strict validation.
"""

from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Dict, Optional, List, Union


class SatelliteSignal(BaseModel):
    """Individual satellite fire detection signal"""

    id: str = Field(..., description="Unique signal ID: source:satellite:time:lat,lon")
    hazard: str = Field(pattern="^fire$", description="Hazard type (MVP: fire only)")
    time: str = Field(..., description="ISO8601 UTC timestamp")
    lat: float = Field(..., description="Latitude in decimal degrees")
    lon: float = Field(..., description="Longitude in decimal degrees")
    severity: Dict[str, float] = Field(..., description="Severity metrics (e.g., FRP)")
    source_name: str = Field(..., description="Data source name (e.g., FIRMS)")
    source_url: Optional[HttpUrl] = Field(None, description="Exact dataset URL")
    raw_confidence: Optional[float] = Field(None, description="Original confidence value")

    @field_validator("lat")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        """Ensure latitude is within valid range"""
        if not -90 <= v <= 90:
            raise ValueError(f"Latitude {v} out of range [-90, 90]")
        return v

    @field_validator("lon")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        """Ensure longitude is within valid range"""
        if not -180 <= v <= 180:
            raise ValueError(f"Longitude {v} out of range [-180, 180]")
        return v

    @field_validator("time")
    @classmethod
    def validate_utc_time(cls, v: str) -> str:
        """Ensure time string is UTC (ends with Z or +00:00)"""
        if not (v.endswith("Z") or v.endswith("+00:00")):
            raise ValueError(f"Time {v} must be UTC (end with Z or +00:00)")
        return v


class Hotspot(BaseModel):
    """Clustered fire hotspot with multiple detections"""

    id: str = Field(..., description="Unique hotspot ID: hotspot:hazard:timestamp:lat,lon")
    hazard: str = Field(..., description="Hazard type (e.g., fire)")
    lat: float = Field(..., description="Centroid latitude")
    lon: float = Field(..., description="Centroid longitude")
    latest_time: str = Field(..., description="ISO8601 UTC timestamp of newest signal")
    intensity: Dict[str, float] = Field(
        ...,
        description="Intensity metrics: frp_sum, frp_max, count"
    )
    provenance: List[Dict[str, Union[str, int, float]]] = Field(
        ...,
        description="Source provenance: [{src: name, count: N}]"
    )

    @field_validator("lat")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        """Ensure latitude is within valid range"""
        if not -90 <= v <= 90:
            raise ValueError(f"Latitude {v} out of range [-90, 90]")
        return v

    @field_validator("lon")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        """Ensure longitude is within valid range"""
        if not -180 <= v <= 180:
            raise ValueError(f"Longitude {v} out of range [-180, 180]")
        return v

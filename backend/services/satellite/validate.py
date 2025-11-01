"""
Validation Helpers for Satellite Service

Utility functions for validating coordinates, times, and data ranges.
"""

from typing import Iterable
from statistics import mean


def bounded(v: float, lo: float, hi: float) -> bool:
    """Check if value is within bounds (inclusive)"""
    return lo <= v <= hi


def non_empty(it: Iterable) -> bool:
    """Check if iterable has at least one element"""
    for _ in it:
        return True
    return False


def approx_latlon(lat: float, lon: float) -> bool:
    """Validate latitude and longitude ranges"""
    return bounded(lat, -90, 90) and bounded(lon, -180, 180)


def timestring_is_utc(t: str) -> bool:
    """Check if time string is UTC format (ends with Z or +00:00)"""
    return t.endswith("Z") or t.endswith("+00:00")


def robust_avg(xs: list[float]) -> float:
    """Calculate average, returning 0.0 for empty lists"""
    return float(mean(xs)) if xs else 0.0

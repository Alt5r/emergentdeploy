"""
Satellite Service - Multi-Hazard Detection Module

Ingests multiple satellite data sources:
- NASA FIRMS: Fire detections (VIIRS/MODIS)
- USGS: Earthquake events (GeoJSON)

Clusters detections into hazard-specific hotspots with strong validation
and provenance tracking.
"""

from .models import SatelliteSignal, Hotspot
from .clustering import cluster_hazard
from .firms import fetch_firms_signals
from .usgs import fetch_usgs_earthquakes

__all__ = [
    'SatelliteSignal',
    'Hotspot',
    'cluster_hazard',
    'fetch_firms_signals',
    'fetch_usgs_earthquakes'
]

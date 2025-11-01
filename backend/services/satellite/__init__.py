"""
Satellite Service - Live Fire Detection Module

Ingests NASA FIRMS satellite data, clusters fire detections into hotspots,
and provides real-time fire event data with strong validation and provenance tracking.
"""

from .models import SatelliteSignal, Hotspot
from .cluster import cluster_fire

__all__ = ['SatelliteSignal', 'Hotspot', 'cluster_fire']

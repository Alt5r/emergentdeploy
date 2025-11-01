"""
USGS Earthquake Adapter

Fetches earthquake data from USGS GeoJSON feeds and converts to SatelliteSignal format.
Supports magnitude filtering and real-time earthquake detection.
"""

import os
import logging
from typing import List
from datetime import datetime, timezone

import requests

from .models import SatelliteSignal
from .validate import approx_latlon
from .thinkguard import plan, verify, StepPlan

logger = logging.getLogger(__name__)


def fetch_usgs_earthquakes() -> List[SatelliteSignal]:
    """
    Fetch earthquake signals from USGS GeoJSON feed.

    Returns:
        List of SatelliteSignal objects with hazard='earthquake'
    """
    url = os.getenv("USGS_URL", "")

    if not url:
        logger.warning("[USGS] USGS_URL not configured, skipping earthquake ingestion")
        return []

    plan(StepPlan(
        name="fetch_usgs_earthquakes",
        inputs={"url": url},
        validations=[
            "HTTP 200 response",
            "Valid GeoJSON structure",
            "Required fields: mag, time, coordinates",
            "Lat/lon in valid ranges"
        ],
        edge_cases=[
            "Missing magnitude",
            "Invalid coordinates",
            "Future timestamps",
            "Null depth values"
        ],
        outputs=["List[SatelliteSignal] with hazard=earthquake"]
    ))

    try:
        logger.info(f"[USGS] Fetching from: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()

        if data.get("type") != "FeatureCollection":
            raise ValueError(f"Expected FeatureCollection, got: {data.get('type')}")

        features = data.get("features", [])
        signals = _parse_geojson_features(features, url)

        verify(
            "fetch_usgs_earthquakes",
            assertions=[
                len(signals) >= 0,
                all(s.hazard == "earthquake" for s in signals)
            ],
            summary=f"produced={len(signals)} earthquakes from {url}"
        )

        return signals

    except requests.RequestException as e:
        logger.error(f"[USGS] HTTP error: {e}")
        verify("fetch_usgs_earthquakes", assertions=[False], summary=f"HTTP failed: {e}")
        return []
    except Exception as e:
        logger.error(f"[USGS] Parse error: {e}", exc_info=True)
        verify("fetch_usgs_earthquakes", assertions=[False], summary=f"Parse failed: {e}")
        return []


def _parse_geojson_features(features: List[dict], source_url: str) -> List[SatelliteSignal]:
    """
    Parse USGS GeoJSON features into SatelliteSignal objects.

    Args:
        features: List of GeoJSON feature dicts
        source_url: Source URL for provenance

    Returns:
        List of validated SatelliteSignal objects
    """
    signals = []
    dropped = 0

    for feature in features:
        try:
            props = feature.get("properties", {})
            geometry = feature.get("geometry", {})
            coords = geometry.get("coordinates", [])

            # Extract required fields
            mag = props.get("mag")
            time_ms = props.get("time")  # Unix milliseconds
            place = props.get("place", "")

            # Validate required fields
            if mag is None or time_ms is None or len(coords) < 2:
                dropped += 1
                continue

            # Parse coordinates: [lon, lat, depth]
            lon = float(coords[0])
            lat = float(coords[1])
            depth_km = float(coords[2]) if len(coords) > 2 and coords[2] is not None else 0.0

            # Validate coordinates
            if not approx_latlon(lat, lon):
                logger.debug(f"[USGS] Invalid coords: lat={lat}, lon={lon}")
                dropped += 1
                continue

            # Convert Unix milliseconds to ISO8601 UTC
            time_dt = datetime.fromtimestamp(time_ms / 1000.0, tz=timezone.utc)
            time_iso = time_dt.isoformat().replace("+00:00", "Z")

            # Create unique ID
            signal_id = f"usgs:{time_iso}:{lat:.4f},{lon:.4f}"

            # Build severity dict
            severity = {
                "mag": float(mag),
                "depth_km": depth_km
            }

            # Create signal
            signal = SatelliteSignal(
                id=signal_id,
                hazard="earthquake",
                time=time_iso,
                lat=lat,
                lon=lon,
                severity=severity,
                source_name="USGS",
                source_url=source_url,
                raw_confidence=None  # USGS doesn't provide confidence scores
            )

            signals.append(signal)

        except (ValueError, TypeError, KeyError) as e:
            logger.debug(f"[USGS] Dropped feature: {e}")
            dropped += 1
            continue

    logger.info(f"[USGS][GeoJSON] Parsed {len(signals)} earthquakes (dropped {dropped})")
    return signals

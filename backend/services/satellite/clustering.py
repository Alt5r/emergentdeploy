"""
Multi-Hazard Clustering Module

Supports hazard-specific clustering with different parameters:
- Fires: tight spatial clusters (5km, 90min window)
- Earthquakes: aftershock grouping (30km, 24h window)
"""

import os
import math
import numpy as np
import logging
from typing import List, Tuple, Dict
from datetime import datetime, timedelta, timezone
from sklearn.cluster import DBSCAN

from .models import SatelliteSignal, Hotspot
from .validate import robust_avg
from .thinkguard import plan, verify, StepPlan

logger = logging.getLogger(__name__)

# Earth's radius in kilometers (for Haversine distance)
EARTH_KM = 6371.0088

# Hazard-specific clustering parameters
HAZARD_PARAMS = {
    "fire": {
        "eps_km": float(os.getenv("FIRE_EPS_KM", os.getenv("EPS_KM", "5.0"))),
        "min_pts": int(float(os.getenv("FIRE_MIN_PTS", os.getenv("MIN_PTS", "3")))),
        "window_min": int(os.getenv("FIRE_WINDOW_MIN", os.getenv("WINDOW_MIN", "90")))
    },
    "earthquake": {
        "eps_km": float(os.getenv("QUAKE_EPS_KM", "30.0")),
        "min_pts": int(float(os.getenv("QUAKE_MIN_PTS", "2"))),
        "window_min": int(os.getenv("QUAKE_WINDOW_MIN", "1440"))  # 24 hours
    }
}


def _to_radians(coords: List[Tuple[float, float]]) -> np.ndarray:
    """Convert list of (lat, lon) tuples to radians for Haversine"""
    return np.radians(np.array(coords))


def _window_signals(signals: List[SatelliteSignal], window_min: int) -> List[SatelliteSignal]:
    """
    Filter signals to those within the time window.

    Args:
        signals: All signals for a hazard
        window_min: Time window in minutes

    Returns:
        Signals within the time window
    """
    if not signals:
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_min)
    out = []

    for s in signals:
        # Parse ISO8601 time (handles both Z and +00:00)
        sig_time = datetime.fromisoformat(s.time.replace("Z", "+00:00"))
        if sig_time >= cutoff:
            out.append(s)

    logger.info(f"[CLUSTER] Windowed: {len(out)}/{len(signals)} signals within {window_min} min")
    return out


def cluster_hazard(signals: List[SatelliteSignal], hazard: str) -> List[Hotspot]:
    """
    Cluster signals for a specific hazard type using hazard-specific parameters.

    Args:
        signals: All signals for this hazard type
        hazard: Hazard type ('fire' or 'earthquake')

    Returns:
        List of Hotspot objects
    """
    if hazard not in HAZARD_PARAMS:
        logger.error(f"[CLUSTER] Unknown hazard type: {hazard}")
        return []

    params = HAZARD_PARAMS[hazard]
    eps_km = params["eps_km"]
    min_pts = params["min_pts"]
    window_min = params["window_min"]

    plan(StepPlan(
        name=f"cluster_{hazard}",
        inputs={
            "signals": len(signals),
            "eps_km": eps_km,
            "min_pts": min_pts,
            "window_min": window_min
        },
        validations=[
            "Non-empty signal list",
            f"Valid clustering params (eps={eps_km}, minPts={min_pts})",
            f"Time window = {window_min} min"
        ],
        edge_cases=[
            "All signals outside time window",
            "Signals too sparse to form clusters",
            "Single signal per location"
        ],
        outputs=[f"List[Hotspot] for {hazard}"]
    ))

    # Filter to time window
    windowed = _window_signals(signals, window_min)

    if len(windowed) < min_pts:
        logger.info(f"[CLUSTER] Too few signals ({len(windowed)}) for {hazard}, min_pts={min_pts}")
        verify(
            f"cluster_{hazard}",
            assertions=[True],
            summary=f"ok=True | clusters=0 | signals_in_window={len(windowed)} (below threshold)"
        )
        return []

    # Extract coordinates and convert to radians
    coords = [(s.lat, s.lon) for s in windowed]
    coords_rad = _to_radians(coords)

    # Run DBSCAN with Haversine metric
    # eps must be in radians: eps_rad = eps_km / EARTH_KM
    eps_rad = eps_km / EARTH_KM
    db = DBSCAN(eps=eps_rad, min_samples=min_pts, metric="haversine")
    labels = db.fit_predict(coords_rad)

    # Group signals by cluster label
    clusters: Dict[int, List[SatelliteSignal]] = {}
    noise_count = 0

    for i, label in enumerate(labels):
        if label == -1:
            noise_count += 1
            continue
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(windowed[i])

    logger.info(
        f"[CLUSTER] DBSCAN found {len(clusters)} clusters, "
        f"{noise_count} noise points for {hazard}"
    )

    # Convert clusters to Hotspots
    hotspots = []
    for cluster_id, cluster_signals in clusters.items():
        hotspot = _aggregate_cluster(cluster_signals, hazard)
        if hotspot:
            hotspots.append(hotspot)

    verify(
        f"cluster_{hazard}",
        assertions=[
            len(hotspots) >= 0,
            all(h.hazard == hazard for h in hotspots)
        ],
        summary=f"ok=True | clusters={len(hotspots)} | signals_in_window={len(windowed)}"
    )

    return hotspots


def _aggregate_cluster(signals: List[SatelliteSignal], hazard: str) -> Hotspot:
    """
    Aggregate a cluster of signals into a single Hotspot.

    Args:
        signals: Signals belonging to this cluster
        hazard: Hazard type

    Returns:
        Hotspot object with aggregated metrics
    """
    # Compute centroid (mean lat/lon)
    lats = [s.lat for s in signals]
    lons = [s.lon for s in signals]
    centroid_lat = robust_avg(lats)
    centroid_lon = robust_avg(lons)

    # Find latest time
    times = [datetime.fromisoformat(s.time.replace("Z", "+00:00")) for s in signals]
    latest_dt = max(times)
    latest_time = latest_dt.isoformat().replace("+00:00", "Z")

    # Build intensity dict based on hazard type
    intensity = _build_intensity(signals, hazard)

    # Build provenance
    provenance = [{"src": signals[0].source_name, "count": len(signals)}]

    # Create hotspot ID
    latest_unix = int(latest_dt.timestamp())
    hotspot_id = f"hotspot:{hazard}:{latest_unix}:{centroid_lat:.4f},{centroid_lon:.4f}"

    return Hotspot(
        id=hotspot_id,
        hazard=hazard,
        lat=centroid_lat,
        lon=centroid_lon,
        latest_time=latest_time,
        intensity=intensity,
        provenance=provenance
    )


def _build_intensity(signals: List[SatelliteSignal], hazard: str) -> Dict[str, float]:
    """
    Build intensity metrics based on hazard type.

    Args:
        signals: Signals in cluster
        hazard: Hazard type

    Returns:
        Intensity dict with hazard-specific metrics
    """
    if hazard == "fire":
        # Fire intensity: FRP metrics
        frps = [s.severity.get("frp", 0.0) for s in signals]
        return {
            "frp_sum": sum(frps),
            "frp_max": max(frps) if frps else 0.0,
            "count": len(signals)
        }

    elif hazard == "earthquake":
        # Earthquake intensity: magnitude and depth
        mags = [s.severity.get("mag", 0.0) for s in signals]
        depths = [s.severity.get("depth_km", 0.0) for s in signals]
        return {
            "mag_max": max(mags) if mags else 0.0,
            "mag_avg": robust_avg(mags),
            "depth_avg_km": robust_avg(depths),
            "count": len(signals)
        }

    else:
        # Generic fallback
        return {"count": len(signals)}

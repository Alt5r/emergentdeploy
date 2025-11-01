"""
Clustering Module - Haversine-DBSCAN for Fire Hotspots

Groups spatially and temporally close fire detections into hotspots.
Uses DBSCAN with Haversine distance metric for geographic clustering.
"""

import os
import math
import numpy as np
import logging
from typing import List, Tuple
from datetime import datetime, timedelta, timezone
from sklearn.cluster import DBSCAN

from .models import SatelliteSignal, Hotspot
from .validate import robust_avg
from .thinkguard import plan, verify, StepPlan

logger = logging.getLogger(__name__)

# Earth's radius in kilometers (for Haversine distance)
EARTH_KM = 6371.0088

# Clustering parameters (from environment or defaults)
EPS_KM = float(os.getenv("EPS_KM", "5.0"))  # Max distance between points (km)
MIN_PTS = int(float(os.getenv("MIN_PTS", "3")))  # Min points to form a cluster
WINDOW_MIN = int(os.getenv("WINDOW_MIN", "90"))  # Time window (minutes)


def _to_radians(coords: List[Tuple[float, float]]) -> np.ndarray:
    """Convert list of (lat, lon) tuples to radians for Haversine"""
    return np.radians(np.array(coords))


def _window_signals(signals: List[SatelliteSignal]) -> List[SatelliteSignal]:
    """
    Filter signals to those within the time window.

    Only keeps signals from the last WINDOW_MIN minutes.
    """
    if not signals:
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MIN)
    out = []

    for s in signals:
        # Parse ISO8601 time (handles both Z and +00:00)
        sig_time = datetime.fromisoformat(s.time.replace("Z", "+00:00"))
        if sig_time >= cutoff:
            out.append(s)

    logger.info(f"[CLUSTER] Windowed: {len(out)}/{len(signals)} signals within {WINDOW_MIN} min")
    return out


def cluster_fire(signals: List[SatelliteSignal]) -> List[Hotspot]:
    """
    Cluster fire signals into hotspots using Haversine-DBSCAN.

    Algorithm:
    1. Filter signals to time window (last WINDOW_MIN minutes)
    2. Convert coordinates to radians for Haversine metric
    3. Run DBSCAN with eps=EPS_KM/EARTH_KM, min_samples=MIN_PTS
    4. Aggregate each cluster into a Hotspot

    Args:
        signals: List of SatelliteSignal objects

    Returns:
        List of Hotspot objects (clusters with ≥ MIN_PTS members)
    """
    p = StepPlan(
        name="cluster_fire",
        inputs={
            "signals": len(signals),
            "EPS_KM": EPS_KM,
            "MIN_PTS": MIN_PTS,
            "WINDOW_MIN": WINDOW_MIN
        },
        validations=[
            "signals within time window",
            "coords present",
            "DBSCAN labels != -1 for clusters"
        ],
        edge_cases=["no signals", "all noise", "gigantic single cluster"],
        outputs=["List[Hotspot]"]
    )
    plan(p)

    # Step 1: Filter to time window
    windowed = _window_signals(signals)

    if not windowed:
        verify("cluster_fire", assertions=[True], summary="no signals in window")
        logger.info("[CLUSTER] No signals in time window, returning empty list")
        return []

    # Step 2: Extract coordinates and convert to radians
    coords = [(s.lat, s.lon) for s in windowed]
    rad = _to_radians(coords)

    # Step 3: Run DBSCAN with Haversine metric
    # eps is in radians (EPS_KM / EARTH_KM)
    db = DBSCAN(eps=EPS_KM / EARTH_KM, min_samples=MIN_PTS, metric="haversine")
    db.fit(rad)
    labels = db.labels_

    # Count clusters (excluding noise label -1)
    unique_labels = set(labels)
    cluster_count = len([l for l in unique_labels if l != -1])
    noise_count = sum(1 for l in labels if l == -1)

    logger.info(
        f"[CLUSTER] DBSCAN found {cluster_count} clusters, "
        f"{noise_count} noise points"
    )

    # Step 4: Aggregate clusters into Hotspots
    out: List[Hotspot] = []

    for lbl in sorted(unique_labels):
        if lbl == -1:
            continue  # Skip noise

        # Get all signals in this cluster
        members = [windowed[i] for i in range(len(windowed)) if labels[i] == lbl]

        if not members:
            continue

        # Calculate centroid (mean lat/lon)
        lats = [m.lat for m in members]
        lons = [m.lon for m in members]
        centroid_lat = float(np.mean(lats))
        centroid_lon = float(np.mean(lons))

        # Find latest detection time
        latest = max(m.time for m in members)

        # Calculate intensity metrics
        frps = [m.severity.get("frp", 0.0) for m in members]
        frp_sum = float(np.sum(frps))
        frp_max = float(np.max(frps)) if frps else 0.0

        # Generate hotspot ID
        timestamp = int(datetime.now(timezone.utc).timestamp())
        hotspot_id = f"hotspot:fire:{timestamp}:{centroid_lat:.4f},{centroid_lon:.4f}"

        # Create Hotspot object
        hotspot = Hotspot(
            id=hotspot_id,
            hazard="fire",
            lat=centroid_lat,
            lon=centroid_lon,
            latest_time=latest,
            intensity={
                "frp_sum": frp_sum,
                "frp_max": frp_max,
                "count": float(len(members))
            },
            provenance=[
                {"src": "FIRMS", "count": len(members)}
            ]
        )

        out.append(hotspot)

    # Verify postconditions
    verify(
        "cluster_fire",
        assertions=[
            isinstance(out, list),
            all(h.intensity["count"] >= MIN_PTS for h in out)
        ],
        summary=f"clusters={len(out)}"
    )

    logger.info(f"[CLUSTER] Created {len(out)} hotspots from {len(windowed)} signals")
    return out

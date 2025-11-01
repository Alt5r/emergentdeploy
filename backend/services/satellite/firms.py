"""
FIRMS Ingester - NASA Fire Information for Resource Management System

Fetches and parses VIIRS/MODIS active fire detections from NASA FIRMS.
Supports both CSV and GeoJSON formats with automatic detection.
"""

import csv
import io
import os
import requests
import logging
from datetime import datetime, timezone
from typing import List

from .models import SatelliteSignal
from .thinkguard import plan, verify, StepPlan
from .validate import approx_latlon, timestring_is_utc

logger = logging.getLogger(__name__)

# FIRMS URL from environment (required)
FIRMS_URL = os.getenv("FIRMS_URL", "").strip()


def _parse_csv(text: str, source_url: str) -> List[SatelliteSignal]:
    """
    Parse FIRMS CSV format into SatelliteSignal objects.

    CSV columns expected:
    - latitude, longitude (required, numeric)
    - acq_date (YYYY-MM-DD), acq_time (HHMM) (required)
    - frp (Fire Radiative Power, optional)
    - satellite (e.g., VIIRS, MODIS)
    - confidence (numeric or categorical)
    """
    p = StepPlan(
        name="_parse_csv",
        inputs={"len(text)": len(text), "source_url": source_url},
        validations=["CSV header present", "lat/lon numeric in range", "UTC timestamp"],
        edge_cases=["empty CSV", "missing frp", "weird confidence strings"],
        outputs=["List[SatelliteSignal]"]
    )
    plan(p)

    buf = io.StringIO(text)
    reader = csv.DictReader(buf)
    out: List[SatelliteSignal] = []
    dropped = 0

    for i, row in enumerate(reader):
        try:
            # Required fields
            lat = float(row["latitude"])
            lon = float(row["longitude"])

            if not approx_latlon(lat, lon):
                logger.debug(f"[PARSE][CSV] drop line {i}: coords out of range")
                dropped += 1
                continue

            # Parse date/time (FIRMS format: YYYY-MM-DD / HHMM)
            acq_date = row.get("acq_date", "")
            acq_time = row.get("acq_time", "")

            if not acq_date or not acq_time:
                logger.debug(f"[PARSE][CSV] drop line {i}: missing date/time")
                dropped += 1
                continue

            # Combine date and time, convert to ISO8601 UTC
            dt = datetime.strptime(f"{acq_date} {acq_time}", "%Y-%m-%d %H%M")
            dt = dt.replace(tzinfo=timezone.utc)
            time_iso = dt.isoformat()

            # Optional fields
            frp = float(row.get("frp", 0.0)) if row.get("frp") not in (None, "", "nan") else 0.0
            satellite = row.get("satellite", "VIIRS")
            confidence_raw = row.get("confidence", "")

            # Try to parse confidence as numeric
            conf_num = None
            if confidence_raw:
                try:
                    conf_num = float(confidence_raw)
                except ValueError:
                    pass  # Confidence is categorical (e.g., "nominal", "high")

            # Generate unique ID
            signal_id = f"firms:{satellite}:{time_iso}:{lat:.4f},{lon:.4f}"

            out.append(SatelliteSignal(
                id=signal_id,
                hazard="fire",
                time=time_iso,
                lat=lat,
                lon=lon,
                severity={"frp": frp},
                source_name="FIRMS",
                source_url=source_url,
                raw_confidence=conf_num
            ))

        except Exception as e:
            logger.debug(f"[PARSE][CSV] drop line {i}: {e}")
            dropped += 1
            continue

    # Verify postconditions
    verify(
        "_parse_csv",
        assertions=[
            all(approx_latlon(s.lat, s.lon) for s in out),
            all(timestring_is_utc(s.time) for s in out)
        ],
        summary=f"produced={len(out)}, dropped={dropped}"
    )

    logger.info(f"[FIRMS][CSV] Parsed {len(out)} signals (dropped {dropped})")
    return out


def _parse_geojson(obj: dict, source_url: str) -> List[SatelliteSignal]:
    """
    Parse FIRMS GeoJSON format into SatelliteSignal objects.

    GeoJSON structure:
    - features: array of feature objects
    - geometry.coordinates: [lon, lat]
    - properties: {acq_datetime, frp, satellite, confidence}
    """
    p = StepPlan(
        name="_parse_geojson",
        inputs={"keys": list(obj.keys())[:5], "source_url": source_url},
        validations=["FeatureCollection", "coords numeric", "UTC time"],
        edge_cases=["empty features", "missing props fields"],
        outputs=["List[SatelliteSignal]"]
    )
    plan(p)

    feats = obj.get("features", [])
    out: List[SatelliteSignal] = []
    dropped = 0

    for i, f in enumerate(feats):
        try:
            # Extract coordinates (GeoJSON order: [lon, lat])
            coords = f["geometry"]["coordinates"]
            lon, lat = float(coords[0]), float(coords[1])

            if not approx_latlon(lat, lon):
                logger.debug(f"[PARSE][GJ] drop feature {i}: coords out of range")
                dropped += 1
                continue

            props = f.get("properties", {})

            # Try common time field names
            time_raw = props.get("acq_datetime") or props.get("acq_time_iso") or props.get("ACQ_TIME")

            if not time_raw:
                logger.debug(f"[PARSE][GJ] drop feature {i}: missing datetime")
                dropped += 1
                continue

            # Parse and normalize to UTC ISO8601
            # Handle both "Z" and "+00:00" suffixes
            time_iso = datetime.fromisoformat(time_raw.replace("Z", "+00:00"))
            time_iso = time_iso.astimezone(timezone.utc).isoformat()

            # Optional fields
            frp = float(props.get("frp", 0.0) or props.get("FRP", 0.0))
            satellite = props.get("satellite", "VIIRS")
            confidence_raw = props.get("confidence", "")

            # Try to parse confidence as numeric
            conf_num = None
            if confidence_raw:
                try:
                    conf_num = float(confidence_raw)
                except ValueError:
                    pass

            # Generate unique ID
            signal_id = f"firms:{satellite}:{time_iso}:{lat:.4f},{lon:.4f}"

            out.append(SatelliteSignal(
                id=signal_id,
                hazard="fire",
                time=time_iso,
                lat=lat,
                lon=lon,
                severity={"frp": frp},
                source_name="FIRMS",
                source_url=source_url,
                raw_confidence=conf_num
            ))

        except Exception as e:
            logger.debug(f"[PARSE][GJ] drop feature {i}: {e}")
            dropped += 1
            continue

    # Verify postconditions
    verify(
        "_parse_geojson",
        assertions=[
            all(approx_latlon(s.lat, s.lon) for s in out),
            all(timestring_is_utc(s.time) for s in out)
        ],
        summary=f"produced={len(out)}, dropped={dropped}"
    )

    logger.info(f"[FIRMS][GeoJSON] Parsed {len(out)} signals (dropped {dropped})")
    return out


def fetch_firms_signals() -> List[SatelliteSignal]:
    """
    Fetch and parse FIRMS active fire detections.

    Returns:
        List of SatelliteSignal objects

    Raises:
        RuntimeError: If FIRMS_URL not configured
        requests.HTTPError: If HTTP request fails
    """
    p = StepPlan(
        name="fetch_firms_signals",
        inputs={"FIRMS_URL": FIRMS_URL},
        validations=["URL is non-empty", "HTTP 200", "parse path chosen by Content-Type"],
        edge_cases=["rate limit", "empty body", "CSV header mismatch"],
        outputs=["List[SatelliteSignal]"]
    )
    plan(p)

    if not FIRMS_URL:
        raise RuntimeError(
            "FIRMS_URL not set in environment. "
            "Please configure with a valid NASA FIRMS feed URL."
        )

    logger.info(f"[FIRMS] Fetching from: {FIRMS_URL}")

    # Fetch data with timeout
    r = requests.get(FIRMS_URL, timeout=30)
    r.raise_for_status()

    # Detect format by Content-Type or file content
    ctype = r.headers.get("Content-Type", "").lower()
    text = r.text.strip()

    if "json" in ctype or text.startswith("{"):
        data = r.json()
        out = _parse_geojson(data, FIRMS_URL)
    else:
        # Assume CSV
        out = _parse_csv(text, FIRMS_URL)

    # Final verification
    verify(
        "fetch_firms_signals",
        assertions=[isinstance(out, list)],
        summary=f"signals={len(out)} from {FIRMS_URL}"
    )

    return out

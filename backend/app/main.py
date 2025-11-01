"""
FastAPI Application - Crisis Data Aggregator API

This module provides REST API endpoints for accessing crisis event data
"""

import logging
import asyncio
import os
from typing import List, Dict, Optional, Union
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from backend.config import API_CONFIG, LOGGING_CONFIG
from backend.services.aggregator import get_verified_events, CrisisAggregator
from backend.services.satellite.models import Hotspot, SatelliteSignal
from backend.services.satellite.firms import fetch_firms_signals
from backend.services.satellite.usgs import fetch_usgs_earthquakes
from backend.services.satellite.clustering import cluster_hazard

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=LOGGING_CONFIG["level"],
    format=LOGGING_CONFIG["format"]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=API_CONFIG["title"],
    description=API_CONFIG["description"],
    version=API_CONFIG["version"]
)

# Global aggregator instance (could be moved to dependency injection)
aggregator = CrisisAggregator()

# Satellite module storage (in-memory for MVP)
# Organized by hazard type for efficient clustering
SATELLITE_SIGNALS: Dict[str, List[SatelliteSignal]] = {
    "fire": [],
    "earthquake": []
}
SATELLITE_HOTSPOTS: Dict[str, List[Hotspot]] = {
    "fire": [],
    "earthquake": []
}

# Async locks for thread-safe access to global state
_signals_lock = asyncio.Lock()
_hotspots_lock = asyncio.Lock()

# Satellite configuration
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "300"))
SIGNAL_TTL_HOURS = int(os.getenv("SIGNAL_TTL_HOURS", "6"))  # Prune signals older than this


# Pydantic models for API responses
class LocationInfo(BaseModel):
    """Location information"""
    latitude: float
    longitude: float
    display_name: str
    extracted_name: Optional[str] = None


class SourceInfo(BaseModel):
    """Source information"""
    name: str
    url: str


class EventActions(BaseModel):
    """Actions/executables for event (placeholders)"""
    alert_triggered: bool = Field(False, description="TODO: Implement alert system")
    evacuation_planned: bool = Field(False, description="TODO: Implement evacuation planner")


class VerifiedEventResponse(BaseModel):
    """Verified crisis event response"""
    event_id: str
    title: str
    description: str
    published: str
    verified_at: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    source_count: int
    sources: List[SourceInfo]
    locations: List[Dict]
    location_text: Optional[str] = None
    actions: EventActions


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str


class AggregatorStatusResponse(BaseModel):
    """Aggregator configuration status"""
    time_window_hours: int
    min_confidence_threshold: float
    sources_count: int
    enable_human_review: bool
    executables: Dict[str, bool]


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - API health check"""
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "version": API_CONFIG["version"]
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": API_CONFIG["version"]
    }


@app.get(f"{API_CONFIG['prefix']}/status", response_model=AggregatorStatusResponse)
async def get_aggregator_status():
    """Get current aggregator configuration and status"""
    return {
        "time_window_hours": aggregator.config["time_window_hours"],
        "min_confidence_threshold": aggregator.config["min_confidence_threshold"],
        "sources_count": len(aggregator.sources),
        "enable_human_review": aggregator.config["enable_human_review"],
        "executables": aggregator.config["executables"]
    }


@app.get(f"{API_CONFIG['prefix']}/events", response_model=List[VerifiedEventResponse])
async def get_events(
    min_confidence: Optional[float] = Query(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score filter"
    ),
    limit: Optional[int] = Query(
        None,
        ge=1,
        le=100,
        description="Maximum number of events to return"
    )
):
    """
    Get all verified crisis events

    Args:
        min_confidence: Optional minimum confidence score filter
        limit: Optional maximum number of events to return

    Returns:
        List of verified crisis events
    """
    try:
        logger.info("Fetching verified crisis events...")
        events = await get_verified_events()

        # Apply filters
        if min_confidence is not None:
            events = [e for e in events if e["confidence_score"] >= min_confidence]

        if limit is not None:
            events = events[:limit]

        logger.info(f"Returning {len(events)} verified events")
        return events

    except Exception as e:
        logger.error(f"Error fetching events: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch crisis events")


@app.get(f"{API_CONFIG['prefix']}/events/{{event_id}}", response_model=VerifiedEventResponse)
async def get_event_by_id(event_id: str):
    """
    Get a specific crisis event by ID

    Args:
        event_id: Event identifier

    Returns:
        Verified crisis event
    """
    try:
        events = await get_verified_events()

        for event in events:
            if event["event_id"] == event_id:
                return event

        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching event {event_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch event")


@app.post(f"{API_CONFIG['prefix']}/refresh")
async def refresh_events():
    """
    Manually trigger event aggregation refresh

    Returns:
        Summary of refresh operation
    """
    try:
        logger.info("Manual refresh triggered")
        events = await get_verified_events()

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "events_count": len(events),
            "message": "Events refreshed successfully"
        }

    except Exception as e:
        logger.error(f"Error during refresh: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to refresh events")


# ============================================================================
# Satellite Module Endpoints
# ============================================================================

@app.get(f"{API_CONFIG['prefix']}/hotspots", response_model=List[Hotspot])
async def get_hotspots(
    hazard: Optional[str] = Query(None, pattern="^(fire|earthquake)$", description="Hazard type filter (fire, earthquake, or none for all)"),
    min_intensity: Optional[float] = Query(None, ge=0.0, description="Minimum intensity filter (FRP for fires, magnitude for quakes)"),
    since: Optional[str] = Query(None, description="Filter hotspots after this ISO8601 timestamp"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Maximum number of hotspots to return")
):
    """
    Get active hotspots from satellite detections (fires, earthquakes, etc.).

    Returns clustered detections with intensity metrics and provenance.

    Args:
        hazard: Optional hazard type filter ('fire', 'earthquake', or None for all)
        min_intensity: Optional minimum intensity threshold (FRP sum for fires, max magnitude for earthquakes)
        since: Optional ISO8601 timestamp to filter hotspots after this time
        limit: Optional maximum number of hotspots to return

    Returns:
        List of active hotspots
    """
    try:
        # Thread-safe read of hotspots
        async with _hotspots_lock:
            if hazard:
                # Single hazard
                hotspots = list(SATELLITE_HOTSPOTS.get(hazard, []))
            else:
                # All hazards
                hotspots = []
                for hazard_list in SATELLITE_HOTSPOTS.values():
                    hotspots.extend(hazard_list)

        # Apply intensity filter (hazard-specific logic)
        if min_intensity is not None:
            filtered = []
            for h in hotspots:
                if h.hazard == "fire":
                    if h.intensity.get("frp_sum", 0.0) >= min_intensity:
                        filtered.append(h)
                elif h.hazard == "earthquake":
                    if h.intensity.get("mag_max", 0.0) >= min_intensity:
                        filtered.append(h)
                else:
                    filtered.append(h)  # Unknown hazard, include by default
            hotspots = filtered

        # Apply time filter
        if since is not None:
            try:
                since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
                hotspots = [
                    h for h in hotspots
                    if datetime.fromisoformat(h.latest_time.replace("Z", "+00:00")) >= since_dt
                ]
            except ValueError as ve:
                raise HTTPException(status_code=400, detail=f"Invalid 'since' format: {ve}")

        # Sort by latest_time descending (most recent first)
        hotspots.sort(
            key=lambda h: datetime.fromisoformat(h.latest_time.replace("Z", "+00:00")),
            reverse=True
        )

        # Apply limit
        if limit is not None:
            hotspots = hotspots[:limit]

        logger.info(
            f"[API] Returning {len(hotspots)} hotspots "
            f"(hazard={hazard or 'all'}, filters: intensity={min_intensity}, since={since}, limit={limit})"
        )
        return hotspots

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching hotspots: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch hotspots")


@app.post(f"{API_CONFIG['prefix']}/ingest/satellite")
async def ingest_satellite():
    """
    Manually trigger satellite data ingestion and clustering for all hazard types.

    Fetches FIRMS (fires) and USGS (earthquakes), clusters each, and updates hotspots.

    Returns:
        Summary of ingestion operation per hazard
    """
    try:
        logger.info("[SATELLITE] Manual ingestion triggered")

        results = {}

        # Process fires
        fire_result = await _ingest_hazard("fire", fetch_firms_signals)
        results["fire"] = fire_result

        # Process earthquakes
        quake_result = await _ingest_hazard("earthquake", fetch_usgs_earthquakes)
        results["earthquake"] = quake_result

        # Calculate totals
        total_signals = sum(r["signals_added"] for r in results.values())
        total_hotspots = sum(r["hotspots_active"] for r in results.values())

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "total_signals_added": total_signals,
            "total_hotspots_active": total_hotspots,
            "by_hazard": results
        }

    except Exception as e:
        logger.error(f"Error during satellite ingestion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Satellite ingestion failed: {str(e)}")


async def _ingest_hazard(hazard: str, fetch_func) -> dict:
    """
    Helper function to ingest and cluster signals for a specific hazard type.

    Args:
        hazard: Hazard type ('fire', 'earthquake', etc.)
        fetch_func: Function to fetch signals for this hazard

    Returns:
        Dict with ingestion stats
    """
    # Fetch new signals
    new_signals = fetch_func()

    # Thread-safe update of signals
    async with _signals_lock:
        # Merge with existing signals (dedupe by ID)
        known_ids = {s.id for s in SATELLITE_SIGNALS[hazard]}
        added = 0
        for sig in new_signals:
            if sig.id not in known_ids:
                SATELLITE_SIGNALS[hazard].append(sig)
                added += 1

        # Prune old signals (fix memory leak)
        signal_cutoff = datetime.now(timezone.utc) - timedelta(hours=SIGNAL_TTL_HOURS)
        before_prune = len(SATELLITE_SIGNALS[hazard])
        SATELLITE_SIGNALS[hazard] = [
            s for s in SATELLITE_SIGNALS[hazard]
            if datetime.fromisoformat(s.time.replace("Z", "+00:00")) >= signal_cutoff
        ]
        signals_pruned = before_prune - len(SATELLITE_SIGNALS[hazard])

        # Cluster signals into hotspots
        hotspots = cluster_hazard(SATELLITE_SIGNALS[hazard], hazard)

    # Thread-safe update of hotspots
    async with _hotspots_lock:
        SATELLITE_HOTSPOTS[hazard] = hotspots

        # Prune old hotspots (older than 6 hours)
        hotspot_cutoff = datetime.now(timezone.utc) - timedelta(hours=6)
        before_prune_hotspots = len(SATELLITE_HOTSPOTS[hazard])
        SATELLITE_HOTSPOTS[hazard] = [
            h for h in SATELLITE_HOTSPOTS[hazard]
            if datetime.fromisoformat(h.latest_time.replace("Z", "+00:00")) >= hotspot_cutoff
        ]
        hotspots_pruned = before_prune_hotspots - len(SATELLITE_HOTSPOTS[hazard])

    logger.info(
        f"[{hazard.upper()}] Ingestion complete: "
        f"fetched={len(new_signals)}, added={added}, "
        f"signals_pruned={signals_pruned}, "
        f"hotspots={len(SATELLITE_HOTSPOTS[hazard])}, "
        f"hotspots_pruned={hotspots_pruned}"
    )

    return {
        "signals_fetched": len(new_signals),
        "signals_added": added,
        "signals_pruned": signals_pruned,
        "total_signals": len(SATELLITE_SIGNALS[hazard]),
        "hotspots_active": len(SATELLITE_HOTSPOTS[hazard]),
        "hotspots_pruned": hotspots_pruned
    }


@app.get(f"{API_CONFIG['prefix']}/satellite/status")
async def get_satellite_status():
    """
    Get satellite module status and configuration for all hazard types.

    Returns:
        Configuration and current state per hazard
    """
    # Thread-safe read of counts
    async with _signals_lock:
        signal_counts = {h: len(sigs) for h, sigs in SATELLITE_SIGNALS.items()}

    async with _hotspots_lock:
        hotspot_counts = {h: len(spots) for h, spots in SATELLITE_HOTSPOTS.items()}

    return {
        "adapters": {
            "firms": {
                "url": os.getenv("FIRMS_URL", "NOT_SET"),
                "enabled": bool(os.getenv("FIRMS_URL"))
            },
            "usgs": {
                "url": os.getenv("USGS_URL", "NOT_SET"),
                "enabled": bool(os.getenv("USGS_URL"))
            }
        },
        "poll_seconds": POLL_SECONDS,
        "signal_ttl_hours": SIGNAL_TTL_HOURS,
        "clustering": {
            "fire": {
                "eps_km": float(os.getenv("FIRE_EPS_KM", os.getenv("EPS_KM", "5.0"))),
                "min_pts": int(float(os.getenv("FIRE_MIN_PTS", os.getenv("MIN_PTS", "3")))),
                "window_min": int(os.getenv("FIRE_WINDOW_MIN", os.getenv("WINDOW_MIN", "90")))
            },
            "earthquake": {
                "eps_km": float(os.getenv("QUAKE_EPS_KM", "30.0")),
                "min_pts": int(float(os.getenv("QUAKE_MIN_PTS", "2"))),
                "window_min": int(os.getenv("QUAKE_WINDOW_MIN", "1440"))
            }
        },
        "signals_cached": signal_counts,
        "hotspots_active": hotspot_counts,
        "total_signals": sum(signal_counts.values()),
        "total_hotspots": sum(hotspot_counts.values())
    }


# ============================================================================
# TODO: Future endpoints for alert system
@app.post(f"{API_CONFIG['prefix']}/alerts/trigger")
async def trigger_alert(event_id: str):
    """
    TODO: Trigger alert for a specific event
    Placeholder for future alert system implementation
    """
    return {
        "status": "not_implemented",
        "message": "Alert system not yet implemented",
        "event_id": event_id
    }


# TODO: Future endpoints for evacuation planning
@app.post(f"{API_CONFIG['prefix']}/evacuation/plan")
async def plan_evacuation(event_id: str):
    """
    TODO: Generate evacuation plan for a specific event
    Placeholder for future evacuation planner implementation
    """
    return {
        "status": "not_implemented",
        "message": "Evacuation planner not yet implemented",
        "event_id": event_id
    }


# ============================================================================
# Background Worker for Satellite Polling (Multi-Hazard)
# ============================================================================

async def satellite_worker_loop():
    """
    Background worker that periodically fetches satellite data for all enabled hazards.

    Runs continuously with POLL_SECONDS interval between cycles.
    Processes FIRMS (fires) and USGS (earthquakes) in parallel.
    """
    logger.info(f"[SATELLITE WORKER] Starting multi-hazard polling (interval: {POLL_SECONDS}s)")

    while True:
        try:
            logger.info("[SATELLITE WORKER] Polling all enabled adapters...")

            # Process both hazards in parallel using the shared helper
            fire_result = await _ingest_hazard("fire", fetch_firms_signals)
            quake_result = await _ingest_hazard("earthquake", fetch_usgs_earthquakes)

            logger.info(
                f"[SATELLITE WORKER] Cycle complete: "
                f"fires[signals={fire_result['total_signals']}, hotspots={fire_result['hotspots_active']}] "
                f"quakes[signals={quake_result['total_signals']}, hotspots={quake_result['hotspots_active']}]"
            )

        except Exception as e:
            logger.error(f"[SATELLITE WORKER] Error: {e}", exc_info=True)

        # Wait for next poll cycle
        await asyncio.sleep(POLL_SECONDS)


@app.on_event("startup")
async def startup_event():
    """Launch background worker on application startup if any adapter is configured"""
    firms_url = os.getenv("FIRMS_URL", "")
    usgs_url = os.getenv("USGS_URL", "")

    if firms_url or usgs_url:
        adapters = []
        if firms_url:
            adapters.append("FIRMS (fires)")
        if usgs_url:
            adapters.append("USGS (earthquakes)")

        logger.info(f"[STARTUP] Enabled adapters: {', '.join(adapters)}")
        logger.info("[STARTUP] Launching satellite worker...")
        asyncio.create_task(satellite_worker_loop())
    else:
        logger.warning(
            "[STARTUP] No satellite adapters configured - satellite module disabled. "
            "Set FIRMS_URL and/or USGS_URL in .env to enable."
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

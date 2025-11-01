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
from backend.services.satellite.cluster import cluster_fire

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
SATELLITE_SIGNALS: List[SatelliteSignal] = []
SATELLITE_HOTSPOTS: Dict[str, Hotspot] = {}

# Satellite configuration
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "300"))


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
    hazard: str = Query("fire", pattern="^fire$", description="Hazard type (MVP: fire only)"),
    min_intensity: Optional[float] = Query(None, ge=0.0, description="Minimum FRP sum filter")
):
    """
    Get active fire hotspots from satellite detections.

    Returns clustered fire detections with intensity metrics and provenance.

    Args:
        hazard: Hazard type filter (currently only 'fire' supported)
        min_intensity: Optional minimum FRP sum filter

    Returns:
        List of active fire hotspots
    """
    try:
        hotspots = [h for h in SATELLITE_HOTSPOTS.values() if h.hazard == hazard]

        if min_intensity is not None:
            hotspots = [
                h for h in hotspots
                if h.intensity.get("frp_sum", 0.0) >= min_intensity
            ]

        logger.info(f"Returning {len(hotspots)} hotspots (hazard={hazard})")
        return hotspots

    except Exception as e:
        logger.error(f"Error fetching hotspots: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch hotspots")


@app.post(f"{API_CONFIG['prefix']}/ingest/satellite")
async def ingest_satellite():
    """
    Manually trigger satellite data ingestion and clustering.

    This endpoint fetches the latest FIRMS data, clusters it, and updates hotspots.

    Returns:
        Summary of ingestion operation
    """
    try:
        logger.info("[SATELLITE] Manual ingestion triggered")

        # Fetch new signals
        new_signals = fetch_firms_signals()

        # Merge with existing signals (dedupe by ID)
        known_ids = {s.id for s in SATELLITE_SIGNALS}
        added = 0
        for sig in new_signals:
            if sig.id not in known_ids:
                SATELLITE_SIGNALS.append(sig)
                added += 1

        # Cluster signals into hotspots
        hotspots = cluster_fire(SATELLITE_SIGNALS)

        # Update hotspot storage
        for h in hotspots:
            SATELLITE_HOTSPOTS[h.id] = h

        # Prune old hotspots (older than 6 hours)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=6)
        pruned = 0
        for h_id, h in list(SATELLITE_HOTSPOTS.items()):
            h_time = datetime.fromisoformat(h.latest_time.replace("Z", "+00:00"))
            if h_time < cutoff:
                SATELLITE_HOTSPOTS.pop(h_id, None)
                pruned += 1

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "signals_fetched": len(new_signals),
            "signals_added": added,
            "total_signals": len(SATELLITE_SIGNALS),
            "hotspots_active": len(SATELLITE_HOTSPOTS),
            "hotspots_pruned": pruned
        }

    except Exception as e:
        logger.error(f"Error during satellite ingestion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Satellite ingestion failed: {str(e)}")


@app.get(f"{API_CONFIG['prefix']}/satellite/status")
async def get_satellite_status():
    """
    Get satellite module status and configuration.

    Returns:
        Configuration and current state
    """
    return {
        "firms_url": os.getenv("FIRMS_URL", "NOT_SET"),
        "poll_seconds": POLL_SECONDS,
        "window_min": int(os.getenv("WINDOW_MIN", "90")),
        "eps_km": float(os.getenv("EPS_KM", "5.0")),
        "min_pts": int(float(os.getenv("MIN_PTS", "3"))),
        "signals_cached": len(SATELLITE_SIGNALS),
        "hotspots_active": len(SATELLITE_HOTSPOTS)
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
# Background Worker for Satellite Polling
# ============================================================================

async def satellite_worker_loop():
    """
    Background worker that periodically fetches FIRMS data and updates hotspots.

    Runs continuously with POLL_SECONDS interval between cycles.
    """
    logger.info(f"[SATELLITE WORKER] Starting (poll interval: {POLL_SECONDS}s)")

    while True:
        try:
            logger.info("[SATELLITE WORKER] Polling FIRMS...")

            # Fetch new signals
            new_signals = fetch_firms_signals()

            # Merge with existing signals (dedupe by ID)
            known_ids = {s.id for s in SATELLITE_SIGNALS}
            added = 0
            for sig in new_signals:
                if sig.id not in known_ids:
                    SATELLITE_SIGNALS.append(sig)
                    added += 1

            # Cluster signals into hotspots
            hotspots = cluster_fire(SATELLITE_SIGNALS)

            # Update hotspot storage
            for h in hotspots:
                SATELLITE_HOTSPOTS[h.id] = h

            # Prune old hotspots (older than 6 hours)
            cutoff = datetime.now(timezone.utc) - timedelta(hours=6)
            pruned = 0
            for h_id, h in list(SATELLITE_HOTSPOTS.items()):
                h_time = datetime.fromisoformat(h.latest_time.replace("Z", "+00:00"))
                if h_time < cutoff:
                    SATELLITE_HOTSPOTS.pop(h_id, None)
                    pruned += 1

            logger.info(
                f"[SATELLITE WORKER] Cycle complete: "
                f"fetched={len(new_signals)}, added={added}, "
                f"signals_total={len(SATELLITE_SIGNALS)}, "
                f"hotspots={len(SATELLITE_HOTSPOTS)}, pruned={pruned}"
            )

        except Exception as e:
            logger.error(f"[SATELLITE WORKER] Error: {e}", exc_info=True)

        # Wait for next poll cycle
        await asyncio.sleep(POLL_SECONDS)


@app.on_event("startup")
async def startup_event():
    """Launch background worker on application startup"""
    firms_url = os.getenv("FIRMS_URL", "")

    if firms_url:
        logger.info("[STARTUP] FIRMS_URL configured, launching satellite worker")
        asyncio.create_task(satellite_worker_loop())
    else:
        logger.warning(
            "[STARTUP] FIRMS_URL not set - satellite module disabled. "
            "Set FIRMS_URL in .env to enable fire hotspot detection."
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

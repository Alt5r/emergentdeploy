"""
FastAPI Application - Crisis Data Aggregator API

This module provides REST API endpoints for accessing crisis event data
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.config import API_CONFIG, LOGGING_CONFIG
from backend.services.aggregator import get_verified_events, CrisisAggregator
from backend.services.historical_data import get_historical_events_for_date

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
    ),
    countries: Optional[str] = Query(
        None,
        description="Comma-separated list of country codes to filter (e.g., 'US,GB' for USA and UK)"
    ),
    historical_date: Optional[str] = Query(
        None,
        description="Fetch historical data for a specific date (format: YYYY-MM-DD, e.g., '2025-01-07')"
    )
):
    """
    Get all verified crisis events

    Args:
        min_confidence: Optional minimum confidence score filter
        limit: Optional maximum number of events to return
        countries: Optional comma-separated list of country codes to filter
        historical_date: Optional date to fetch historical disaster data

    Returns:
        List of verified crisis events
    """
    try:
        logger.info("Fetching verified crisis events...")

        # Use historical data if date is specified
        if historical_date:
            logger.info(f"Using historical data for date: {historical_date}")
            events = get_historical_events_for_date(historical_date)
        else:
            events = await get_verified_events()

        # Apply confidence filter
        if min_confidence is not None:
            events = [e for e in events if e["confidence_score"] >= min_confidence]

        # Apply country filter
        if countries:
            country_codes = [c.strip().upper() for c in countries.split(',')]
            logger.info(f"Filtering events for countries: {country_codes}")
            filtered_events = []
            for event in events:
                if event.get('locations'):
                    for location in event['locations']:
                        display_name = location.get('display_name', '').upper()
                        # Check if any of the requested countries appear in the location name
                        if any(
                            ('UNITED STATES' in display_name or 'USA' in display_name or ', US' in display_name) if code == 'US'
                            else ('UNITED KINGDOM' in display_name or 'UK' in display_name or ', GB' in display_name) if code == 'GB'
                            else code in display_name
                            for code in country_codes
                        ):
                            filtered_events.append(event)
                            break
            events = filtered_events

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

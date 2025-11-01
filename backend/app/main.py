"""
FastAPI Application - Crisis Data Aggregator API

This module provides REST API endpoints for accessing crisis event data
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.config import API_CONFIG, LOGGING_CONFIG
from backend.services.aggregator import get_verified_events, CrisisAggregator
from backend.services.historical_data import get_historical_events_for_date
from backend.services.fema_shelters import FEMAShelterService

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

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global aggregator instance (could be moved to dependency injection)
aggregator = CrisisAggregator()
fema_service = FEMAShelterService()


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


# FEMA Shelter endpoints
@app.get("/api/v1/shelters")
async def get_shelters(
    state: Optional[str] = Query(None, description="Two-letter state code (e.g., CA, TX)"),
    status: Optional[str] = Query(None, description="Shelter status (OPEN, CLOSED)")
):
    """
    Get FEMA shelter data

    Returns shelters filtered by state and/or status
    """
    try:
        shelters = fema_service.get_shelters(state=state, status=status)
        return {
            "status": "success",
            "count": len(shelters),
            "shelters": shelters
        }
    except Exception as e:
        logger.error(f"Error fetching shelters: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch shelter data")


@app.get("/api/v1/shelters/california")
async def get_california_shelters():
    """
    Get all shelters in California

    Convenience endpoint for California-specific shelter data
    """
    try:
        shelters = fema_service.get_california_shelters()
        return {
            "status": "success",
            "state": "CA",
            "count": len(shelters),
            "shelters": shelters
        }
    except Exception as e:
        logger.error(f"Error fetching California shelters: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch California shelter data")


# Tropical Storm endpoints
@app.get("/api/v1/storms")
async def get_active_storms():
    """
    Get active tropical storms and hurricanes

    Returns storm data from NHC including position, intensity, and forecast
    """
    try:
        import json
        from pathlib import Path

        storms_file = Path(__file__).parent.parent / "services" / "notifs" / "TS_data" / "active_storms_data.json"

        if storms_file.exists():
            with open(storms_file, 'r') as f:
                storms = json.load(f)
            return {
                "status": "success",
                "count": len(storms),
                "storms": storms
            }
        else:
            return {
                "status": "success",
                "count": 0,
                "storms": []
            }
    except Exception as e:
        logger.error(f"Error fetching storms: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch storm data")


# Tsunami/DART station endpoints
@app.get("/api/v1/tsunami/stations")
async def get_dart_stations():
    """
    Get DART tsunami buoy station locations

    Returns coordinates of all DART stations for tsunami monitoring
    """
    try:
        import csv
        from pathlib import Path

        stations_file = Path(__file__).parent.parent / "services" / "notifs" / "T_data" / "dart_stations_coordinates.csv"

        if stations_file.exists():
            stations = []
            with open(stations_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    stations.append({
                        "station_id": row['station_id'],
                        "latitude": float(row['latitude']),
                        "longitude": float(row['longitude'])
                    })

            return {
                "status": "success",
                "count": len(stations),
                "stations": stations
            }
        else:
            return {
                "status": "success",
                "count": 0,
                "stations": []
            }
    except Exception as e:
        logger.error(f"Error fetching DART stations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch DART station data")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

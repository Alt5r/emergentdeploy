"""
Configuration for Crisis Data Aggregator

This module contains all configuration settings for the aggregator system.
"""

from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Crisis Data Aggregator Configuration
AGGREGATOR_CONFIG = {
    # Time window for event correlation (in hours)
    # Events within this window from different sources are considered related
    "time_window_hours": 3,

    # Minimum confidence score (0.0 - 1.0) for an event to be considered verified
    # Events below this threshold will be flagged for human review
    # Lowered to 0.3 to capture small-scale local events
    "min_confidence_threshold": 0.3,

    # Path to RSS sources configuration file
    "sources_file": BASE_DIR / "services" / "data" / "sources.json",

    # Enable manual review queue for low-confidence events
    "enable_human_review": True,

    # Future executable modules (currently disabled - placeholders only)
    "executables": {
        "alert_system": False,          # TODO: Implement alert/notification system
        "evacuation_planner": False     # TODO: Implement evacuation route planning
    },

    # Geocoding settings
    "geocoding": {
        "user_agent": "EmergentCrisisAggregator/1.0",
        "timeout": 5,  # seconds
        "cache_ttl": 86400,  # 24 hours in seconds
    },

    # Confidence scoring weights
    "confidence_weights": {
        "source_count": 0.4,        # Weight for number of sources reporting
        "time_proximity": 0.3,      # Weight for timestamp clustering
        "location_match": 0.2,      # Weight for location consistency
        "source_reliability": 0.1   # Weight for source reliability score
    }
}

# API Configuration
API_CONFIG = {
    "title": "Emergent Crisis Data Aggregator API",
    "description": "Real-time crisis event aggregation and verification system",
    "version": "1.0.0",
    "prefix": "/api/v1"
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
}

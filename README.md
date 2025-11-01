# Emergent - Crisis Data Aggregator

A real-time crisis and disaster event aggregation system that collects, verifies, and cross-references data from multiple news sources to provide reliable emergency information.

## Overview

Emergent aggregates disaster-related news from reliable sources including major news agencies (Reuters, AP, BBC), government agencies (FEMA, USGS, NWS), and specialized disaster monitoring services. It uses intelligent cross-verification and confidence scoring to filter out noise and provide verified crisis events.

## Features

- **Multi-source RSS aggregation** from 10+ reliable news sources
- **Cross-source verification** with confidence scoring
- **Geocoding integration** for location extraction and mapping
- **RESTful API** built with FastAPI
- **Clean placeholders** for future alert and evacuation systems
- **Configurable thresholds** for event verification

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the API Server
```bash
# From project root
python backend/app/main.py

# Or with uvicorn
uvicorn backend.app.main:app --reload
```

### 3. Access the API
- API Base: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- API Documentation: http://localhost:8000/redoc

### 4. Try Sample Requests
```bash
# Get all verified events
curl http://localhost:8000/api/v1/events

# Get high-confidence events only
curl "http://localhost:8000/api/v1/events?min_confidence=0.8"

# Get aggregator status
curl http://localhost:8000/api/v1/status
```

## Project Structure

```
Emergent/
├── backend/
│   ├── config.py                    # Configuration
│   ├── app/
│   │   └── main.py                  # FastAPI application
│   └── services/
│       ├── aggregator.py            # Core aggregation logic
│       ├── utils_geo.py             # Geocoding utilities
│       └── data/
│           └── sources.json         # RSS feed sources
├── docs/
│   └── crisis_aggregator_progress.md  # Detailed documentation
├── tests/                           # Unit tests (TODO)
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## Documentation

For detailed implementation information, architecture overview, and progress tracking, see:
- **[Crisis Aggregator Progress Document](docs/crisis_aggregator_progress.md)**

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/events` | Get all verified crisis events |
| GET | `/api/v1/events/{event_id}` | Get specific event by ID |
| GET | `/api/v1/status` | Get aggregator configuration |
| POST | `/api/v1/refresh` | Manually trigger aggregation |

## Configuration

Edit `backend/config.py` to customize:
- Time window for event correlation (default: 3 hours)
- Minimum confidence threshold (default: 0.6)
- Confidence scoring weights
- Geocoding settings

## Future Features

- Alert/notification system integration
- Evacuation route planning
- Historical data storage
- Real-time WebSocket updates
- Human review queue for low-confidence events

## Tech Stack

- **FastAPI** - Modern web framework
- **feedparser** - RSS feed parsing
- **geopy** - Geocoding (Nominatim/OSM)
- **Pydantic** - Data validation
- **uvicorn** - ASGI server

## Contributing

See the [progress document](docs/crisis_aggregator_progress.md) for implementation status and future enhancements.

## License

A collaborative project.

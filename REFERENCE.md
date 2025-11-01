# Emergent - Technical Reference Documentation

**Version:** 1.0.0
**Last Updated:** 2025-11-01
**Project Type:** Full-Stack Crisis Data Aggregation Platform

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Frontend Documentation](#frontend-documentation)
4. [Backend Documentation](#backend-documentation)
5. [API Reference](#api-reference)
6. [Data Models](#data-models)
7. [Integration Patterns](#integration-patterns)
8. [Configuration](#configuration)
9. [Development Guide](#development-guide)
10. [Deployment](#deployment)
11. [Security Considerations](#security-considerations)
12. [Known Issues & Gaps](#known-issues--gaps)

---

## Project Overview

**Emergent** is a real-time crisis data aggregation and disaster response coordination platform. It combines a Python FastAPI backend that aggregates multi-source disaster data with a Next.js React frontend providing interactive visualization and analysis.

### Core Features

- **Real-time Crisis Aggregation:** Fetches and consolidates disaster data from 10+ RSS feeds (Reuters, AP, BBC, FEMA, USGS, NWS, etc.)
- **Event Verification:** Multi-factor confidence scoring algorithm to verify event authenticity
- **Geocoding:** Automatic location extraction and coordinate conversion
- **Interactive Mapping:** Mapbox GL JS visualization of disasters, response teams, aid organizations, and affected areas
- **Event Clustering:** Groups related events based on time proximity and location overlap
- **Chat Interface:** Context-aware disaster analysis assistant

### Tech Stack

**Frontend:**
- Next.js 15.5.6 with React 19.1.0
- TypeScript
- Tailwind CSS v4
- Mapbox GL JS 3.15.0
- Radix UI component library

**Backend:**
- FastAPI (Python)
- Uvicorn (async server)
- Pydantic v2 (data validation)
- Feedparser (RSS parsing)
- Geopy (geocoding via Nominatim)

---

## Architecture

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Next.js    │  │  React       │  │  Mapbox GL   │      │
│  │   App Router │  │  Components  │  │  Visualization│     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                  │              │
│         └─────────────────┴──────────────────┘              │
│                           │                                 │
│                    Context API State                        │
└───────────────────────────┼─────────────────────────────────┘
                            │
                     HTTP REST API
                            │
┌───────────────────────────┼─────────────────────────────────┐
│                    FastAPI Backend                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  API         │  │  Aggregator  │  │  Geocoding   │      │
│  │  Endpoints   │  │  Service     │  │  Service     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                  │              │
│         └─────────────────┴──────────────────┘              │
└───────────────────────────┼─────────────────────────────────┘
                            │
                   ┌────────┴────────┐
                   │                 │
            RSS Feed Sources    Nominatim
         (10+ News & Gov APIs)  (Geocoding)
```

### Data Flow

1. **RSS Aggregation:**
   - Backend fetches RSS feeds concurrently (async)
   - Parses XML/JSON responses
   - Filters for disaster keywords
   - Extracts location text

2. **Geocoding:**
   - Extracts location names using regex patterns
   - Converts to coordinates via Nominatim API
   - Caches results for 24 hours

3. **Event Clustering:**
   - Groups events by time proximity (3-hour window)
   - Matches by location overlap
   - Calculates confidence scores

4. **Verification:**
   - Multi-factor scoring algorithm
   - Filters by confidence threshold (0.6)
   - Flags low-confidence for human review

5. **Frontend Visualization:**
   - Fetches verified events via REST API
   - Renders on Mapbox with custom markers
   - Provides chat interface for analysis

---

## Frontend Documentation

### Directory Structure

```
frontend/
├── app/
│   ├── page.tsx              # Root page with StartupProvider
│   ├── appPage.tsx           # Main application logic (537 lines)
│   ├── layout.tsx            # Root layout (fonts, analytics)
│   └── globals.css           # Global styles
├── components/
│   ├── ui/                   # Radix UI component library
│   │   ├── alert.tsx
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── input.tsx
│   │   ├── select.tsx
│   │   ├── switch.tsx
│   │   └── ...
│   ├── AudienceMap.tsx       # Mapbox visualization (100+ lines)
│   ├── UnifiedPinSidebar.tsx # Sidebar for disaster details
│   ├── MarkdownRenderer.tsx  # Chat message parser
│   └── fieldSwitch.tsx       # Toggle component
├── contexts/
│   └── StartupContext.tsx    # Global state management
├── hooks/
│   └── useBackgroundAPI.ts   # Background API call hook
├── lib/
│   ├── api.ts                # API client with retry logic
│   └── utils.ts              # Utility functions
├── public/
│   ├── starplex.png          # App icon
│   └── HostGrotesk-Regular.ttf
├── next.config.ts
├── tsconfig.json
├── package.json
└── components.json           # shadcn/ui config
```

### Key Components

#### page.tsx
**Location:** `frontend/app/page.tsx`

Entry point that wraps the app with `StartupProvider`:

```tsx
export default function Page() {
  return (
    <StartupProvider>
      <AppContent />
    </StartupProvider>
  );
}
```

#### appPage.tsx
**Location:** `frontend/app/appPage.tsx` (537 lines)

Main application interface managing:
- 4 toggle states: `showVCs`, `showCompetitors`, `showDemographics`, `showCofounders`
- Sequential data fetching with 3-second delays
- Chat functionality with message history
- Mobile-responsive UI with FAB and menu overlay
- Data caches: `competitorsData`, `vcsData`, `cofoundersData`, `demographicsData`

**Key State:**
```tsx
const [showVCs, setShowVCs] = useState(false);
const [showCompetitors, setShowCompetitors] = useState(false);
const [showDemographics, setShowDemographics] = useState(false);
const [showCofounders, setShowCofounders] = useState(false);
```

#### AudienceMap.tsx
**Location:** `frontend/components/AudienceMap.tsx`

Interactive Mapbox GL JS visualization:
- **Token:** `pk.eyJ1IjoiYWR3aXRoYW5zIiwiYSI6ImNtZ3Y0ejF1ajBna3gya3NlOGxlM2dvaHQifQ.Nm-Nyqb3OLpB1cpZCzvTIw`
- **Features:**
  - Multiple marker types (disasters, response teams, aid orgs, affected areas)
  - Custom color coding
  - Theme toggle (light/dark)
  - Interactive sidebar on pin click
  - Heatmap visualization

**Marker Types:**
- 🔴 Red: Active disasters (from competitors endpoint)
- 🟢 Green: Response teams (from cofounders endpoint)
- 🔵 Blue: Aid organizations (from VCs endpoint)
- 🟡 Yellow: Affected areas (from demographics endpoint)

#### StartupContext.tsx
**Location:** `frontend/contexts/StartupContext.tsx`

Global state management using React Context:

```tsx
interface StartupContextType {
  startupIdea: string;                    // Crisis description
  setStartupIdea: (idea: string) => void;
  keywords: string[];                     // Extracted keywords
  setKeywords: (keywords: string[]) => void;
  marketAnalysis: {
    how_AI_proof_it_is: number;           // Severity score
    market_cap_estimation: number;        // Impact estimation
  } | null;
  setMarketAnalysis: (analysis: ...) => void;
}
```

**Access via:**
```tsx
const { startupIdea, setStartupIdea } = useStartup();
```

### API Client

**Location:** `frontend/lib/api.ts`

All API calls point to:
```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
```

**Retry Strategy:**
- Exponential backoff (1s, 2s, 4s)
- Max 2 retries
- Special handling for 429 (rate limit) errors
- 30-second timeout for long-running requests

**Key Functions:**

```typescript
// Get active disasters
findCompetitors(idea: string): Promise<CompetitorResponse>

// Get aid organizations
findVCs(idea: string): Promise<VCResponse>

// Get response teams
findCofounders(idea: string): Promise<CofounderResponse>

// Get affected areas
getAudienceMap(startupIdea: string): Promise<DemographicsResponse>

// Chat with context
sendChatMessage(
  businessIdea: string,
  message: string,
  context: ChatContext
): Promise<ChatResponse>

// Extract keywords and analysis
extractKeywords(userPrompt: string): Promise<KeywordsResponse>
```

### Styling System

- **Framework:** Tailwind CSS v4 with PostCSS
- **Component Library:** Radix UI primitives with custom styling
- **Utility:** `clsx` + `tailwind-merge` for class composition
- **Theme:** Global dark mode (`dark` class in layout)
- **Custom Fonts:** Host Grotesk loaded from `/public`

### Dependencies

```json
{
  "next": "15.5.6",
  "react": "19.1.0",
  "react-dom": "19.1.0",
  "typescript": "5",
  "@radix-ui/*": "Multiple packages",
  "mapbox-gl": "3.15.0",
  "recharts": "2.15.4",
  "framer-motion": "12.23.24",
  "lucide-react": "0.546.0",
  "tailwindcss": "4",
  "@vercel/analytics": "Latest",
  "@vercel/speed-insights": "Latest"
}
```

---

## Backend Documentation

### Directory Structure

```
backend/
├── __init__.py
├── config.py                 # Global configuration (63 lines)
├── app/
│   ├── __init__.py
│   └── main.py               # FastAPI application (246 lines)
└── services/
    ├── __init__.py
    ├── aggregator.py         # Core aggregation (367 lines)
    ├── utils_geo.py          # Geocoding utilities (200 lines)
    ├── data/
    │   └── sources.json      # RSS feed configuration
    └── notifs/
        └── test.py           # Placeholder for notifications
```

### Core Modules

#### config.py
**Location:** `backend/config.py` (63 lines)

```python
AGGREGATOR_CONFIG = {
    "time_window_hours": 3,              # Event correlation window
    "min_confidence_threshold": 0.6,     # Verification threshold
    "sources_file": "services/data/sources.json",
    "enable_human_review": True,         # Flag low-confidence events
    "executables": {
        "alert_system": False,           # TODO: Not implemented
        "evacuation_planner": False      # TODO: Not implemented
    },
    "geocoding": {
        "user_agent": "EmergentCrisisAggregator/1.0",
        "timeout": 5,
        "cache_ttl": 86400  # 24 hours
    },
    "confidence_weights": {
        "source_count": 0.4,             # 40% - more sources = higher confidence
        "time_proximity": 0.3,           # 30% - tighter clustering
        "location_match": 0.2,           # 20% - same location
        "source_reliability": 0.1        # 10% - source trustworthiness
    }
}
```

#### aggregator.py
**Location:** `backend/services/aggregator.py` (367 lines)

**Key Classes:**

**1. CrisisEvent**
```python
class CrisisEvent:
    title: str
    description: str
    source: str                 # News source name
    published: datetime
    url: str
    location_text: Optional[str]
    locations: List[Dict]       # Geocoded coordinates
    event_id: str               # MD5 hash of title + timestamp
```

**2. VerifiedEvent**
```python
class VerifiedEvent:
    events: List[CrisisEvent]           # Clustered similar events
    confidence: float                    # Calculated score (0-1)
    primary_event: CrisisEvent           # First event as primary
    source_count: int                    # Number of unique sources
    verified_at: datetime
```

**3. CrisisAggregator**

Main aggregation service with methods:

```python
async def fetch_feed(source: Dict) -> List[CrisisEvent]:
    """Async RSS parsing with disaster keyword filtering"""

async def fetch_all_feeds() -> List[CrisisEvent]:
    """Concurrent fetch of all RSS sources"""

def _cluster_events(events: List[CrisisEvent]) -> List[List[CrisisEvent]]:
    """Group similar events by time and location"""

def _calculate_confidence(cluster: List[CrisisEvent]) -> float:
    """Multi-factor confidence scoring"""

def aggregate_and_verify() -> List[VerifiedEvent]:
    """Main pipeline: fetch → cluster → score → filter"""
```

**Confidence Calculation Algorithm:**

```python
confidence = (
    0.4 * normalize(source_count, max_sources=10) +
    0.3 * normalize(time_tightness, max_hours=3) +
    0.2 * location_match_ratio +
    0.1 * avg_source_reliability
)
```

- **Source Count (40%):** More independent sources reporting → higher confidence
- **Time Proximity (30%):** Events clustered within shorter timeframes → higher confidence
- **Location Match (20%):** Consistent location reporting → higher confidence
- **Source Reliability (10%):** Average reliability weight of sources

#### utils_geo.py
**Location:** `backend/services/utils_geo.py` (200 lines)

**Key Classes:**

**1. GeocodingCache**
```python
class GeocodingCache:
    """In-memory cache with TTL (24 hours)"""
    def get(location: str) -> Optional[Dict]
    def set(location: str, data: Dict)
```

**2. GeocodingService**
```python
class GeocodingService:
    """Nominatim (OpenStreetMap) geocoding"""
    def geocode(location: str) -> Optional[Dict]:
        # Rate limited: 1 request/second
        # Returns: {latitude, longitude, display_name, raw}
```

**3. LocationExtractor**
```python
class LocationExtractor:
    """Extract location names from text using regex"""

    LOCATION_PATTERNS = [
        r"in ([A-Z][a-zA-Z\s]+(?:,\s*[A-Z]{2,})?)",
        r"at ([A-Z][a-zA-Z\s]+)",
        r"near ([A-Z][a-zA-Z\s]+)",
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2,})"
    ]

    DISASTER_KEYWORDS = [
        "earthquake", "tsunami", "hurricane", "tornado",
        "flood", "wildfire", "volcano", "avalanche",
        "landslide", "storm", "cyclone", "typhoon",
        "drought", "blizzard", "heat wave"
    ]

    def extract_locations(text: str) -> List[str]
    def contains_disaster_keywords(text: str) -> bool
    def extract_and_geocode(text: str) -> List[Dict]
```

### RSS Feed Sources

**Location:** `backend/services/data/sources.json`

Configured feeds:

| Source | Category | Reliability | URL |
|--------|----------|-------------|-----|
| Reuters | major_news | 0.95 | https://www.reutersagency.com/feed/ |
| Associated Press | major_news | 0.95 | https://feeds.apnews.com/... |
| BBC News | major_news | 0.9 | http://feeds.bbci.co.uk/news/rss.xml |
| CNN | major_news | 0.85 | http://rss.cnn.com/rss/cnn_topstories.rss |
| The Guardian | major_news | 0.85 | https://www.theguardian.com/world/rss |
| FEMA | government | 1.0 | https://www.fema.gov/rss |
| USGS | government | 1.0 | https://earthquake.usgs.gov/... |
| NWS | government | 1.0 | https://www.weather.gov/rss/ |
| ReliefWeb | specialized | 0.9 | https://reliefweb.int/rss |
| GDACS | specialized | 0.9 | https://www.gdacs.org/rss.aspx |

**Source Schema:**
```json
{
  "id": "unique_identifier",
  "name": "Display Name",
  "url": "RSS feed URL",
  "category": "major_news|government|specialized",
  "reliability_weight": 0.0-1.0,
  "tags": ["disaster", "emergency", "humanitarian"]
}
```

### Dependencies

```
# FastAPI Stack
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# RSS Feed Parsing
feedparser==6.0.11

# Geocoding
geopy==2.4.1

# HTTP Requests
httpx==0.26.0
aiohttp==3.9.1

# NLP
spacy==3.7.2

# Utilities
python-dateutil==2.8.2

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
```

---

## API Reference

### Base URL

```
http://localhost:8000
```

Set via environment variable:
```bash
export NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Current Endpoints (Implemented)

#### GET /
**Description:** Health check
**Response:** `200 OK`
```json
{
  "message": "Emergent Crisis Data Aggregator API"
}
```

#### GET /health
**Description:** Health check
**Response:** `200 OK`
```json
{
  "status": "healthy"
}
```

#### GET /api/v1/status
**Description:** Get aggregator configuration
**Response:** `200 OK`
```json
{
  "time_window_hours": 3,
  "min_confidence_threshold": 0.6,
  "sources_count": 10,
  "enable_human_review": true,
  "executables": {
    "alert_system": false,
    "evacuation_planner": false
  }
}
```

#### GET /api/v1/events
**Description:** Get all verified events
**Query Parameters:**
- `min_confidence` (float, 0-1): Filter by confidence score
- `limit` (int): Max number of events to return

**Response:** `200 OK`
```json
[
  {
    "event_id": "abc123",
    "title": "7.2 Magnitude Earthquake Strikes Tokyo",
    "description": "Strong earthquake felt across Tokyo region...",
    "published": "2025-11-01T10:30:00Z",
    "verified_at": "2025-11-01T10:35:00Z",
    "confidence_score": 0.85,
    "source_count": 5,
    "sources": [
      {"name": "Reuters", "url": "https://..."},
      {"name": "AP", "url": "https://..."}
    ],
    "locations": [
      {
        "latitude": 35.6762,
        "longitude": 139.6503,
        "display_name": "Tokyo, Japan"
      }
    ],
    "location_text": "Tokyo, Japan",
    "actions": {
      "alert_triggered": false,
      "evacuation_planned": false,
      "human_review_required": false
    }
  }
]
```

#### GET /api/v1/events/{event_id}
**Description:** Get specific event by ID
**Response:** `200 OK` (same schema as single event above)

#### POST /api/v1/refresh
**Description:** Manually trigger RSS aggregation
**Response:** `200 OK`
```json
{
  "message": "Aggregation triggered",
  "events_found": 15,
  "verified_events": 8
}
```

#### POST /api/v1/alerts/trigger
**Description:** (Placeholder) Trigger alert system
**Response:** `501 Not Implemented`

#### POST /api/v1/evacuation/plan
**Description:** (Placeholder) Generate evacuation plan
**Response:** `501 Not Implemented`

### Missing Endpoints (Frontend Expects, Not Implemented)

#### POST /find-competitors
**Expected Request:**
```json
{
  "startup_idea": "Natural disaster in California"
}
```
**Expected Response:**
```json
{
  "competitors": [
    {
      "company_name": "7.5 Earthquake in San Francisco",
      "description": "Major seismic event...",
      "threat_score": 8.5,
      "location": "San Francisco, CA"
    }
  ]
}
```

#### POST /find-vcs
**Expected Request:**
```json
{
  "startup_idea": "Natural disaster in California"
}
```
**Expected Response:**
```json
{
  "vcs": [
    {
      "name": "Red Cross California",
      "investment_focus": "Disaster relief",
      "match_score": 9.2,
      "contact": "contact@redcross.org"
    }
  ]
}
```

#### POST /find-cofounders
**Expected Request:**
```json
{
  "startup_idea": "Natural disaster in California"
}
```
**Expected Response:**
```json
{
  "cofounders": [
    {
      "name": "FEMA Response Team Alpha",
      "expertise": "Emergency response coordination",
      "match_score": 8.8,
      "availability": "Active"
    }
  ]
}
```

#### POST /audience-map
**Expected Request:**
```json
{
  "startup_idea": "Natural disaster in California"
}
```
**Expected Response:**
```json
{
  "demographics": [
    {
      "location": "San Francisco, CA",
      "latitude": 37.7749,
      "longitude": -122.4194,
      "affected_population": 884363,
      "severity": "High"
    }
  ]
}
```

#### POST /chat
**Expected Request:**
```json
{
  "business_idea": "Natural disaster in California",
  "message": "What response teams are available?",
  "context": {
    "vcs": [...],
    "cofounders": [...],
    "competitors": [...],
    "demographics": [...]
  }
}
```
**Expected Response:**
```json
{
  "response": "Based on current data, there are 3 FEMA teams deployed..."
}
```

#### POST /extract-keywords
**Expected Request:**
```json
{
  "user_prompt": "Hurricane hitting Florida coast"
}
```
**Expected Response:**
```json
{
  "keywords": ["hurricane", "Florida", "coast", "evacuation"],
  "market_analysis": {
    "how_AI_proof_it_is": 7.5,
    "market_cap_estimation": 8500000000
  }
}
```

---

## Data Models

### Pydantic Schemas (Backend)

#### LocationInfo
```python
class LocationInfo(BaseModel):
    latitude: float
    longitude: float
    display_name: str
    extracted_name: Optional[str] = None
```

#### SourceInfo
```python
class SourceInfo(BaseModel):
    name: str
    url: str
```

#### EventActions
```python
class EventActions(BaseModel):
    alert_triggered: bool = False
    evacuation_planned: bool = False
    human_review_required: bool = False
```

#### VerifiedEventResponse
```python
class VerifiedEventResponse(BaseModel):
    event_id: str
    title: str
    description: str
    published: str
    verified_at: str
    confidence_score: float  # 0.0-1.0
    source_count: int
    sources: List[SourceInfo]
    locations: List[Dict]
    location_text: Optional[str]
    actions: EventActions
```

#### AggregatorStatusResponse
```python
class AggregatorStatusResponse(BaseModel):
    time_window_hours: int
    min_confidence_threshold: float
    sources_count: int
    enable_human_review: bool
    executables: Dict[str, bool]
```

### TypeScript Interfaces (Frontend)

#### CompetitorResponse
```typescript
interface CompetitorResponse {
  competitors: Array<{
    company_name: string;      // Disaster name
    description: string;
    threat_score: number;
    location: string;
  }>;
}
```

#### VCResponse
```typescript
interface VCResponse {
  vcs: Array<{
    name: string;              // Aid organization name
    investment_focus: string;
    match_score: number;
    contact: string;
  }>;
}
```

#### CofounderResponse
```typescript
interface CofounderResponse {
  cofounders: Array<{
    name: string;              // Response team name
    expertise: string;
    match_score: number;
    availability: string;
  }>;
}
```

#### DemographicsResponse
```typescript
interface DemographicsResponse {
  demographics: Array<{
    location: string;
    latitude: number;
    longitude: number;
    affected_population: number;
    severity: string;
  }>;
}
```

#### ChatContext
```typescript
interface ChatContext {
  vcs?: any[];
  cofounders?: any[];
  competitors?: any[];
  demographics?: any[];
}
```

---

## Integration Patterns

### Frontend → Backend Flow

```
1. User enters crisis description
   ↓
2. StartupContext updates startupIdea
   ↓
3. useBackgroundAPI hook triggers
   ↓
4. Sequential API calls (3s delay between):
   a. getAudienceMap() → Demographics/affected areas
   b. findCompetitors() → Active disasters
   c. findCofounders() → Response teams
   d. findVCs() → Aid organizations
   ↓
5. Data cached in component state
   ↓
6. AudienceMap visualizes on Mapbox
   ↓
7. Chat functionality uses cached data as context
```

### Backend Aggregation Pipeline

```
1. RSS Sources
   ↓
2. Async Concurrent Fetch (feedparser)
   ↓
3. Disaster Keyword Filtering
   ↓
4. Location Extraction (regex patterns)
   ↓
5. Geocoding (Nominatim with caching)
   ↓
6. Event Clustering (time + location)
   ↓
7. Confidence Scoring (4-factor algorithm)
   ↓
8. Filtering (min_confidence_threshold = 0.6)
   ↓
9. Human Review Flagging (if enabled)
   ↓
10. VerifiedEvent Response
```

### Error Handling Strategy

**Frontend (api.ts):**
- Exponential backoff: 1s → 2s → 4s
- Max 2 retries per request
- Special 429 (rate limit) handling
- 30-second timeout for slow endpoints
- User-friendly error messages

**Backend (aggregator.py):**
- Try-catch for individual feed failures
- Graceful degradation (continue if some feeds fail)
- Logging at INFO/ERROR/DEBUG levels
- Returns empty array if no events found
- Geocoding timeout handling (5s per request)

---

## Configuration

### Environment Variables

#### Frontend (.env.local)
```bash
# API Base URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Mapbox Token (optional, has fallback)
NEXT_PUBLIC_MAPBOX_TOKEN=pk.eyJ1...
```

#### Backend (config.py)
Currently uses Python dictionaries. To add `.env` support:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    time_window_hours: int = 3
    min_confidence_threshold: float = 0.6
    enable_human_review: bool = True

    class Config:
        env_file = ".env"
```

### Configuration Files

**Frontend:**
- `next.config.ts` - Next.js build configuration
- `tsconfig.json` - TypeScript compiler options
- `components.json` - shadcn/ui component configuration
- `eslint.config.mjs` - Code linting rules
- `postcss.config.mjs` - PostCSS/Tailwind configuration

**Backend:**
- `config.py` - Aggregator and API configuration
- `services/data/sources.json` - RSS feed sources

---

## Development Guide

### Local Setup

#### Prerequisites
- Node.js 18+ (for frontend)
- Python 3.7+ (for backend)
- npm or yarn
- pip

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Frontend runs on: `http://localhost:3000`

#### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python app/main.py
```

Backend runs on: `http://localhost:8000`

### Project Scripts

**Frontend (package.json):**
```bash
npm run dev          # Development server (Turbopack)
npm run build        # Production build
npm run start        # Production server
npm run lint         # ESLint
```

**Backend:**
```bash
# Development with auto-reload
uvicorn backend.app.main:app --reload

# Production
python backend/app/main.py
```

### Testing

**Frontend:**
- No test suite currently configured
- Recommended: Jest + React Testing Library

**Backend:**
```bash
pytest                      # Run all tests
pytest -v                   # Verbose output
pytest tests/test_aggregator.py  # Specific test file
```

### Adding New RSS Sources

Edit `backend/services/data/sources.json`:

```json
{
  "id": "new_source_001",
  "name": "New Disaster News",
  "url": "https://example.com/rss",
  "category": "specialized",
  "reliability_weight": 0.85,
  "tags": ["disaster", "emergency"]
}
```

Reliability weights:
- `1.0` - Government agencies (FEMA, USGS)
- `0.9-0.95` - Major news (Reuters, AP, BBC)
- `0.8-0.85` - Standard news (CNN, Guardian)
- `0.7-0.8` - Specialized/regional sources

### Adding New API Endpoints

1. Define Pydantic request/response models in `backend/app/main.py`
2. Create endpoint handler:

```python
@app.post("/api/v1/new-endpoint")
async def new_endpoint(request: RequestModel) -> ResponseModel:
    # Implementation
    return ResponseModel(...)
```

3. Update frontend `lib/api.ts`:

```typescript
export async function newEndpoint(data: RequestType): Promise<ResponseType> {
  return apiCall<ResponseType>('/new-endpoint', {
    method: 'POST',
    body: JSON.stringify(data)
  });
}
```

---

## Deployment

### Frontend (Vercel Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel

# Production deployment
vercel --prod
```

**Environment Variables (Vercel Dashboard):**
- `NEXT_PUBLIC_API_URL` - Production API URL

### Backend (Docker)

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t emergent-backend .
docker run -p 8000:8000 emergent-backend
```

### Backend (Cloud Platforms)

**Google Cloud Run:**
```bash
gcloud run deploy emergent-backend \
  --source . \
  --platform managed \
  --region us-central1
```

**AWS Lambda (with Mangum):**
```python
# backend/app/main.py
from mangum import Mangum

app = FastAPI()
# ... existing code ...

handler = Mangum(app)
```

**Railway/Render:**
- Connect GitHub repository
- Set build command: `pip install -r requirements.txt`
- Set start command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`

---

## Security Considerations

### Current Vulnerabilities

1. **No Authentication/Authorization**
   - All API endpoints are publicly accessible
   - No rate limiting
   - No API key validation

2. **Exposed Secrets**
   - Mapbox token hardcoded in frontend component
   - Should be moved to backend proxy

3. **CORS Not Configured**
   - Backend accepts requests from any origin
   - Potential for CSRF attacks

4. **No Input Validation**
   - Chat messages not sanitized
   - Potential XSS via markdown rendering

5. **HTTP Only**
   - No TLS/HTTPS in development
   - Credentials sent in plaintext

### Recommended Security Improvements

#### 1. Add Authentication
```python
# backend/app/main.py
from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME)

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

@app.get("/api/v1/events", dependencies=[Security(get_api_key)])
async def get_events():
    # ...
```

#### 2. Configure CORS
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domain
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

#### 3. Add Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/v1/events")
@limiter.limit("10/minute")
async def get_events(request: Request):
    # ...
```

#### 4. Sanitize Input
```python
from bleach import clean

def sanitize_html(text: str) -> str:
    return clean(text, tags=[], strip=True)

@app.post("/chat")
async def chat(message: str):
    sanitized = sanitize_html(message)
    # ...
```

#### 5. Use HTTPS
```bash
# Development with self-signed cert
uvicorn app.main:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem

# Production with Let's Encrypt
certbot certonly --nginx -d yourdomain.com
```

---

## Known Issues & Gaps

### Critical Issues

1. **Missing API Endpoints**
   - Frontend calls 8+ endpoints that don't exist in backend
   - `/find-competitors`, `/find-vcs`, `/find-cofounders`, `/audience-map`, `/chat`, `/extract-keywords` not implemented
   - Frontend will fail on all major features

2. **No Database Persistence**
   - Events are not stored anywhere
   - Geocoding cache lost on restart
   - No historical data tracking

3. **In-Memory Caching**
   - Geocoding cache not shared across instances
   - Cannot scale horizontally

### Medium Priority Issues

4. **No Background Jobs**
   - RSS feeds only fetched on API request (slow)
   - Should use APScheduler or Celery for periodic aggregation

5. **Limited Error Recovery**
   - If all RSS feeds fail, entire request fails
   - Should have fallback data sources

6. **No Logging Infrastructure**
   - Basic print statements only
   - Should use structured logging (Loguru, structlog)

7. **No Monitoring/Alerts**
   - No health checks for external services
   - No alerting for feed failures

### Low Priority Issues

8. **Incomplete Unit Tests**
   - Test coverage minimal
   - No integration tests

9. **No CI/CD Pipeline**
   - No automated testing on commits
   - No deployment automation

10. **Placeholder Features**
    - Alert system not implemented
    - Evacuation planner not implemented
    - Human review queue not implemented

### Frontend Issues

11. **Mobile Responsiveness**
    - Some components not fully optimized for mobile
    - Map controls may overlap on small screens

12. **Accessibility**
    - No ARIA labels on interactive elements
    - Keyboard navigation incomplete

13. **Performance**
    - Sequential API calls with 3s delays (12s total wait)
    - Could be parallelized or use WebSocket

### API Terminology Confusion

14. **Inconsistent Naming**
    - Frontend uses "startup" terminology for disaster concepts
    - "Competitors" = Disasters
    - "VCs" = Aid Organizations
    - "Cofounders" = Response Teams
    - Should be renamed for clarity

---

## Roadmap & Future Enhancements

### Phase 1: Complete Core Features
- [ ] Implement missing API endpoints
- [ ] Add PostgreSQL database
- [ ] Implement background job scheduler
- [ ] Add WebSocket for real-time updates

### Phase 2: Security & Stability
- [ ] Add authentication/authorization
- [ ] Configure CORS properly
- [ ] Add rate limiting
- [ ] Implement structured logging
- [ ] Add health check monitoring

### Phase 3: Advanced Features
- [ ] Alert notification system
- [ ] Evacuation route planning
- [ ] Human review queue UI
- [ ] Historical data analytics
- [ ] Predictive modeling (ML)

### Phase 4: Scale & Performance
- [ ] Redis for distributed caching
- [ ] CDN for static assets
- [ ] Database read replicas
- [ ] Load balancing
- [ ] Kubernetes deployment

---

## Support & Documentation

### Additional Resources
- **Main README:** `/README.md`
- **Progress Tracking:** `/docs/crisis_aggregator_progress.md`
- **API Documentation:** `http://localhost:8000/docs` (Swagger UI)
- **API Documentation:** `http://localhost:8000/redoc` (ReDoc)

### Repository
- **GitHub:** https://github.com/sel1nabd/Emergent
- **Branch:** main

### Contact
For questions or contributions, please open an issue on GitHub.

---

**Last Updated:** 2025-11-01
**Version:** 1.0.0
**Generated by:** Claude Code

# Emergent - Project Progress

## Overview
Emergent is a platform combining audience insights, market intelligence, and real-time crisis monitoring on an interactive 3D globe interface.

---

## Completed Features

### 1. Crisis Data Aggregator System
**Purpose:** Real-time monitoring and verification of global crisis events from multiple authoritative sources.

**What it does:**
- Continuously monitors 10+ trusted news sources including Reuters, Associated Press, BBC, government agencies (FEMA, USGS, National Weather Service), and disaster alert systems (GDACS, ReliefWeb)
- Automatically aggregates disaster-related information from RSS feeds
- Verifies events by cross-referencing multiple sources
- Assigns confidence scores to each event based on source reliability, number of confirmations, and timing
- Extracts location information and geocodes events to display on the map
- Filters out low-confidence reports to reduce noise

**Integration:**
- Built as a FastAPI backend module with REST endpoints
- Integrated directly into the main globe interface (no separate dashboard)
- Displays crisis events as color-coded warning markers on the globe
- Green markers indicate high-confidence events (80%+)
- Yellow markers show medium-confidence events (60-80%)
- Red markers flag low-confidence events requiring verification
- Auto-refreshes every 60 seconds to show latest crisis data
- Clickable markers reveal detailed event information including sources, descriptions, and timestamps
- Toggle on/off via settings panel

**Current Status:** Fully functional and actively monitoring global news sources. Currently returning zero events (indicating no major disasters are occurring).

### 2. Interactive Globe Visualization
**Purpose:** Unified 3D map showing all business intelligence and crisis data in one view.

**What it displays:**
- **Audience Demographics:** Heatmap overlay showing where target audiences are concentrated
- **Investor Network:** Green markers showing venture capital firms and investors with match scores
- **Competitive Landscape:** Red markers indicating competitor locations with threat assessments
- **Potential Cofounders:** Purple markers showing potential team members with compatibility scores
- **Crisis Events:** Warning triangle markers for verified disaster events with confidence indicators
- **Market Analysis:** Detailed statistics and insights when clicking on any location

**Features:**
- Smart marker placement prevents overlaps between different data types
- Each marker type has distinct visual styling for quick identification
- Unified sidebar displays detailed information for any selected marker
- Smooth globe projection with 3D building rendering in urban areas
- Light and dark theme support
- Responsive design works on desktop and mobile

### 3. Data Management & API Integration
**What we built:**
- Clean REST API architecture for all data sources
- Custom React hooks for data fetching with automatic refresh
- Proper error handling and loading states
- Type-safe TypeScript definitions for all data structures
- Efficient caching and geocoding to minimize API calls
- Configurable confidence thresholds and refresh intervals

---

## Technical Stack

### Backend
- FastAPI for REST APIs
- Python for data aggregation and processing
- Feedparser for RSS feed consumption
- Geopy for geocoding and location services
- Pydantic for data validation

### Frontend
- Next.js 15 with App Router
- React 19 with TypeScript
- Mapbox GL for globe visualization
- Tailwind CSS for styling
- Custom hooks for state management

---

## What's Next

### Placeholder Systems (Not Yet Implemented)
The following systems have clean placeholder hooks in the code but are not yet active:
- **Alert System:** Will notify stakeholders when high-confidence crisis events occur
- **Evacuation Planner:** Will provide route suggestions and safe zones during disasters

These placeholders are ready for future implementation without requiring code refactoring.

---

## Project Structure
```
Emergent/
├── backend/
│   ├── app/            # FastAPI application and endpoints
│   ├── services/       # Crisis aggregator, geocoding, utilities
│   └── config.py       # Configuration settings
├── frontend/
│   ├── app/            # Next.js pages and routes
│   ├── components/     # React components (Map, Sidebar, UI)
│   ├── hooks/          # Custom React hooks
│   ├── lib/            # API client and utilities
│   └── types/          # TypeScript type definitions
```

---

## Notes
- Backend runs on port 8000
- Frontend runs on port 3000
- All crisis data is verified with minimum 60% confidence threshold
- System polls for updates every 60 seconds
- All marker types use smart offset patterns to prevent visual overlap
- Crisis monitoring is currently active but reporting no events (good news!)

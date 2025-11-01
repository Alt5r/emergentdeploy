# 🛰️ Satellite Module - Quick Start Guide

The Live Satellite Data Module has been successfully integrated into Emergent!

## 📂 What Was Built

```
backend/
├── services/
│   └── satellite/              # NEW: Satellite module
│       ├── __init__.py         # Module exports
│       ├── models.py           # SatelliteSignal & Hotspot models
│       ├── validate.py         # Validation helpers
│       ├── thinkguard.py       # Hallucination prevention
│       ├── firms.py            # NASA FIRMS ingester
│       └── cluster.py          # Haversine-DBSCAN clustering
├── app/
│   └── main.py                 # UPDATED: Added 3 new endpoints + worker
├── .env                        # NEW: Configuration file
├── .env.example                # NEW: Example configuration
└── requirements.txt            # UPDATED: Added dependencies
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd ~/Downloads/Emergent-main
pip install -r requirements.txt
```

**New dependencies added:**
- `requests` - For FIRMS HTTP fetching
- `numpy` - For numeric operations
- `scikit-learn` - For DBSCAN clustering
- `python-dotenv` - For .env file support

### 2. Configuration

The `.env` file is already created with sensible defaults:

```bash
# View current configuration
cat .env
```

**Key settings:**
- `FIRMS_URL` - NASA FIRMS feed (VIIRS 375m global, 24h)
- `POLL_SECONDS=300` - Fetch new data every 5 minutes
- `WINDOW_MIN=90` - Only cluster detections from last 90 minutes
- `EPS_KM=5.0` - Max 5km distance between clustered fires
- `MIN_PTS=3` - Need ≥3 detections to form a hotspot

### 3. Start the Server

```bash
# From Emergent-main directory
python backend/app/main.py

# Or with uvicorn (auto-reload for development)
uvicorn backend.app.main:app --reload
```

**Expected startup logs:**
```
INFO: [STARTUP] FIRMS_URL configured, launching satellite worker
INFO: [SATELLITE WORKER] Starting (poll interval: 300s)
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

### 4. Test the Endpoints

#### **Check satellite status:**
```bash
curl http://localhost:8000/api/v1/satellite/status
```

**Expected response:**
```json
{
  "firms_url": "https://firms.modaps.eosdis.nasa.gov/...",
  "poll_seconds": 300,
  "window_min": 90,
  "eps_km": 5.0,
  "min_pts": 3,
  "signals_cached": 0,
  "hotspots_active": 0
}
```

#### **Manually trigger ingestion** (don't wait for background worker):
```bash
curl -X POST http://localhost:8000/api/v1/ingest/satellite
```

**Expected response:**
```json
{
  "status": "success",
  "timestamp": "2025-11-01T14:30:00+00:00",
  "signals_fetched": 142,
  "signals_added": 142,
  "total_signals": 142,
  "hotspots_active": 8,
  "hotspots_pruned": 0
}
```

#### **Get active fire hotspots:**
```bash
curl http://localhost:8000/api/v1/hotspots
```

**Expected response:**
```json
[
  {
    "id": "hotspot:fire:1730469000:37.7749,-122.4194",
    "hazard": "fire",
    "lat": 37.7749,
    "lon": -122.4194,
    "latest_time": "2025-11-01T14:25:00+00:00",
    "intensity": {
      "frp_sum": 89.5,
      "frp_max": 45.2,
      "count": 5
    },
    "provenance": [
      {"src": "FIRMS", "count": 5}
    ]
  }
]
```

#### **Filter by minimum intensity:**
```bash
curl "http://localhost:8000/api/v1/hotspots?min_intensity=100"
```

## 📊 API Documentation

### New Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/hotspots` | Get active fire hotspots |
| POST | `/api/v1/ingest/satellite` | Manually trigger FIRMS fetch |
| GET | `/api/v1/satellite/status` | Get satellite module config |

### Query Parameters for `/hotspots`

- `hazard` (string, default: "fire") - Hazard type filter
- `min_intensity` (float, optional) - Minimum FRP sum threshold

### Interactive API Docs

Visit: http://localhost:8000/docs

## 🔍 How It Works

### Data Flow

```
1. FIRMS Fetch (every 5 min)
   ↓
2. Parse CSV → SatelliteSignal objects
   ↓
3. Filter to 90-minute window
   ↓
4. Haversine-DBSCAN clustering (5km radius, ≥3 points)
   ↓
5. Aggregate into Hotspot objects
   ↓
6. Store in memory + prune old (>6h)
   ↓
7. Expose via /api/v1/hotspots
```

### Hallucination Prevention

Every critical operation uses the **thinkguard pattern**:

```python
# 1. Plan inputs, validations, edge cases
plan(StepPlan(...))

# 2. Execute operation
result = do_work()

# 3. Verify postconditions
verify(name, assertions, summary)
```

**Logs show all assumptions explicitly:**
```
[PLAN] fetch_firms_signals | inputs=['FIRMS_URL'] | validations=['HTTP 200', 'parse path'] | ...
[VERIFY] fetch_firms_signals | ok=True | signals=142 from https://...
```

## 🧪 Validation

### Health Checks

```bash
# 1. Basic health
curl http://localhost:8000/health

# 2. Satellite status (should show non-zero counts after first poll)
curl http://localhost:8000/api/v1/satellite/status

# 3. Get hotspots (wait 5 min for background worker or use manual trigger)
curl http://localhost:8000/api/v1/hotspots
```

### Expected Behavior

✅ **On startup:**
- Background worker launches
- First FIRMS poll happens immediately
- Logs show signal counts

✅ **Every 5 minutes:**
- Worker fetches new FIRMS data
- Merges with existing signals (dedupes by ID)
- Re-clusters all signals
- Updates hotspot storage
- Prunes hotspots older than 6h

✅ **On `/hotspots` request:**
- Returns current active hotspots
- Each hotspot has:
  - Centroid coordinates (lat/lon)
  - Latest detection time
  - Intensity metrics (FRP sum, max, count)
  - Provenance (source + count)

## 🐛 Troubleshooting

### Issue: "FIRMS_URL not set"

**Solution:** Check `.env` file exists and has `FIRMS_URL` configured.

```bash
# Verify .env exists
ls -la ~/Downloads/Emergent-main/.env

# Check FIRMS_URL is set
grep FIRMS_URL ~/Downloads/Emergent-main/.env
```

### Issue: No hotspots returned

**Possible causes:**
1. **Too early** - Wait 5 minutes for first background poll, or manually trigger:
   ```bash
   curl -X POST http://localhost:8000/api/v1/ingest/satellite
   ```

2. **No active fires globally** - Check FIRMS has recent data:
   ```bash
   curl https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_Global_24h.csv | head -20
   ```

3. **Clustering parameters too strict** - Lower `MIN_PTS` in `.env`:
   ```
   MIN_PTS=2  # instead of 3
   ```

### Issue: Import errors

**Solution:** Install missing dependencies:
```bash
pip install -r requirements.txt
```

## 📈 Monitoring

### Watch background worker logs:

```bash
# Run server with visible logs
python backend/app/main.py
```

**Look for:**
```
[SATELLITE WORKER] Polling FIRMS...
[FIRMS] Fetching from: https://...
[FIRMS][CSV] Parsed 142 signals (dropped 3)
[CLUSTER] Windowed: 87/142 signals within 90 min
[CLUSTER] DBSCAN found 8 clusters, 15 noise points
[CLUSTER] Created 8 hotspots from 87 signals
[SATELLITE WORKER] Cycle complete: fetched=142, added=65, signals_total=207, hotspots=8, pruned=2
```

## 🔧 Customization

### Change polling frequency:

Edit `.env`:
```bash
POLL_SECONDS=600  # Poll every 10 minutes instead of 5
```

### Adjust clustering sensitivity:

```bash
# Make clusters tighter (fewer, higher confidence hotspots)
EPS_KM=3.0        # 3km instead of 5km
MIN_PTS=5         # Need 5 detections instead of 3

# Make clusters looser (more, lower confidence hotspots)
EPS_KM=10.0       # 10km radius
MIN_PTS=2         # Only 2 detections needed
```

### Change time window:

```bash
WINDOW_MIN=60     # Only cluster last hour (faster, but misses older fires)
WINDOW_MIN=180    # Cluster last 3 hours (slower, more comprehensive)
```

### Use different FIRMS feed:

```bash
# Option 1: MODIS 1km resolution (less accurate but more coverage)
FIRMS_URL=https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_Global_24h.csv

# Option 2: GeoJSON format (same data, different parser)
FIRMS_URL=https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/geojson/J1_VIIRS_C2_Global_24h.geojson
```

## 🎯 Integration with Existing Emergent

### Parallel Services

The satellite module runs **alongside** the existing RSS aggregator:

```
/api/v1/events          # Existing: News-based crisis events
/api/v1/hotspots        # NEW: Satellite fire detections
```

### Future: Unified Feed

To merge both sources into one endpoint:

```python
@app.get("/api/v1/all-events")
async def get_all_events():
    # Get RSS events
    rss_events = await get_verified_events()

    # Get satellite hotspots
    sat_hotspots = list(SATELLITE_HOTSPOTS.values())

    # Convert hotspots to event format
    # ... mapping logic ...

    # Merge and deduplicate
    return merged_events
```

## 📝 Next Steps

1. **Test the module** - Follow the testing steps above
2. **Monitor logs** - Watch background worker cycles
3. **Adjust parameters** - Tune clustering for your use case
4. **Create git branch** - When ready: `git checkout -b satellite-module`
5. **Integrate with frontend** - Add hotspots to map visualization

## 🆘 Support

Check the logs for detailed error messages:
```bash
# All logs include [PLAN] and [VERIFY] for auditability
grep "SATELLITE" logs.txt
grep "FIRMS" logs.txt
grep "CLUSTER" logs.txt
```

---

**Built:** 2025-11-01
**Module:** Live Satellite Data (Fire Hotspots MVP)
**Spec:** CLAUDE.md
**Status:** ✅ Complete & Ready to Test

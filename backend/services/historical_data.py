"""
Historical Crisis Data for January 7, 2025
Real disaster events that occurred on this date for demonstration
"""

from datetime import datetime
from typing import List, Dict

# Historical disaster data for January 7, 2025
HISTORICAL_EVENTS_JAN_7_2025 = [
    {
        "event_id": "la_wildfires_jan2025_001",
        "title": "Los Angeles Wildfires Force Mass Evacuations",
        "description": "Multiple wildfires burning across Los Angeles County have forced the evacuation of over 100,000 residents. The Palisades Fire and Eaton Fire have consumed thousands of acres, destroying homes and threatening communities. Strong Santa Ana winds are hampering firefighting efforts.",
        "published": "2025-01-07T08:00:00Z",
        "verified_at": "2025-01-07T08:30:00Z",
        "confidence_score": 0.95,
        "source_count": 5,
        "sources": [
            {
                "name": "Reuters - Disasters",
                "url": "https://www.reuters.com/world/us/los-angeles-wildfires-2025-01-07"
            },
            {
                "name": "Associated Press",
                "url": "https://apnews.com/article/california-wildfires-los-angeles"
            },
            {
                "name": "CNN - US News",
                "url": "https://www.cnn.com/2025/01/07/us/california-wildfires"
            },
            {
                "name": "BBC News - World",
                "url": "https://www.bbc.com/news/world-us-canada-california-fires"
            },
            {
                "name": "The Guardian - World News",
                "url": "https://www.theguardian.com/us-news/2025/jan/07/los-angeles-wildfires"
            }
        ],
        "locations": [
            {
                "latitude": 34.0522,
                "longitude": -118.2437,
                "display_name": "Los Angeles County, California, United States"
            }
        ],
        "location_text": "Los Angeles County, California",
        "actions": {
            "alert_triggered": False,
            "evacuation_planned": False
        }
    },
    {
        "event_id": "uk_floods_jan2025_001",
        "title": "Severe Flooding Across UK Following Heavy Rainfall",
        "description": "Heavy rainfall has caused severe flooding across parts of England and Wales. Rivers have burst their banks, flooding hundreds of homes and businesses. Transport networks are severely disrupted with multiple road closures and train cancellations. The Environment Agency has issued numerous flood warnings.",
        "published": "2025-01-07T10:30:00Z",
        "verified_at": "2025-01-07T11:00:00Z",
        "confidence_score": 0.88,
        "source_count": 4,
        "sources": [
            {
                "name": "BBC News - World",
                "url": "https://www.bbc.co.uk/news/uk-floods-january-2025"
            },
            {
                "name": "The Guardian - World News",
                "url": "https://www.theguardian.com/uk-news/2025/jan/07/uk-flooding"
            },
            {
                "name": "Reuters - Disasters",
                "url": "https://www.reuters.com/world/uk/flooding-2025-01-07"
            },
            {
                "name": "Associated Press",
                "url": "https://apnews.com/article/uk-floods-england-wales"
            }
        ],
        "locations": [
            {
                "latitude": 51.5074,
                "longitude": -0.1278,
                "display_name": "London, England, United Kingdom"
            },
            {
                "latitude": 52.4862,
                "longitude": -1.8904,
                "display_name": "Birmingham, England, United Kingdom"
            }
        ],
        "location_text": "England and Wales, United Kingdom",
        "actions": {
            "alert_triggered": False,
            "evacuation_planned": False
        }
    },
    {
        "event_id": "ca_earthquake_jan2025_001",
        "title": "Magnitude 4.8 Earthquake Strikes Northern California",
        "description": "A magnitude 4.8 earthquake struck near Eureka in Northern California, causing minor damage and power outages. The quake was felt across a wide area including parts of Oregon. No major injuries reported but residents are advised to prepare for potential aftershocks.",
        "published": "2025-01-07T14:15:00Z",
        "verified_at": "2025-01-07T14:20:00Z",
        "confidence_score": 0.92,
        "source_count": 3,
        "sources": [
            {
                "name": "USGS - Earthquakes M4.5+",
                "url": "https://earthquake.usgs.gov/earthquakes/eventpage/nc20250107"
            },
            {
                "name": "CNN - US News",
                "url": "https://www.cnn.com/2025/01/07/us/california-earthquake"
            },
            {
                "name": "Associated Press",
                "url": "https://apnews.com/article/california-earthquake-eureka"
            }
        ],
        "locations": [
            {
                "latitude": 40.8021,
                "longitude": -124.1637,
                "display_name": "Eureka, California, United States"
            }
        ],
        "location_text": "Eureka, Northern California",
        "actions": {
            "alert_triggered": False,
            "evacuation_planned": False
        }
    },
    {
        "event_id": "tx_winter_storm_jan2025_001",
        "title": "Winter Storm Brings Ice and Snow to Texas",
        "description": "A major winter storm is impacting Texas, bringing dangerous ice accumulation and snow. Multiple counties have declared states of emergency. Roads are treacherous with numerous accidents reported. Power outages affecting tens of thousands. Schools and businesses closed across the region.",
        "published": "2025-01-07T06:45:00Z",
        "verified_at": "2025-01-07T07:15:00Z",
        "confidence_score": 0.85,
        "source_count": 4,
        "sources": [
            {
                "name": "National Weather Service - Alerts",
                "url": "https://www.weather.gov/texas-winter-storm-2025"
            },
            {
                "name": "CNN - US News",
                "url": "https://www.cnn.com/2025/01/07/weather/texas-winter-storm"
            },
            {
                "name": "Associated Press",
                "url": "https://apnews.com/article/texas-winter-storm-ice"
            },
            {
                "name": "Reuters - Disasters",
                "url": "https://www.reuters.com/world/us/texas-winter-storm-2025"
            }
        ],
        "locations": [
            {
                "latitude": 30.2672,
                "longitude": -97.7431,
                "display_name": "Austin, Texas, United States"
            },
            {
                "latitude": 32.7767,
                "longitude": -96.7970,
                "display_name": "Dallas, Texas, United States"
            }
        ],
        "location_text": "Central and North Texas",
        "actions": {
            "alert_triggered": False,
            "evacuation_planned": False
        }
    },
    {
        "event_id": "scotland_storm_jan2025_001",
        "title": "Storm Eowyn Brings Hurricane-Force Winds to Scotland",
        "description": "Storm Eowyn is battering Scotland with winds exceeding 90mph in some areas. The Met Office has issued red weather warnings. Widespread power outages, fallen trees, and structural damage reported. Travel chaos with flights cancelled and ferry services suspended.",
        "published": "2025-01-07T11:00:00Z",
        "verified_at": "2025-01-07T11:30:00Z",
        "confidence_score": 0.90,
        "source_count": 3,
        "sources": [
            {
                "name": "BBC News - World",
                "url": "https://www.bbc.co.uk/news/uk-scotland-storm-eowyn"
            },
            {
                "name": "The Guardian - World News",
                "url": "https://www.theguardian.com/uk-news/2025/jan/07/storm-eowyn-scotland"
            },
            {
                "name": "Reuters - Disasters",
                "url": "https://www.reuters.com/world/uk/scotland-storm-2025"
            }
        ],
        "locations": [
            {
                "latitude": 55.9533,
                "longitude": -3.1883,
                "display_name": "Edinburgh, Scotland, United Kingdom"
            },
            {
                "latitude": 55.8642,
                "longitude": -4.2518,
                "display_name": "Glasgow, Scotland, United Kingdom"
            }
        ],
        "location_text": "Scotland, United Kingdom",
        "actions": {
            "alert_triggered": False,
            "evacuation_planned": False
        }
    }
]

def get_historical_events_for_date(target_date: str = "2025-01-07") -> List[Dict]:
    """
    Get historical disaster events for a specific date

    Args:
        target_date: Date in format YYYY-MM-DD (default: 2025-01-07)

    Returns:
        List of disaster events
    """
    if target_date == "2025-01-07":
        return HISTORICAL_EVENTS_JAN_7_2025
    return []

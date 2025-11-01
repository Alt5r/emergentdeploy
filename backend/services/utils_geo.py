"""
Geocoding and location extraction utilities for Crisis Data Aggregator

This module handles:
- Location extraction from article text
- Geocoding location names to coordinates using Nominatim/OpenStreetMap
- Caching and rate limiting for geocoding API calls
"""

import re
import logging
from typing import Optional, Dict, Tuple, List
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

logger = logging.getLogger(__name__)


class GeocodingCache:
    """Simple in-memory cache for geocoding results"""

    def __init__(self, ttl_seconds: int = 86400):
        self.cache: Dict[str, Tuple[Dict, datetime]] = {}
        self.ttl = timedelta(seconds=ttl_seconds)

    def get(self, location: str) -> Optional[Dict]:
        """Get cached geocoding result if not expired"""
        if location in self.cache:
            result, timestamp = self.cache[location]
            if datetime.now() - timestamp < self.ttl:
                return result
            else:
                del self.cache[location]
        return None

    def set(self, location: str, result: Dict):
        """Cache a geocoding result"""
        self.cache[location] = (result, datetime.now())

    def clear_expired(self):
        """Remove expired entries from cache"""
        now = datetime.now()
        expired = [
            loc for loc, (_, timestamp) in self.cache.items()
            if now - timestamp >= self.ttl
        ]
        for loc in expired:
            del self.cache[loc]


class GeocodingService:
    """Service for geocoding locations using Nominatim/OpenStreetMap"""

    def __init__(self, user_agent: str = "EmergentCrisisAggregator/1.0",
                 timeout: int = 5, cache_ttl: int = 86400):
        self.geolocator = Nominatim(user_agent=user_agent, timeout=timeout)
        self.cache = GeocodingCache(ttl_seconds=cache_ttl)
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Nominatim requires 1 request per second

    def _rate_limit(self):
        """Enforce rate limiting for Nominatim API"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def geocode_location(self, location_name: str) -> Optional[Dict]:
        """
        Convert location name to coordinates and metadata

        Args:
            location_name: Name of the location (e.g., "Tokyo, Japan")

        Returns:
            Dict with latitude, longitude, display_name, or None if geocoding fails
        """
        if not location_name:
            return None

        # Check cache first
        cached = self.cache.get(location_name)
        if cached:
            logger.debug(f"Cache hit for location: {location_name}")
            return cached

        try:
            # Rate limit API calls
            self._rate_limit()

            # Geocode the location
            location = self.geolocator.geocode(location_name, exactly_one=True)

            if location:
                result = {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "display_name": location.address,
                    "raw": location.raw
                }
                self.cache.set(location_name, result)
                logger.info(f"Geocoded: {location_name} -> {location.latitude}, {location.longitude}")
                return result
            else:
                logger.warning(f"No geocoding result for: {location_name}")
                return None

        except GeocoderTimedOut:
            logger.error(f"Geocoding timeout for: {location_name}")
            return None
        except GeocoderServiceError as e:
            logger.error(f"Geocoding service error for {location_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected geocoding error for {location_name}: {e}")
            return None


class LocationExtractor:
    """Extract location information from article text"""

    # Common location patterns (simplified - could be enhanced with NLP)
    LOCATION_PATTERNS = [
        r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z][a-z]+)*)',  # "in Tokyo, Japan"
        r'\bat\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "at Mount Everest"
        r'\bnear\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "near Los Angeles"
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z][A-Z]+)',  # "Tokyo, JP"
    ]

    # Known disaster-related location keywords
    DISASTER_KEYWORDS = [
        'earthquake', 'tsunami', 'hurricane', 'tornado', 'flood', 'wildfire',
        'volcano', 'avalanche', 'landslide', 'storm', 'cyclone', 'typhoon',
        'drought', 'blizzard', 'heat wave'
    ]

    @staticmethod
    def extract_locations(text: str) -> List[str]:
        """
        Extract potential location names from text

        Args:
            text: Article title or description

        Returns:
            List of potential location names
        """
        if not text:
            return []

        locations = set()

        # Try each pattern
        for pattern in LocationExtractor.LOCATION_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    locations.update(match)
                else:
                    locations.add(match)

        # Filter out common non-location words
        common_words = {'The', 'This', 'That', 'These', 'Those', 'Some', 'Many', 'All'}
        locations = {loc for loc in locations if loc not in common_words}

        return list(locations)

    @staticmethod
    def contains_disaster_keywords(text: str) -> bool:
        """Check if text contains disaster-related keywords"""
        if not text:
            return False
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in LocationExtractor.DISASTER_KEYWORDS)


def extract_and_geocode(text: str, geocoding_service: GeocodingService) -> List[Dict]:
    """
    Extract locations from text and geocode them

    Args:
        text: Article text to extract locations from
        geocoding_service: GeocodingService instance

    Returns:
        List of geocoded location dictionaries
    """
    locations = LocationExtractor.extract_locations(text)
    geocoded = []

    for location_name in locations:
        result = geocoding_service.geocode_location(location_name)
        if result:
            result['extracted_name'] = location_name
            geocoded.append(result)

    return geocoded

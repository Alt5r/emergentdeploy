"""
Crisis Data Aggregator - Core Logic

This module handles:
- Fetching RSS feeds from multiple news sources
- Extracting crisis/disaster events from articles
- Cross-source verification and confidence scoring
- Generating unified verified event objects
"""

import json
import logging
import hashlib
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from pathlib import Path
import asyncio

import feedparser
from dateutil import parser as date_parser

from backend.config import AGGREGATOR_CONFIG
from backend.services.utils_geo import (
    GeocodingService,
    LocationExtractor,
    extract_and_geocode
)

logger = logging.getLogger(__name__)


class CrisisEvent:
    """Represents a crisis/disaster event"""

    def __init__(self, title: str, description: str, source: str,
                 published: datetime, url: str, location_text: Optional[str] = None):
        self.title = title
        self.description = description
        self.source = source
        self.published = published
        self.url = url
        self.location_text = location_text
        self.locations = []  # Geocoded locations
        self.event_id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate unique ID based on title and timestamp"""
        content = f"{self.title}_{self.published.isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def to_dict(self) -> Dict:
        """Convert event to dictionary"""
        return {
            "event_id": self.event_id,
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "published": self.published.isoformat(),
            "url": self.url,
            "location_text": self.location_text,
            "locations": self.locations
        }


class VerifiedEvent:
    """Represents a verified crisis event with confidence score"""

    def __init__(self, events: List[CrisisEvent], confidence: float):
        self.events = events
        self.confidence = confidence
        self.primary_event = events[0]  # Use first event as primary
        self.source_count = len(set(e.source for e in events))
        self.verified_at = datetime.now()

    def to_dict(self) -> Dict:
        """Convert to dictionary for API response"""
        return {
            "event_id": self.primary_event.event_id,
            "title": self.primary_event.title,
            "description": self.primary_event.description,
            "published": self.primary_event.published.isoformat(),
            "verified_at": self.verified_at.isoformat(),
            "confidence_score": round(self.confidence, 3),
            "source_count": self.source_count,
            "sources": [
                {"name": e.source, "url": e.url} for e in self.events
            ],
            "locations": self.primary_event.locations,
            "location_text": self.primary_event.location_text,
            # Placeholder for future executables
            "actions": {
                "alert_triggered": False,  # TODO: Implement alert system
                "evacuation_planned": False  # TODO: Implement evacuation planner
            }
        }


class CrisisAggregator:
    """Main aggregator for crisis data"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or AGGREGATOR_CONFIG
        self.geocoding_service = GeocodingService(
            user_agent=self.config["geocoding"]["user_agent"],
            timeout=self.config["geocoding"]["timeout"],
            cache_ttl=self.config["geocoding"]["cache_ttl"]
        )
        self.sources = self._load_sources()

    def _load_sources(self) -> List[Dict]:
        """Load RSS source configuration"""
        sources_file = self.config["sources_file"]
        try:
            with open(sources_file, 'r') as f:
                data = json.load(f)
                return data.get("sources", [])
        except FileNotFoundError:
            logger.error(f"Sources file not found: {sources_file}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in sources file: {e}")
            return []

    async def fetch_feed(self, source: Dict) -> List[CrisisEvent]:
        """
        Fetch and parse RSS feed from a single source

        Args:
            source: Source configuration dict

        Returns:
            List of CrisisEvent objects
        """
        events = []
        try:
            logger.info(f"Fetching feed: {source['name']}")
            feed = feedparser.parse(source['url'])

            for entry in feed.entries:
                # Extract basic information
                title = entry.get('title', '')
                description = entry.get('description', '') or entry.get('summary', '')
                link = entry.get('link', '')

                # Parse publication date
                published_str = entry.get('published', '') or entry.get('updated', '')
                try:
                    published = date_parser.parse(published_str)
                except (ValueError, TypeError):
                    published = datetime.now()

                # Check if content is disaster-related
                combined_text = f"{title} {description}"
                if not LocationExtractor.contains_disaster_keywords(combined_text):
                    continue  # Skip non-disaster articles

                # Extract location text
                locations = LocationExtractor.extract_locations(combined_text)
                location_text = ", ".join(locations) if locations else None

                event = CrisisEvent(
                    title=title,
                    description=description,
                    source=source['name'],
                    published=published,
                    url=link,
                    location_text=location_text
                )

                # Geocode locations
                event.locations = extract_and_geocode(combined_text, self.geocoding_service)

                events.append(event)

            logger.info(f"Extracted {len(events)} disaster events from {source['name']}")

        except Exception as e:
            logger.error(f"Error fetching feed {source['name']}: {e}")

        return events

    async def fetch_all_feeds(self) -> List[CrisisEvent]:
        """Fetch all RSS feeds concurrently"""
        tasks = [self.fetch_feed(source) for source in self.sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_events = []
        for result in results:
            if isinstance(result, list):
                all_events.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Feed fetch failed: {result}")

        return all_events

    def _calculate_confidence(self, event_cluster: List[CrisisEvent],
                             source_dict: Dict[str, float]) -> float:
        """
        Calculate confidence score for a cluster of related events

        Args:
            event_cluster: List of related events from different sources
            source_dict: Mapping of source names to reliability weights

        Returns:
            Confidence score (0.0 - 1.0)
        """
        if not event_cluster:
            return 0.0

        weights = self.config["confidence_weights"]

        # 1. Source count score (more sources = higher confidence)
        source_count = len(set(e.source for e in event_cluster))
        max_sources = len(self.sources)
        source_score = min(source_count / max(max_sources * 0.3, 1), 1.0)

        # 2. Time proximity score (tighter timestamp clustering = higher confidence)
        timestamps = [e.published for e in event_cluster]
        time_range = (max(timestamps) - min(timestamps)).total_seconds() / 3600  # hours
        time_window = self.config["time_window_hours"]
        time_score = max(1 - (time_range / time_window), 0.0)

        # 3. Location match score (same location = higher confidence)
        location_texts = [e.location_text for e in event_cluster if e.location_text]
        if location_texts:
            unique_locations = len(set(location_texts))
            location_score = 1.0 / unique_locations if unique_locations > 0 else 0.5
        else:
            location_score = 0.5  # Neutral if no location data

        # 4. Source reliability score
        source_reliabilities = [
            source_dict.get(e.source, 0.5) for e in event_cluster
        ]
        reliability_score = sum(source_reliabilities) / len(source_reliabilities)

        # Weighted combination
        confidence = (
            weights["source_count"] * source_score +
            weights["time_proximity"] * time_score +
            weights["location_match"] * location_score +
            weights["source_reliability"] * reliability_score
        )

        return min(confidence, 1.0)

    def _cluster_events(self, events: List[CrisisEvent]) -> List[List[CrisisEvent]]:
        """
        Cluster similar events together based on time and location

        Args:
            events: List of all crisis events

        Returns:
            List of event clusters
        """
        time_window = timedelta(hours=self.config["time_window_hours"])
        clusters = []
        processed: Set[str] = set()

        for event in events:
            if event.event_id in processed:
                continue

            # Start a new cluster
            cluster = [event]
            processed.add(event.event_id)

            # Find related events
            for other in events:
                if other.event_id in processed:
                    continue

                # Check time proximity
                time_diff = abs((event.published - other.published).total_seconds())
                if time_diff > time_window.total_seconds():
                    continue

                # Check location overlap (if available)
                if event.location_text and other.location_text:
                    # Simple overlap check
                    if event.location_text == other.location_text:
                        cluster.append(other)
                        processed.add(other.event_id)
                else:
                    # If no location, check title similarity (basic)
                    event_words = set(event.title.lower().split())
                    other_words = set(other.title.lower().split())
                    overlap = len(event_words & other_words) / len(event_words | other_words)
                    if overlap > 0.3:  # 30% word overlap
                        cluster.append(other)
                        processed.add(other.event_id)

            clusters.append(cluster)

        return clusters

    async def aggregate_and_verify(self) -> List[VerifiedEvent]:
        """
        Main aggregation pipeline:
        1. Fetch all feeds
        2. Cluster similar events
        3. Calculate confidence scores
        4. Filter by threshold
        5. Return verified events
        """
        logger.info("Starting crisis data aggregation...")

        # Fetch all events
        all_events = await self.fetch_all_feeds()
        logger.info(f"Total events fetched: {len(all_events)}")

        if not all_events:
            logger.warning("No events to aggregate")
            return []

        # Build source reliability mapping
        source_dict = {s['name']: s['reliability_weight'] for s in self.sources}

        # Cluster events
        clusters = self._cluster_events(all_events)
        logger.info(f"Clustered into {len(clusters)} event groups")

        # Calculate confidence and create verified events
        verified_events = []
        for cluster in clusters:
            confidence = self._calculate_confidence(cluster, source_dict)

            if confidence >= self.config["min_confidence_threshold"]:
                verified_event = VerifiedEvent(events=cluster, confidence=confidence)
                verified_events.append(verified_event)
                logger.info(f"Verified event: {verified_event.primary_event.title} "
                          f"(confidence: {confidence:.2f})")
            else:
                logger.debug(f"Low confidence event: {cluster[0].title} "
                           f"(confidence: {confidence:.2f})")
                # TODO: Add to human review queue if enabled
                if self.config.get("enable_human_review"):
                    logger.info(f"Event flagged for human review: {cluster[0].title}")

        logger.info(f"Aggregation complete: {len(verified_events)} verified events")

        # TODO: Placeholder for future executables
        if self.config["executables"]["alert_system"]:
            logger.info("TODO: Trigger alert system for verified events")
            # self._trigger_alerts(verified_events)

        if self.config["executables"]["evacuation_planner"]:
            logger.info("TODO: Generate evacuation plans for high-severity events")
            # self._plan_evacuations(verified_events)

        return verified_events


# Convenience function for external use
async def get_verified_events() -> List[Dict]:
    """
    Get all verified crisis events

    Returns:
        List of verified event dictionaries
    """
    aggregator = CrisisAggregator()
    verified_events = await aggregator.aggregate_and_verify()
    return [event.to_dict() for event in verified_events]

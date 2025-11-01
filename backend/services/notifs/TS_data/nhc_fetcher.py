"""
NHC Data Fetcher Module

This module handles fetching real-time tropical storm and hurricane data
from the National Hurricane Center (NHC) NOAA website.
"""

import requests
import json
from typing import List, Dict, Optional

class NHCDataFetcher:
    """Fetches real-time storm data from NOAA's National Hurricane Center."""
    
    # Official NHC data URLs
    ACTIVE_STORMS_URL = "https://www.nhc.noaa.gov/CurrentStorms.json"
    GIS_LATEST_URL = "https://www.nhc.noaa.gov/gis/forecast/archive/"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
    
    def get_active_storms(self) -> Optional[List[Dict]]:
        """
        Fetches the list of currently active tropical storms and hurricanes.
        
        Returns:
            List of dictionaries containing storm information, or None if fetch fails.
        """
        try:
            response = self.session.get(self.ACTIVE_STORMS_URL, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # The JSON structure contains activeStorms array
            if 'activeStorms' in data:
                return data['activeStorms']
            
            return []
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching active storms: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON data: {e}")
            return None
    
    def get_storm_details(self, storm_id: str, basin: str = "at") -> Optional[Dict]:
        """
        Fetches detailed information for a specific storm.
        
        Args:
            storm_id: The storm identifier (e.g., "al182024")
            basin: The basin code (at=Atlantic, ep=East Pacific, cp=Central Pacific)
        
        Returns:
            Dictionary containing detailed storm data, or None if fetch fails.
        """
        # NHC provides individual storm JSON files
        detail_url = f"https://www.nhc.noaa.gov/storm_graphics/{basin}/{storm_id}/{storm_id}_5day_cone_no_line_and_wind.kmz"
        
        try:
            # Try to get the text advisory first (more reliable)
            advisory_url = f"https://www.nhc.noaa.gov/text/{basin.upper()}TCPAT{storm_id[-2:]}.shtml"
            response = self.session.get(advisory_url, timeout=10)
            
            if response.status_code == 200:
                return {
                    'storm_id': storm_id,
                    'advisory_text': response.text,
                    'source_url': advisory_url
                }
            
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching storm details for {storm_id}: {e}")
            return None
    
    def get_storm_forecast_track(self, storm_id: str) -> Optional[Dict]:
        """
        Fetches the forecast track data for a specific storm.
        
        Args:
            storm_id: The storm identifier
        
        Returns:
            Dictionary containing forecast track points, or None if fetch fails.
        """
        # NHC provides GeoJSON format for forecast tracks
        forecast_url = f"https://www.nhc.noaa.gov/storm_graphics/api/{storm_id}_CONE_latest.kmz"
        
        try:
            # Try the GeoJSON endpoint first
            geojson_url = f"https://www.nhc.noaa.gov/gis-at.xml"
            response = self.session.get(geojson_url, timeout=10)
            response.raise_for_status()
            
            return {
                'storm_id': storm_id,
                'forecast_data': response.text,
                'source_url': geojson_url
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching forecast track for {storm_id}: {e}")
            return None

"""
Storm Data Parser Module

This module parses the raw storm data from NHC into structured format.
"""

import re
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

class StormParser:
    """Parses NHC storm data into structured format."""
    
    @staticmethod
    def parse_active_storm(storm_data: Dict) -> Dict:
        """
        Parses an active storm from the NHC JSON format.
        
        Args:
            storm_data: Raw storm data dictionary from NHC
        
        Returns:
            Parsed storm information
        """
        parsed = {
            'id': storm_data.get('id', 'Unknown'),
            'name': storm_data.get('name', 'Unknown'),
            'classification': storm_data.get('classification', 'Unknown'),
            'intensity': storm_data.get('intensity', 'Unknown'),
            'pressure': storm_data.get('pressure', 'Unknown'),
            'latitude': storm_data.get('latitude', 'Unknown'),
            'longitude': storm_data.get('longitude', 'Unknown'),
            'movement': storm_data.get('movement', 'Unknown'),
            'last_update': storm_data.get('lastUpdate', 'Unknown'),
            'public_advisory': storm_data.get('publicAdvisory', 'Unknown'),
            'forecast_advisory': storm_data.get('forecastAdvisory', 'Unknown'),
            'wind_speed_kt': storm_data.get('maxSustainedWinds', 'Unknown'),
            'basin': storm_data.get('basin', 'Unknown')
        }
        
        return parsed
    
    @staticmethod
    def extract_coordinates_from_advisory(advisory_text: str) -> Optional[Tuple[float, float]]:
        """
        Extracts latitude and longitude from NHC advisory text.
        
        Args:
            advisory_text: The raw advisory text
        
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        # Pattern: "20.5N 85.3W" or similar
        pattern = r'(\d+\.?\d*)\s*([NS])\s+(\d+\.?\d*)\s*([EW])'
        match = re.search(pattern, advisory_text)
        
        if match:
            lat = float(match.group(1))
            lat_dir = match.group(2)
            lon = float(match.group(3))
            lon_dir = match.group(4)
            
            if lat_dir == 'S':
                lat = -lat
            if lon_dir == 'W':
                lon = -lon
            
            return (lat, lon)
        
        return None
    
    @staticmethod
    def parse_storm_severity(classification: str, wind_speed: str) -> str:
        """
        Determines storm severity based on classification and wind speed.
        
        Args:
            classification: Storm classification (e.g., "Hurricane", "Tropical Storm")
            wind_speed: Maximum sustained wind speed in knots
        
        Returns:
            Severity level as string
        """
        try:
            wind_kt = int(wind_speed) if wind_speed != 'Unknown' else 0
        except (ValueError, TypeError):
            wind_kt = 0
        
        if 'Hurricane' in classification:
            # Saffir-Simpson scale
            if wind_kt >= 137:
                return "Category 5 Hurricane (Catastrophic)"
            elif wind_kt >= 113:
                return "Category 4 Hurricane (Extreme)"
            elif wind_kt >= 96:
                return "Category 3 Hurricane (Major)"
            elif wind_kt >= 83:
                return "Category 2 Hurricane (Moderate)"
            elif wind_kt >= 64:
                return "Category 1 Hurricane (Minimal)"
        elif 'Tropical Storm' in classification:
            return "Tropical Storm"
        elif 'Tropical Depression' in classification:
            return "Tropical Depression"
        elif 'Post-Tropical' in classification:
            return "Post-Tropical Cyclone"
        
        return classification
    
    @staticmethod
    def extract_forecast_positions(advisory_text: str) -> List[Dict]:
        """
        Extracts forecast position points from advisory text.
        
        Args:
            advisory_text: The raw advisory text
        
        Returns:
            List of forecast position dictionaries
        """
        forecast_positions = []
        
        # Pattern for forecast lines: "12H  01/1800Z 20.8N  86.1W   65 KT  75 MPH"
        pattern = r'(\d+H)\s+(\d+/\d+Z)\s+(\d+\.?\d*[NS])\s+(\d+\.?\d*[EW])\s+(\d+)\s*KT'
        
        matches = re.findall(pattern, advisory_text)
        
        for match in matches:
            time_ahead = match[0]
            timestamp = match[1]
            lat_str = match[2]
            lon_str = match[3]
            wind_kt = match[4]
            
            # Parse coordinates
            lat = float(re.search(r'(\d+\.?\d*)', lat_str).group(1))
            if 'S' in lat_str:
                lat = -lat
            
            lon = float(re.search(r'(\d+\.?\d*)', lon_str).group(1))
            if 'W' in lon_str:
                lon = -lon
            
            forecast_positions.append({
                'time_ahead': time_ahead,
                'timestamp': timestamp,
                'latitude': lat,
                'longitude': lon,
                'wind_speed_kt': int(wind_kt)
            })
        
        return forecast_positions

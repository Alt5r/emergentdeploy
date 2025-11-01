"""
FEMA National Shelter System API integration
"""

import httpx
from typing import List, Dict, Optional


class FEMAShelterService:
    """Service to fetch shelter data from FEMA NSS"""

    BASE_URL = "https://gis.fema.gov/arcgis/rest/services/NSS/OpenShelters/MapServer/0/query"

    def __init__(self):
        self.timeout = 15

    def get_shelters(self, state: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
        """
        Fetch shelters from FEMA API

        Args:
            state: Two-letter state code (e.g., 'CA', 'TX') or None for all states
            status: Shelter status ('OPEN', 'CLOSED') or None for all statuses

        Returns:
            List of shelter dictionaries with location and details
        """
        # Build WHERE clause
        conditions = []
        if state:
            conditions.append(f"state='{state.upper()}'")
        if status:
            conditions.append(f"shelter_status='{status.upper()}'")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        params = {
            "where": where_clause,
            "outFields": "*",
            "f": "json",
            "returnGeometry": "true"
        }

        try:
            response = httpx.get(self.BASE_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            if "features" not in data:
                return []

            # Transform to our format
            shelters = []
            for feature in data["features"]:
                attr = feature["attributes"]
                geometry = feature.get("geometry", {})

                shelter = {
                    "id": attr.get("shelter_id"),
                    "name": attr.get("shelter_name"),
                    "address": attr.get("address"),
                    "city": attr.get("city"),
                    "state": attr.get("state"),
                    "zip": attr.get("zip"),
                    "status": attr.get("shelter_status"),
                    "latitude": attr.get("latitude") or geometry.get("y"),
                    "longitude": attr.get("longitude") or geometry.get("x"),
                    "evacuation_capacity": attr.get("evacuation_capacity"),
                    "current_population": attr.get("total_population"),
                    "organization": attr.get("org_name"),
                    "ada_compliant": attr.get("ada_compliant"),
                    "wheelchair_accessible": attr.get("wheelchair_accessible"),
                    "pet_accommodations": attr.get("pet_accommodations_code"),
                    "hours_open": attr.get("hours_open"),
                    "hours_close": attr.get("hours_close"),
                }
                shelters.append(shelter)

            return shelters

        except httpx.HTTPError as e:
            print(f"Error fetching FEMA shelter data: {e}")
            return []

    def get_california_shelters(self) -> List[Dict]:
        """Convenience method to get California shelters"""
        return self.get_shelters(state="CA")

    def get_open_shelters(self, state: Optional[str] = None) -> List[Dict]:
        """Get only open shelters"""
        return self.get_shelters(state=state, status="OPEN")

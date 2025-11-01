#!/usr/bin/env python3
"""
Simple test script to fetch data from FEMA and UK Flood APIs
"""

import httpx
import json


def test_fema_shelters():
    """Test FEMA Open Shelters API - California shelters"""
    print("\n=== Testing FEMA Open Shelters API (California) ===")

    # FEMA ArcGIS endpoint for open shelters
    url = "https://gis.fema.gov/arcgis/rest/services/NSS/OpenShelters/MapServer/0/query"

    params = {
        "where": "state='CA'",  # California shelters (all statuses)
        "outFields": "*",  # All fields
        "f": "json",  # JSON format
        "returnGeometry": "true"
    }

    try:
        response = httpx.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "features" in data:
            shelter_count = len(data["features"])
            print(f"✓ Successfully fetched {shelter_count} California shelters")

            if shelter_count > 0:
                # Show first 3 shelters as examples
                for i, feature in enumerate(data["features"][:3], 1):
                    shelter = feature["attributes"]
                    print(f"\nShelter {i}:")
                    print(f"  Name: {shelter.get('shelter_name')}")
                    print(f"  Location: {shelter.get('city')}, {shelter.get('state')}")
                    print(f"  Address: {shelter.get('address')}")
                    print(f"  Status: {shelter.get('shelter_status')}")
                    print(f"  Capacity: {shelter.get('evacuation_capacity')}")
                    print(f"  Coordinates: ({shelter.get('latitude')}, {shelter.get('longitude')})")

                if shelter_count > 3:
                    print(f"\n... and {shelter_count - 3} more shelters")
        else:
            print("✗ No features returned")

        return data

    except httpx.HTTPError as e:
        print(f"✗ Error fetching FEMA data: {e}")
        return None


def test_uk_floods():
    """Test UK Flood Monitoring API"""
    print("\n=== Testing UK Flood Monitoring API ===")

    # UK Environment Agency flood warnings endpoint
    url = "https://environment.data.gov.uk/flood-monitoring/id/floods"

    params = {
        "min-severity": "2"  # Warning level or higher (1=Severe, 2=Warning, 3=Alert)
    }

    try:
        response = httpx.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "items" in data:
            flood_count = len(data["items"])
            print(f"✓ Successfully fetched {flood_count} flood warnings")

            if flood_count > 0:
                # Show first warning as example
                warning = data["items"][0]
                print(f"\nExample warning:")
                print(f"  Description: {warning.get('description')}")
                print(f"  Severity: {warning.get('severityLevel')} - {warning.get('severity')}")
                print(f"  Area: {warning.get('eaAreaName')}")
                print(f"  Message: {warning.get('message', 'N/A')[:100]}...")
        else:
            print("✗ No items returned")

        return data

    except httpx.HTTPError as e:
        print(f"✗ Error fetching UK flood data: {e}")
        return None


def test_uk_flood_stations():
    """Test UK Flood Monitoring Stations (water levels)"""
    print("\n=== Testing UK Flood Monitoring Stations ===")

    url = "https://environment.data.gov.uk/flood-monitoring/id/stations"

    params = {
        "status": "Active",
        "_limit": "5"  # Just get 5 stations as example
    }

    try:
        response = httpx.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "items" in data:
            station_count = len(data["items"])
            print(f"✓ Successfully fetched {station_count} monitoring stations")

            if station_count > 0:
                station = data["items"][0]
                print(f"\nExample station:")
                print(f"  Name: {station.get('label')}")
                print(f"  River: {station.get('riverName', 'N/A')}")
                print(f"  Town: {station.get('town', 'N/A')}")
                print(f"  Status: {station.get('status')}")
        else:
            print("✗ No items returned")

        return data

    except httpx.HTTPError as e:
        print(f"✗ Error fetching UK station data: {e}")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("Emergency API Test Script")
    print("Testing FEMA (US) and UK Environment Agency APIs")
    print("=" * 60)

    # Test FEMA
    fema_data = test_fema_shelters()

    # Test UK Floods
    uk_flood_data = test_uk_floods()

    # Test UK Stations
    uk_station_data = test_uk_flood_stations()

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

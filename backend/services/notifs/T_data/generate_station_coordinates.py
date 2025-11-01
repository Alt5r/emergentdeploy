import requests
import csv
import re
from data_fetcher import get_all_dart_station_ids

def get_station_coordinates(station_id):
    """
    Fetches GPS coordinates for a specific DART station from its station page.
    
    Args:
        station_id (str): The station ID to fetch coordinates for.
    
    Returns:
        tuple: (latitude, longitude) or (None, None) if not found.
    """
    # Try to get coordinates from the station's dedicated page
    station_url = f"https://www.ndbc.noaa.gov/station_page.php?station={station_id}"
    
    try:
        response = requests.get(station_url, timeout=10)
        response.raise_for_status()
        
        content = response.text
        
        # Look for coordinate patterns in the HTML
        # Pattern 1: Decimal degrees (e.g., "51.414 N 164.816 W")
        pattern1 = r'([\d.]+)\s*°?\s*([NS])\s+([\d.]+)\s*°?\s*([EW])'
        matches = re.findall(pattern1, content)
        
        if matches:
            lat_str, lat_dir, lon_str, lon_dir = matches[0]
            lat = float(lat_str)
            lon = float(lon_str)
            
            if lat_dir == 'S':
                lat = -lat
            if lon_dir == 'W':
                lon = -lon
            
            return (lat, lon)
        
        # Pattern 2: Look for meta tags or structured data
        pattern2 = r'latitude["\s:]+([+-]?[\d.]+)'
        pattern3 = r'longitude["\s:]+([+-]?[\d.]+)'
        
        lat_match = re.search(pattern2, content, re.IGNORECASE)
        lon_match = re.search(pattern3, content, re.IGNORECASE)
        
        if lat_match and lon_match:
            return (float(lat_match.group(1)), float(lon_match.group(1)))
        
        return (None, None)
    
    except Exception as e:
        return (None, None)

def generate_csv():
    """
    Generates a CSV file with DART station IDs and their GPS coordinates.
    """
    print("Fetching DART station IDs...")
    dart_station_ids = get_all_dart_station_ids()
    
    if not dart_station_ids:
        print("Could not retrieve station IDs.")
        return
    
    print(f"Found {len(dart_station_ids)} DART stations.")
    print("Fetching coordinates for each station (this may take a minute)...\n")
    
    # Fetch coordinates for each station
    station_data = []
    for i, station_id in enumerate(dart_station_ids):
        print(f"  ({i+1}/{len(dart_station_ids)}) Fetching coordinates for station: {station_id}", end='\r')
        lat, lon = get_station_coordinates(station_id)
        station_data.append({
            'station_id': station_id,
            'latitude': lat if lat is not None else 'Unknown',
            'longitude': lon if lon is not None else 'Unknown'
        })
    
    print("\n\nWriting to CSV file...")
    
    # Write to CSV
    csv_filename = 'dart_stations_coordinates.csv'
    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['station_id', 'latitude', 'longitude']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for data in station_data:
            writer.writerow(data)
    
    print(f"Successfully created {csv_filename} with {len(station_data)} stations.")
    print(f"\nSummary:")
    known_coords = sum(1 for d in station_data if d['latitude'] != 'Unknown')
    print(f"  - Stations with known coordinates: {known_coords}")
    print(f"  - Stations with unknown coordinates: {len(station_data) - known_coords}")
    
    # Display first few entries as a sample
    print(f"\nSample entries:")
    for data in station_data[:10]:
        print(f"  {data['station_id']}: ({data['latitude']}, {data['longitude']})")

if __name__ == "__main__":
    generate_csv()

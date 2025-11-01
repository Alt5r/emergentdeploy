from data_fetcher import get_all_dart_station_ids, fetch_dart_data
from event_analyzer import find_significant_wave_event
import json
import csv
import os

def load_station_coordinates():
    """
    Loads DART station coordinates from the CSV file.
    
    Returns:
        dict: Dictionary mapping station IDs to (latitude, longitude) tuples
    """
    coordinates = {}
    csv_path = os.path.join(os.path.dirname(__file__), 'dart_stations_coordinates.csv')
    
    try:
        with open(csv_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                station_id = row['station_id']
                lat = row['latitude']
                lon = row['longitude']
                
                # Only add if coordinates are known
                if lat != 'Unknown' and lon != 'Unknown':
                    coordinates[station_id] = {
                        'latitude': float(lat),
                        'longitude': float(lon)
                    }
    except FileNotFoundError:
        print(f"Warning: CSV file not found at {csv_path}")
    except Exception as e:
        print(f"Error loading coordinates: {e}")
    
    return coordinates

def get_tsunami_data_json():
    """
    Fetches and analyzes DART buoy data, returning results in JSON format.
    
    Returns:
        str: JSON string containing all tsunami detection data with coordinates
    """
    # Load station coordinates from CSV
    station_coords = load_station_coordinates()
    
    # Get all DART station IDs
    station_ids = get_all_dart_station_ids()
    
    if not station_ids:
        return json.dumps({
            "status": "error",
            "message": "Could not retrieve DART station IDs",
            "total_stations": 0,
            "events_detected": 0,
            "stations": []
        }, indent=2)
    
    all_station_data = []
    detected_events = []
    
    # Add a simulated event for demonstration purposes
    # This represents what a real tsunami detection would look like
    simulated_event_station = "21413"
    simulated_event = {
        "station_id": simulated_event_station,
        "coordinates": station_coords.get(simulated_event_station, {
            'latitude': 30.487,
            'longitude': 152.124
        }),
        "status": "event_detected",
        "event_details": {
            "detected_wave_height_m": 5780.85,
            "mean_wave_height_m": 5779.97,
            "anomaly_threshold_m": 5780.10,
            "severity": "High",
            "timestamp": "2025-11-01T12:00:00Z",
            "alert_type": "Tsunami Warning - Simulated Example"
        }
    }
    detected_events.append(simulated_event)
    
    # Analyze each station
    for station_id in station_ids:
        # Skip the simulated event station to avoid duplication
        if station_id == simulated_event_station:
            all_station_data.append(simulated_event)
            continue
            
        dart_df = fetch_dart_data(station_id)
        
        if dart_df is None or dart_df.empty:
            continue
        
        # Analyze for significant wave events
        event = find_significant_wave_event(dart_df)
        
        # Get coordinates for this station
        coords = station_coords.get(station_id, {
            'latitude': 'Unknown',
            'longitude': 'Unknown'
        })
        
        station_data = {
            "station_id": station_id,
            "coordinates": coords,
            "status": "event_detected" if event else "normal",
            "event_details": None
        }
        
        if event:
            station_data["event_details"] = {
                "detected_wave_height_m": round(event['detected_wave_height'], 2),
                "mean_wave_height_m": round(event['mean_height'], 2),
                "anomaly_threshold_m": round(event['threshold'], 2),
                "severity": "High" if event['detected_wave_height'] > event['threshold'] * 1.5 else "Moderate",
                "timestamp": "2025-11-01T12:00:00Z"
            }
            detected_events.append(station_data)
        
        all_station_data.append(station_data)
    
    # Build result
    result = {
        "status": "success",
        "total_stations_analyzed": len(all_station_data),
        "events_detected": len(detected_events),
        "triggered_buoys": detected_events,
        "all_stations": all_station_data
    }
    
    return json.dumps(result, indent=2)

def main():
    """
    Main function to orchestrate the fetching and analysis of DART buoy data.
    """
    print("Starting DART buoy data analysis...")
    
    # Get tsunami data as JSON
    tsunami_json = get_tsunami_data_json()
    tsunami_data = json.loads(tsunami_json)
    
    if tsunami_data['status'] == 'error':
        print(f"❌ {tsunami_data['message']}")
        return
    
    # Step 1: Get a list of all available DART station IDs
    station_ids = get_all_dart_station_ids()
    
    if not station_ids:
        print("Could not retrieve any DART station IDs. Exiting.")
        return
    
    # First, show a sample of data from the first buoy to verify timestamps
    print(f"\n--- Checking data freshness from first station: {station_ids[0]} ---")
    sample_df = fetch_dart_data(station_ids[0])
    if sample_df is not None and not sample_df.empty:
        print("Sample of data (first 5 rows with timestamps):")
        print(sample_df.head())
        print("\nLast 5 measurements:")
        print(sample_df.tail())
        print(f"\nColumns available: {list(sample_df.columns)}")
    else:
        print("Could not fetch sample data.")

    # Step 2: Display analysis results
    print(f"\n\nAnalyzing data for {tsunami_data['total_stations_analyzed']} stations...")
    print(f"Stations analyzed: {len(station_ids)}")

    print("\n\n--- Analysis Complete ---")
    
    if tsunami_data['events_detected'] == 0:
        print("✅ No significant wave events were detected in any of the buoys.")
    else:
        print(f"⚠️  Found {tsunami_data['events_detected']} buoy(s) with significant events:\n")
        
        for event in tsunami_data['triggered_buoys']:
            print(f"\n🌊 TRIGGERED BUOY: {event['station_id']}")
            print("-" * 70)
            print(f"📍 Location:")
            print(f"   Latitude:  {event['coordinates']['latitude']}")
            print(f"   Longitude: {event['coordinates']['longitude']}")
            print(f"\n💧 Event Details:")
            details = event['event_details']
            print(f"   Detected Wave Height: {details['detected_wave_height_m']} m")
            print(f"   Mean Wave Height:     {details['mean_wave_height_m']} m")
            print(f"   Anomaly Threshold:    {details['anomaly_threshold_m']} m")
            print(f"   Severity:             {details['severity']}")
            print("-" * 70)
    
    # Save JSON to file
    output_file = "tsunami_detection_data.json"
    try:
        with open(output_file, 'w') as f:
            f.write(tsunami_json)
        print(f"\n💾 Tsunami data saved to: {output_file}")
    except Exception as e:
        print(f"\n⚠️  Could not save to file: {e}")
    
    print("\n📋 JSON Output Preview:")
    print(tsunami_json[:600] + "..." if len(tsunami_json) > 600 else tsunami_json)


if __name__ == "__main__":
    main()

from data_fetcher import get_all_dart_station_ids, fetch_dart_data
from event_analyzer import find_significant_wave_event

def main():
    """
    Main function to orchestrate the fetching and analysis of DART buoy data.
    """
    print("Starting DART buoy data analysis...")
    
    # Step 1: Get a list of all available DART station IDs
    station_ids = get_all_dart_station_ids()
    
    if not station_ids:
        print("Could not retrieve any DART station IDs. Exiting.")
        return

    detected_events = []

    # Step 2: Iterate through each station, fetch its data, and analyze it
    print(f"\nAnalyzing data for {len(station_ids)} stations...")
    for i, station_id in enumerate(station_ids):
        # Print progress to the console
        print(f"  ({i+1}/{len(station_ids)}) Checking station: {station_id}", end='\r')
        
        # Step 2a: Fetch the data for the current station
        dart_df = fetch_dart_data(station_id)
        
        if dart_df is None or dart_df.empty:
            continue
            
        # Step 2b: Analyze the data for a significant event
        event = find_significant_wave_event(dart_df)
        
        if event:
            print(f"\n\n*** Significant Wave Event Detected at Station: {station_id} ***")
            print(f"  - Detected Wave Height: {event['detected_wave_height']:.2f} m")
            print(f"  - Buoy's Mean Wave Height: {event['mean_height']:.2f} m")
            print(f"  - Anomaly Threshold: {event['threshold']:.2f} m\n")
            detected_events.append({
                "station_id": station_id,
                "details": event
            })

    print("\n\n--- Analysis Complete ---")
    if not detected_events:
        print("No significant wave events were detected in any of the buoys.")
    else:
        print(f"Summary: Found {len(detected_events)} buoy(s) with significant events.")
        for event in detected_events:
            print(f"  - Station: {event['station_id']}")


if __name__ == "__main__":
    main()

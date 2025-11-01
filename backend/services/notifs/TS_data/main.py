"""
Main script for fetching and displaying real-time NHC tropical storm data.

This script orchestrates the fetching, parsing, and display of active tropical
storms and hurricanes from NOAA's National Hurricane Center.
"""

from nhc_fetcher import NHCDataFetcher
from storm_parser import StormParser
import json

def display_storm_info(storm, parser, fetcher, storm_number=1):
    """Helper function to display storm information in a formatted way."""
    
    print(f"\n🌀 STORM #{storm_number}")
    print("-" * 70)
    
    # Display basic information
    print(f"Name:           {storm['name']}")
    print(f"ID:             {storm['id']}")
    print(f"Classification: {storm['classification']}")
    
    # Determine severity
    severity = parser.parse_storm_severity(
        storm['classification'], 
        str(storm['wind_speed_kt'])
    )
    print(f"Severity:       {severity}")
    
    # Display position
    print(f"\n📍 Current Position:")
    print(f"   Latitude:    {storm['latitude']}")
    print(f"   Longitude:   {storm['longitude']}")
    
    # Display intensity
    print(f"\n💨 Intensity:")
    print(f"   Max Winds:   {storm['wind_speed_kt']} knots")
    print(f"   Pressure:    {storm['pressure']} mb")
    print(f"   Movement:    {storm['movement']}")
    
    # Display update time
    print(f"\n🕐 Last Update:  {storm['last_update']}")
    
    # Try to get detailed advisory for forecast track
    if storm['id'] != 'Unknown':
        print(f"\n📊 Fetching forecast track...")
        details = fetcher.get_storm_details(storm['id'], storm['basin'])
        
        if details and 'advisory_text' in details:
            # Extract forecast positions
            forecast = parser.extract_forecast_positions(details['advisory_text'])
            
            if forecast:
                print(f"   Found {len(forecast)} forecast points:")
                for fp in forecast[:5]:  # Show first 5 forecast points
                    print(f"      {fp['time_ahead']}: ({fp['latitude']:.2f}, {fp['longitude']:.2f}) - {fp['wind_speed_kt']} kt")
            else:
                print("   Forecast track data not available in advisory.")
    
    storm['severity'] = severity
    print("-" * 70)
    return storm

def fetch_historical_test_data():
    """Fetches a recent historical storm for testing purposes."""
    
    print("\n" + "=" * 70)
    print("TESTING WITH HISTORICAL DATA (2024 Hurricane Season)")
    print("=" * 70)
    print()
    
    # Hurricane Helene (2024) - Recent major hurricane
    # This is example data structure similar to what NHC provides
    test_storm = {
        'id': 'al092024',
        'name': 'Helene',
        'classification': 'Hurricane',
        'intensity': 'Major',
        'pressure': '938',
        'latitude': '26.8N',
        'longitude': '84.5W',
        'movement': 'NNE at 23 mph',
        'lastUpdate': '2024-09-26T18:00:00.000Z',
        'maxSustainedWinds': '120',
        'basin': 'al',
        'publicAdvisory': 'https://www.nhc.noaa.gov/text/refresh/MIATCPAT4+shtml/261459.shtml',
        'forecastAdvisory': 'https://www.nhc.noaa.gov/text/refresh/MIATCMAT4+shtml/261459.shtml'
    }
    
    return [test_storm]

def main():
    """Main function to fetch and display active storm data."""
    
    print("=" * 70)
    print("NOAA National Hurricane Center - Real-time Storm Data")
    print("=" * 70)
    print()
    
    # Initialize fetcher and parser
    fetcher = NHCDataFetcher()
    parser = StormParser()
    
    # Fetch active storms
    print("Fetching active storms from NHC...")
    active_storms = fetcher.get_active_storms()
    
    if active_storms is None:
        print("❌ Failed to fetch storm data. Please check your internet connection.")
        return
    
    all_storm_data = []
    
    if not active_storms or len(active_storms) == 0:
        print("✅ No active tropical storms or hurricanes at this time.")
        print("   This is good news!")
        
        # Fetch historical test data to verify functionality
        print("\n⚠️  Since there are no active storms, testing with recent historical data...")
        test_storms = fetch_historical_test_data()
        
        for i, storm_raw in enumerate(test_storms, 1):
            storm = parser.parse_active_storm(storm_raw)
            storm_data = display_storm_info(storm, parser, fetcher, i)
            all_storm_data.append(storm_data)
    else:
        print(f"✅ Found {len(active_storms)} active storm(s)\n")
        print("=" * 70)
        
        # Process each active storm
        for i, storm_raw in enumerate(active_storms, 1):
            storm = parser.parse_active_storm(storm_raw)
            storm_data = display_storm_info(storm, parser, fetcher, i)
            all_storm_data.append(storm_data)
    
    # Save all data to JSON file
    output_file = "active_storms_data.json"
    try:
        with open(output_file, 'w') as f:
            json.dump(all_storm_data, f, indent=2)
        print(f"\n💾 Storm data saved to: {output_file}")
    except Exception as e:
        print(f"\n⚠️  Could not save to file: {e}")
    
    print("\n" + "=" * 70)
    print("Data fetch complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()

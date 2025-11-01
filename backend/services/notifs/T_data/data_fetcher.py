import requests
from bs4 import BeautifulSoup
import pandas as pd
import io

def get_all_dart_station_ids():
    """
    Fetches the list of all DART station IDs by scraping the NDBC real-time data directory.
    This is a fallback method and does not provide coordinates.
    """
    data_directory_url = "https://www.ndbc.noaa.gov/data/realtime2/"
    print(f"Fetching list of .dart files from {data_directory_url}...")

    try:
        response = requests.get(data_directory_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        station_ids = []
        # Find all links (<a> tags) in the HTML
        for link in soup.find_all('a'):
            href = link.get('href')
            # If the link's destination ends with .dart, it's a data file
            if href and href.endswith('.dart'):
                # The station ID is the filename without the .dart extension
                station_id = href.replace('.dart', '')
                station_ids.append(station_id)
        
        print(f"Found {len(station_ids)} stations with .dart files.")
        return station_ids

    except requests.exceptions.RequestException as e:
        print(f"Error fetching DART data directory: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while scraping buoy list: {e}")
        return []

def fetch_dart_data(station_id):
    """
    Fetches the real-time data (.dart file) for a single DART station.
    """
    base_data_url = "https://www.ndbc.noaa.gov/data/realtime2/"
    data_url = f"{base_data_url}{station_id}.dart"
    
    try:
        data_response = requests.get(data_url)
        data_response.raise_for_status()
        
        dart_data = data_response.text
        if not dart_data.strip() or dart_data.startswith("<!DOCTYPE"):
            return None
            
        data_io = io.StringIO(dart_data)
        
        df = pd.read_csv(data_io, delim_whitespace=True, skiprows=2)
        
        # The last column is the sea surface height. Rename it for clarity.
        df.rename(columns={df.columns[-1]: 'sea_surface_height_m'}, inplace=True)
        
        return df

    except requests.exceptions.RequestException:
        # This can happen if the link exists but the file is empty or an error page
        return None
    except Exception as e:
        print(f"Error processing data for station {station_id}: {e}")
        return None

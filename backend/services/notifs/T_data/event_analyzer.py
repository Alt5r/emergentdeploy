import pandas as pd

def find_significant_wave_event(df: pd.DataFrame, threshold_std_dev: float = 3.5) -> dict | None:
    """
    Analyzes DART buoy data to find significant wave height anomalies.

    A simple but effective method for detecting tsunamis or rogue waves is to look for
    measurements that are a significant number of standard deviations away from the mean.

    Args:
        df (pd.DataFrame): DataFrame containing the buoy data. Must have a 
                           'sea_surface_height_m' column.
        threshold_std_dev (float): The number of standard deviations from the mean
                                   to consider a measurement an anomaly. A value of 3.5
                                   is a common starting point.

    Returns:
        A dictionary with event details if a significant event is found, otherwise None.
    """
    if df is None or df.empty:
        return None

    # Ensure the sea surface height column exists
    if 'sea_surface_height_m' not in df.columns:
        print("Warning: 'sea_surface_height_m' column not found in DataFrame.")
        return None

    # Convert the measurement column to a numeric type, coercing errors
    df['sea_surface_height_m'] = pd.to_numeric(df['sea_surface_height_m'], errors='coerce')
    df.dropna(subset=['sea_surface_height_m'], inplace=True)

    if df.empty:
        return None

    # --- Anomaly Detection Logic ---
    # 1. Calculate the mean and standard deviation of the sea surface height
    mean_height = df['sea_surface_height_m'].mean()
    std_dev_height = df['sea_surface_height_m'].std()

    # 2. Get the most recent measurement
    last_measurement = df['sea_surface_height_m'].iloc[-1]

    # 3. Define the threshold for an anomaly
    # An event is a measurement that is significantly higher than the average.
    anomaly_threshold = mean_height + (std_dev_height * threshold_std_dev)

    # 4. Check if the last measurement exceeds the threshold
    if last_measurement > anomaly_threshold:
        return {
            "detected_wave_height": last_measurement,
            "mean_height": mean_height,
            "threshold": anomaly_threshold
        }
    
    return None

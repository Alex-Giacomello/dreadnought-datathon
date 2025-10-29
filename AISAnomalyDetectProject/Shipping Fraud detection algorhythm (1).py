"""

Sorry, but NO I haven't debuged this yet.  Let me think my code is complete...denial isn't just a river.

Start excessinly long Explanation and Design Choices Monologue:

-Modularity and Readability: The code is broken into clear functions (haversine_distance_nm, get_most_recent_files, load_and_preprocess_day, detect_shipping_anomalies) to improve readability, maintainability, and testability.
-Configuration: Key parameters are defined at the top as constants, making them easy to adjust without digging into the logic.
-Error Handling (File Loading):
----load_and_preprocess_day is robust. It uses try-except blocks to catch common IOError, EmptyDataError, ParserError, and ValueError (for missing columns or bad timestamps).
----It prints informative error messages but continues processing other files, as required.
----low_memory=False in pd.read_csv is used to prevent mixed-type inference warnings on large columns, although it might use more memory initially.
-Memory Management:
----While the current load_and_preprocess_day loads each day's CSV into a Pandas DataFrame, this is a critical point for Dask integration. For 8M+ rows per day, if num_days_to_analyze is large, loading all into memory will crash.
----The current approach processes day-by-day comparisons. This means at any given time, only two days' worth of data (df_previous_day and df_current_day) are actively held in memory as Pandas DataFrames, which is a significant optimization for memory. Dask was recommended, but I don't have any experience with it so it is not implemented in the code.
--------Where Dask would be beneficial:
------------load_and_preprocess_day: If a single day's file itself exceeds available RAM (unlikely but possible), this function could be rewritten to return a Dask DataFrame.
------------haversine_distance_nm and merged_df processing: If the number of common MMSI for distance calculation is extremely high, merged_df.apply could be slow. Replacing this with Dask's map_partitions for the distance calculation would distribute the workload. I've noted this in the comments.
------------get_most_recent_files: If the file parsing logic needs to be distributed.
-Data Filtering and Schema Enforcement:
----Columns are explicitly selected and ShipType filtered early to reduce memory footprint.
----pd.to_datetime with errors='coerce' handles bad timestamp strings gracefully, converting them to NaT (Not a Time), which are then dropped.
----pd.to_numeric handles coordinate and speed conversion, dropping NaNs if critical data is missing.

-Anomaly Detection Logic:
----AIS Beacon On/Off: Leverages Python set operations (union, difference) which are highly optimized for finding unique elements and their differences. This is efficient for identifying missing or reappearing MMSIs.
-Excessive Travel Distance:
----Defined as 200<>550NM based on average upper and lower bounds for daily travel distance for CARGO ships
----Uses geopy.distance.great_circle for accurate Haversine distance.
----Merges previous and current day dataframes on MMSI to align positions for calculation.
----The apply function is used for row-wise distance calculation. Again, for extreme scale, this would be a Dask candidate.
____ADD Map Plot by day using MIMSI


-Performance Target (Trying to keep it under 5 minutes per day - Faster is better):
----The day-by-day processing strategy is key here. Instead of loading N days, concatenating to one giant DataFrame, and then processing, we process day N vs N+1, then N+1 vs N+2, etc. This keeps the active memory footprint low and allows for a more predictable performance per comparison step.
----Set operations for beacon detection are very fast.
--------The Pandas merge and apply for distance calculation are the most computationally intensive parts. Optimizations like using numpy for vectorized Haversine (if geopy proves too slow) or Dask for distributed apply might be needed if the 5-minute (or lower) target is consistently missed with real data.
-Output and Reporting:
----Anomaly reports are collected into a list of dictionaries, then converted to a Pandas DataFrame and saved to a .csv with the specified naming convention.
----Reports are saved in the DATA_DIRECTORY that we haven't decided on.  Will need update in code.
-Current User Interaction (if __name__ == "__main__":)
----A simple command-line prompt handles user input for the number of days, with basic validation.
----Will change once GUI config.ini is developed to handle all varibles.-
-How to Use: (WILL BE UPDATED ONCE WE MOVE FROM STAND-ALONE)
----Install Dependencies: pip install pandas dask geopy
----Configure: Change DATA_DIRECTORY to the actual path where our AIS .csv files are/will be stored.
----Run: Open a command prompt or terminal, navigate to the directory where you saved the file, and run: Shipping Fraud Detection Algorhythm.py
----Input: Enter the number of days you want to analyze when prompted.
---------------------------------------------------------------------------------
-Integration with other code development so far:
----This was build as a stand-alone program.  It will need to be updated to take information and user-input variables from the GUI adn Config.ini files .
----It will need to update all PATHs to Data resources based on out git repository/S3 bucket structure.
----For this code I assumed a file format of .csv - I haven't worked with Parquet.  Code (or data repository) must be updated.

End excessinly long Explanation and Design Choices Monologue.
"""


import os
import pandas as pd
import dask.dataframe as dd
from datetime import datetime, timedelta
from geopy.distance import great_circle # Using geopy for Haversine

# --- Configuration ---
DATA_DIRECTORY = "C:\\AIS_Data"  # Specify your AIS data directory
REQUIRED_COLUMNS = [
    'MMSI', 'ShipName', 'ShipType', 'Latitude', 'Longitude',
    'Timestamp', 'Speed', 'Heading'
]
SHIP_TYPE_MIN = 70
SHIP_TYPE_MAX = 89
MIN_TRAVEL_NM = 200
MAX_TRAVEL_NM = 550
TIMESTAMP_FORMAT = '%Y-%m-%d %H-%M-%S' # Corrected from HH-MM-SS to HH:MM:SS in standard practice, assuming input is consistent

# --- Helper Functions ---

def haversine_distance_nm(lat1, lon1, lat2, lon2):
    """
    Calculates the great-circle distance between two points on the Earth
    (specified in decimal degrees) in nautical miles.
    """
    if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
        return None
    # geopy's great_circle returns distance in km by default, convert to NM
    return great_circle((lat1, lon1), (lat2, lon2)).nm

def get_most_recent_files(data_dir, num_days):
    """
    Identifies the most recent AIS .csv files based on their filenames (date).
    Assumes filenames are in YYYY-MM-DD.csv format.
    """
    all_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    dated_files = {}
    for f in all_files:
        try:
            date_str = f.replace('.csv', '')
            file_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            dated_files[file_date] = os.path.join(data_dir, f)
        except ValueError:
            print(f"Warning: Skipping malformed filename {f}. Expected YYYY-MM-DD.csv")
            continue

    sorted_dates = sorted(dated_files.keys(), reverse=True)
    selected_files = []
    selected_dates = []
    for i in range(min(num_days + 1, len(sorted_dates))): # Need num_days + 1 for comparisons
        selected_files.append(dated_files[sorted_dates[i]])
        selected_dates.append(sorted_dates[i])

    # Ensure files are in chronological order for processing
    selected_files.reverse()
    selected_dates.reverse()

    return selected_files, selected_dates

def load_and_preprocess_day(file_path):
    """
    Loads a single daily CSV, handles errors, and performs initial preprocessing.
    Returns a pandas DataFrame or None if an error occurs.
    """
    try:
        # Dask can infer schema from the first file, but explicitly defining helps
        # especially with mixed types or missing columns in subsequent files.
        df = pd.read_csv(file_path, low_memory=False)

        # Check for required columns
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

        # Select only required columns and filter ship types early
        df = df[REQUIRED_COLUMNS]
        df = df[(df['ShipType'] >= SHIP_TYPE_MIN) & (df['ShipType'] <= SHIP_TYPE_MAX)]

        # Convert Timestamp
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], format=TIMESTAMP_FORMAT, errors='coerce')
        df.dropna(subset=['Timestamp', 'Latitude', 'Longitude', 'MMSI'], inplace=True)

        # Ensure numeric types for coordinates and speed
        df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
        df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
        df['Speed'] = pd.to_numeric(df['Speed'], errors='coerce')
        df['Heading'] = pd.to_numeric(df['Heading'], errors='coerce')
        df.dropna(subset=['Latitude', 'Longitude'], inplace=True) # Drop rows if essential numerics are missing

        # Add a 'date' column for easy grouping/identification
        df['Date'] = df['Timestamp'].dt.date

        return df

    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
    except pd.errors.EmptyDataError:
        print(f"Error: Empty CSV file - {file_path}")
    except pd.errors.ParserError:
        print(f"Error: Malformed CSV content - {file_path}")
    except ValueError as e:
        print(f"Error in {file_path}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while processing {file_path}: {e}")
    return None

# --- Main Detection Algorithm ---

def detect_shipping_anomalies(num_days_to_analyze):
    """
    Main function to orchestrate the loading, processing, and anomaly detection.
    """
    print(f"\n--- Starting AIS Fraud Detection for the last {num_days_to_analyze} days ---")
    file_paths, dates_in_order = get_most_recent_files(DATA_DIRECTORY, num_days_to_analyze)

    if not file_paths or len(file_paths) <= 1:
        print("Not enough valid daily files found for comparison. Need at least 2 days.")
        return

    # Process files day by day for comparisons
    df_previous_day = None
    processed_first_day = False # Flag to manage the first iteration where previous_day doesn't exist

    for i in range(len(file_paths)):
        current_file_path = file_paths[i]
        current_date = dates_in_order[i]
        print(f"\nProcessing data for: {current_date.strftime('%Y-%m-%d')} ({current_file_path})")

        df_current_day = load_and_preprocess_day(current_file_path)

        if df_current_day is None:
            print(f"Skipping {current_file_path} due to loading errors.")
            df_previous_day = None # Reset previous day if current fails
            continue

        if not processed_first_day:
            df_previous_day = df_current_day
            processed_first_day = True
            print(f"Loaded initial day: {current_date.strftime('%Y-%m-%d')}. No comparisons possible yet.")
            continue # Skip to the next day for comparisons

        # --- ANOMALY DETECTION FOR current_date (comparing with df_previous_day) ---
        anomalies = []
        report_date = current_date.strftime('%Y-%m-%d')

        # 1. AIS Beacon Off (No Report)
        # MMSI present in previous day but not in current day
        mmsi_prev_day = set(df_previous_day['MMSI'].unique())
        mmsi_current_day = set(df_current_day['MMSI'].unique())

        beacon_off_mmsi = list(mmsi_prev_day - mmsi_current_day)
        if beacon_off_mmsi:
            beacon_off_ships = df_previous_day[df_previous_day['MMSI'].isin(beacon_off_mmsi)]
            # Get last known position for beacon off
            beacon_off_last_positions = beacon_off_ships.groupby('MMSI').last().reset_index()
            for _, row in beacon_off_last_positions.iterrows():
                anomalies.append({
                    'Date of Anomaly': report_date,
                    'Ship Name': row['ShipName'],
                    'MMSI': row['MMSI'],
                    'Latitude': row['Latitude'],
                    'Longitude': row['Longitude'],
                    'Type of Anomaly Detected': 'AIS Beacon Off'
                })

        # 2. AIS Beacon On (Sudden Reappearance)
        # MMSI present in current day but not in previous day
        beacon_on_mmsi = list(mmsi_current_day - mmsi_prev_day)
        if beacon_on_mmsi:
            beacon_on_ships = df_current_day[df_current_day['MMSI'].isin(beacon_on_mmsi)]
            for _, row in beacon_on_ships.iterrows():
                anomalies.append({
                    'Date of Anomaly': report_date,
                    'Ship Name': row['ShipName'],
                    'MMSI': row['MMSI'],
                    'Latitude': row['Latitude'],
                    'Longitude': row['Longitude'],
                    'Type of Anomaly Detected': 'AIS Beacon On'
                })

        # 3. Excessive Travel Distance (requires merging data for common MMSI)
        # Only consider ships present in both reports
        common_mmsi = list(mmsi_prev_day.intersection(mmsi_current_day))

        if common_mmsi:
            df_prev_common = df_previous_day[df_previous_day['MMSI'].isin(common_mmsi)].set_index('MMSI')
            df_curr_common = df_current_day[df_current_day['MMSI'].isin(common_mmsi)].set_index('MMSI')

            # Merge to get previous and current positions side-by-side for distance calculation
            merged_df = df_prev_common[['Latitude', 'Longitude', 'ShipName']].add_prefix('prev_').join(
                        df_curr_common[['Latitude', 'Longitude']].add_prefix('curr_'),
                        how='inner') # Inner join ensures only ships present in both

            # Calculate distance using Dask for potential parallelization on large number of common_mmsi
            # For this scale, a direct apply might be fine, but Dask setup is good for future
            # If dask.dataframe is used for merged_df, then use dask.dataframe.map_partitions
            # For now, keeping it Pandas-native for simplicity but acknowledging Dask's role.
            # Using apply directly on a large DataFrame could be slow, so consider Dask here.

            # We'll stick to Pandas apply for now, but note this is a prime candidate for Dask map_partitions
            # for true scalability if `merged_df` becomes too large for a single core.
            merged_df['Distance_NM'] = merged_df.apply(
                lambda row: haversine_distance_nm(
                    row['prev_Latitude'], row['prev_Longitude'],
                    row['curr_Latitude'], row['curr_Longitude']
                ), axis=1
            )

            # Flag based on distance
            fast_travel_ships = merged_df[merged_df['Distance_NM'] > MAX_TRAVEL_NM]
            slow_travel_ships = merged_df[merged_df['Distance_NM'] < MIN_TRAVEL_NM]

            for mmsi, row in fast_travel_ships.iterrows():
                anomalies.append({
                    'Date of Anomaly': report_date,
                    'Ship Name': row['prev_ShipName'], # Use prev_ShipName as it's consistent
                    'MMSI': mmsi,
                    'Latitude': row['curr_Latitude'],
                    'Longitude': row['curr_Longitude'],
                    'Type of Anomaly Detected': 'Excessive Travel Distance (Fast)'
                })

            for mmsi, row in slow_travel_ships.iterrows():
                anomalies.append({
                    'Date of Anomaly': report_date,
                    'Ship Name': row['prev_ShipName'],
                    'MMSI': mmsi,
                    'Latitude': row['curr_Latitude'],
                    'Longitude': row['curr_Longitude'],
                    'Type of Anomaly Detected': 'Excessive Travel Distance (Slow)'
                })


        # --- Output Report for the Current Day ---
        if anomalies:
            anomalies_df = pd.DataFrame(anomalies)
            output_filename = f"Report for {report_date}.csv"
            output_path = os.path.join(DATA_DIRECTORY, output_filename) # Save report in the data directory
            anomalies_df.to_csv(output_path, index=False)
            print(f"Generated anomaly report: {output_path} with {len(anomalies)} anomalies.")
        else:
            print(f"No anomalies detected for {report_date}.")

        # Prepare for the next iteration
        df_previous_day = df_current_day.copy() # Make a copy to avoid modifying original

    print("\n--- AIS Fraud Detection Complete ---")


# --- User Interaction ---
if __name__ == "__main__":
    while True:
        try:
            days_input = input(f"Enter the number of days to analyze (e.g., 5): ")
            num_days = int(days_input)
            if num_days <= 0:
                raise ValueError("Number of days must be positive.")
            break
        except ValueError as e:
            print(f"Invalid input: {e}. Please enter a positive integer.")

    detect_shipping_anomalies(num_days)



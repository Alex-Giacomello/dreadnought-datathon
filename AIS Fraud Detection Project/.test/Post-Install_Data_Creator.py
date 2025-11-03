#!/usr/bin/env python3
"""
AIS Shipping Fraud Detection - Test Data Generator
Creates 30 days of AIS data with anomalies for testing
"""
import os
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import math
from pathlib import Path
import shutil  # For directory operations

# Constants
START_DATE = datetime(2024, 10, 1)
END_DATE = datetime(2024, 10, 31)
NUM_NORMAL_SHIPS = 90  # 45 Tankers and 45 CargoShips
NUM_BAD_SHIPS = 10     # 5 BadTankers and 5 BadCargoShips
TOTAL_SHIPS = NUM_NORMAL_SHIPS + NUM_BAD_SHIPS
ANOMALY_TYPES = [
    'AIS_Beacon_Off',          # Ships disappearing from tracking
    'AIS_Beacon_On',           # Ships suddenly reappearing
    'Excessive_Travel_Fast',   # Unusually fast movements (>500 NM/day)
    'Excessive_Travel_Slow',   # Unusually slow movements (<200 NM/day)
    'COG_Heading_Inconsistency'  # Significant deviations in heading and COG (>45 degrees)
]

# AIS vessel type codes
# 70-79: Cargo vessels
# 80-89: Tankers
CARGO_TYPE_CODES = list(range(70, 80))  # 70-79
TANKER_TYPE_CODES = list(range(80, 90))  # 80-89

def generate_test_data():
    """Generate realistic AIS data with anomalies"""
    print(f"Generating test data for {TOTAL_SHIPS} ships from {START_DATE} to {END_DATE}")
    
    # Generate ship information
    ships = []
    
    # Create normal Tanker ships (45)
    for i in range(45):
        ships.append({
            'mmsi': random.randint(200000000, 799999999),
            'name': f"Tanker {i+1}",
            'type': 80,  # Tanker code
            'length': random.randint(150, 350),
            'home_lat': random.uniform(-80, 80),
            'home_lon': random.uniform(-179, 179),
            'max_speed': random.uniform(5, 25),  # knots
            'is_bad_actor': False  # This ship doesn't have anomalies
        })
    
    # Create normal CargoShip ships (45)
    for i in range(45):
        ships.append({
            'mmsi': random.randint(200000000, 799999999),
            'name': f"CargoShip {i+1}",
            'type': 70,  # Cargo code
            'length': random.randint(100, 300),
            'home_lat': random.uniform(-80, 80),
            'home_lon': random.uniform(-179, 179),
            'max_speed': random.uniform(5, 25),  # knots
            'is_bad_actor': False  # This ship doesn't have anomalies
        })
    
    # Create bad Tanker ships (5)
    for i in range(5):
        ships.append({
            'mmsi': random.randint(200000000, 799999999),
            'name': f"BadTanker {i+1}",
            'type': 80,  # Tanker code
            'length': random.randint(150, 350),
            'home_lat': random.uniform(-80, 80),
            'home_lon': random.uniform(-179, 179),
            'max_speed': random.uniform(5, 25),  # knots
            'is_bad_actor': True  # This ship will have anomalies
        })
    
    # Create bad CargoShip ships (5)
    for i in range(5):
        ships.append({
            'mmsi': random.randint(200000000, 799999999),
            'name': f"BadCargoShip {i+1}",
            'type': 70,  # Cargo code
            'length': random.randint(100, 300),
            'home_lat': random.uniform(-80, 80),
            'home_lon': random.uniform(-179, 179),
            'max_speed': random.uniform(5, 25),  # knots
            'is_bad_actor': True  # This ship will have anomalies
        })
    
    # Generate basic movement data
    print("Generating movement data...")
    records = []
    
    for day in range(30):
        # Use a fixed time (noon) for all records in a day
        current_time = START_DATE + timedelta(days=day, hours=12)
        
        for ship in ships:
            # 5% chance ship doesn't transmit this day
            if random.random() < 0.05:
                continue
            
            # Create semi-random movement pattern
            movement_factor = day/30 * 2*math.pi  # circular-ish pattern over month
            
            lat = ship['home_lat'] + 3 * math.sin(movement_factor)
            lon = ship['home_lon'] + 3 * math.cos(movement_factor) 
            
            # Speed and course
            speed = random.uniform(0, ship['max_speed'])
            course = random.uniform(0, 359)
            
            # Navigation status (0=underway, 1=anchored, 5=moored)
            nav_status = random.choices([0, 1, 5], weights=[80, 10, 10])[0]
            
            records.append({
                'MMSI': ship['mmsi'],
                'BaseDateTime': current_time,
                'LAT': lat,
                'LON': lon,
                'SOG': speed,
                'COG': course,
                'Heading': course + random.uniform(-10, 10),  # Heading is typically close to course
                'VesselName': ship['name'],
                'IMO': '1010',
                'CallSign': '1010',
                'VesselType': ship['type'],
                'Status': nav_status,
                'Length': ship['length'],
                'Width': 1010,
                'Draft': 1010,
                'Cargo': 1010,
                'TransceiverClass': '1010',
                'anomaly': None
            })
    
    # Create dataframe
    df = pd.DataFrame(records)
    print(f"Generated {len(df)} AIS records")
    
    # Inject anomalies
    print("Injecting anomalies...")
    # Get only the bad ships
    bad_ships = [ship for ship in ships if ship['is_bad_actor']]
    
    for anomaly_type in ANOMALY_TYPES:
        # Create 3 instances of each anomaly type
        for instance in range(3):
            # Select a random bad ship for this anomaly instance (with replacement)
            # This means some ships might have multiple different anomaly types
            anomaly_ship = random.choice(bad_ships)
            
            # Get records for this ship
            ship_data = df[df['MMSI'] == anomaly_ship['mmsi']]
            if len(ship_data) < 5:
                continue
                
            # Pick a random time in the middle of the dataset
            idx = random.randint(len(ship_data)//4, 3*len(ship_data)//4)
            record_idx = ship_data.iloc[idx].name
            
            # Apply anomaly based on type
            if anomaly_type == 'AIS_Beacon_Off':
                # Find consecutive records and remove them (ship disappears)
                consecutive_records = df[(df['MMSI'] == anomaly_ship['mmsi']) & 
                                         (df['BaseDateTime'] >= df.loc[record_idx, 'BaseDateTime'])].iloc[:12]  # Missing for 24 hours
                
                # Mark the last record before disappearing
                if record_idx in df.index:
                    df.loc[record_idx, 'anomaly'] = 'AIS_Beacon_Off Day 1'
                
                # Drop the records to simulate disappearance
                df = df.drop(consecutive_records.index)
                
            elif anomaly_type == 'AIS_Beacon_On':
                # Ship suddenly reappears
                # First, find a gap in the data to insert records
                ship_data_sorted = df[df['MMSI'] == anomaly_ship['mmsi']].sort_values('BaseDateTime')
                
                if len(ship_data_sorted) > 5:
                    # Select a point after which to insert reappearance
                    middle_idx = len(ship_data_sorted) // 2
                    reappear_time = ship_data_sorted.iloc[middle_idx]['BaseDateTime'] + timedelta(hours=24)
                    
                    # Get last known position
                    last_lat = ship_data_sorted.iloc[middle_idx]['LAT']
                    last_lon = ship_data_sorted.iloc[middle_idx]['LON']
                    
                    # Create a new reappearance record
                    new_record = ship_data_sorted.iloc[middle_idx].copy()
                    new_record['BaseDateTime'] = reappear_time
                    new_record['LAT'] = last_lat + random.uniform(0.5, 2.0)  # Slight position change
                    new_record['LON'] = last_lon + random.uniform(0.5, 2.0)  # Slight position change
                    new_record['anomaly'] = 'AIS_Beacon_On Day 1'
                    
                    # Add the record to the dataframe
                    df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
                
            elif anomaly_type == 'Excessive_Travel_Fast':
                # Create unusually fast movement (>500 NM/day)
                # Find two consecutive records (now one day apart since one record per day)
                ship_data_sorted = df[df['MMSI'] == anomaly_ship['mmsi']].sort_values('BaseDateTime')
                
                if len(ship_data_sorted) > 5:
                    # Select two points a day apart
                    day1_idx = len(ship_data_sorted) // 3
                    day2_idx = day1_idx + 1  # One record later (next day)
                    
                    if day2_idx < len(ship_data_sorted):
                        # Modify the position of the second day to be very far from first
                        day1_record = ship_data_sorted.iloc[day1_idx]
                        day2_record = ship_data_sorted.iloc[day2_idx]
                        
                        # Calculate a position that's more than 500 NM away
                        distance_nm = 550 + random.uniform(50, 200)  # 550-750 NM
                        bearing = random.uniform(0, 360)  # Random direction
                        
                        # Earth's radius in nautical miles
                        earth_radius = 3440.065
                        
                        # Convert to radians
                        lat1 = math.radians(day1_record['LAT'])
                        lon1 = math.radians(day1_record['LON'])
                        
                        # Calculate new position
                        lat2 = math.asin(math.sin(lat1) * math.cos(distance_nm/earth_radius) + 
                                        math.cos(lat1) * math.sin(distance_nm/earth_radius) * math.cos(math.radians(bearing)))
                        
                        lon2 = lon1 + math.atan2(math.sin(math.radians(bearing)) * math.sin(distance_nm/earth_radius) * math.cos(lat1), 
                                                math.cos(distance_nm/earth_radius) - math.sin(lat1) * math.sin(lat2))
                        
                        # Convert back to degrees
                        new_lat = math.degrees(lat2)
                        new_lon = math.degrees(lon2)
                        
                        # Apply the anomaly
                        df.loc[day1_record.name, 'anomaly'] = 'Excessive_Travel_Fast Day 1'
                        df.loc[day2_record.name, 'LAT'] = new_lat
                        df.loc[day2_record.name, 'LON'] = new_lon
                        df.loc[day2_record.name, 'anomaly'] = 'Excessive_Travel_Fast Day 2'
                
            elif anomaly_type == 'Excessive_Travel_Slow':
                # Create unusually slow movement (<200 NM/day)
                # Find two consecutive records (now one day apart)
                ship_data_sorted = df[df['MMSI'] == anomaly_ship['mmsi']].sort_values('BaseDateTime')
                
                if len(ship_data_sorted) > 5:
                    # Select two points a day apart
                    day1_idx = len(ship_data_sorted) // 3
                    day2_idx = day1_idx + 1  # One record later (next day)
                    
                    if day2_idx < len(ship_data_sorted):
                        # Modify the position of the second day to be very close to first
                        day1_record = ship_data_sorted.iloc[day1_idx]
                        day2_record = ship_data_sorted.iloc[day2_idx]
                        
                        # Calculate a position that's less than 200 NM away
                        distance_nm = random.uniform(50, 150)  # 50-150 NM
                        bearing = random.uniform(0, 360)  # Random direction
                        
                        # Earth's radius in nautical miles
                        earth_radius = 3440.065
                        
                        # Convert to radians
                        lat1 = math.radians(day1_record['LAT'])
                        lon1 = math.radians(day1_record['LON'])
                        
                        # Calculate new position
                        lat2 = math.asin(math.sin(lat1) * math.cos(distance_nm/earth_radius) + 
                                        math.cos(lat1) * math.sin(distance_nm/earth_radius) * math.cos(math.radians(bearing)))
                        
                        lon2 = lon1 + math.atan2(math.sin(math.radians(bearing)) * math.sin(distance_nm/earth_radius) * math.cos(lat1), 
                                                math.cos(distance_nm/earth_radius) - math.sin(lat1) * math.sin(lat2))
                        
                        # Convert back to degrees
                        new_lat = math.degrees(lat2)
                        new_lon = math.degrees(lon2)
                        
                        # Apply the anomaly
                        df.loc[day1_record.name, 'anomaly'] = 'Excessive_Travel_Slow Day 1'
                        df.loc[day2_record.name, 'LAT'] = new_lat
                        df.loc[day2_record.name, 'LON'] = new_lon
                        df.loc[day2_record.name, 'anomaly'] = 'Excessive_Travel_Slow Day 2'
                
            elif anomaly_type == 'COG_Heading_Inconsistency':
                # Create significant deviation between COG and heading (>45 degrees)
                # With one record per day, we'll check for sufficient speed in any available records
                fast_records = ship_data[ship_data['SOG'] >= 5]  # Lowered threshold to ensure we find records
                
                if not fast_records.empty:
                    # Select a random fast record
                    fast_idx = random.randint(0, len(fast_records)-1)
                    fast_record_idx = fast_records.iloc[fast_idx].name
                    
                    if fast_record_idx in df.index:
                        # Get current COG
                        current_cog = df.loc[fast_record_idx, 'COG']
                        
                        # Create heading with significant deviation (>45 degrees)
                        deviation = random.uniform(50, 90)  # 50-90 degrees deviation
                        if random.random() < 0.5:
                            new_heading = (current_cog + deviation) % 360
                        else:
                            new_heading = (current_cog - deviation) % 360
                        
                        # Apply the anomaly
                        df.loc[fast_record_idx, 'Heading'] = new_heading
                        df.loc[fast_record_idx, 'anomaly'] = 'COG_Heading_Inconsistency'
            
            # No need to mark the anomaly here as we've already marked it in each specific section
    
    return df

def save_data(df):
    """Save the generated data"""
    # Create output directory in user's home
    output_dir = os.path.join(str(Path.home()), "Test_data")
    os.makedirs(output_dir, exist_ok=True)
    
    # Save dataset as testing_data.csv
    output_file = os.path.join(output_dir, "testing_data.csv")
    df.to_csv(output_file, index=False)
    print(f"Complete data saved to {output_file}")
    
    # Create a metadata file
    metadata = {
        'generation_date': datetime.now().strftime('%Y-%m-%d'),
        'start_date': START_DATE.strftime('%Y-%m-%d'),
        'end_date': END_DATE.strftime('%Y-%m-%d'),
        'num_ships': TOTAL_SHIPS,
        'num_normal_ships': NUM_NORMAL_SHIPS,
        'num_bad_ships': NUM_BAD_SHIPS,
        'num_records': len(df)
    }
    
    metadata_file = os.path.join(output_dir, "metadata.txt")
    with open(metadata_file, 'w') as f:
        for key, value in metadata.items():
            f.write(f"{key}: {value}\n")
    
    print(f"Metadata saved to {metadata_file}")
    
    return output_file

def split_into_daily_files(csv_file_path):
    """Split a large CSV file into daily CSV files with format ais-YYYY-MM-DD.csv"""
    print("\nSplitting data into daily files...")
    
    # Get the directory from the input file path
    output_dir = os.path.dirname(csv_file_path)
    
    # Read the CSV file
    df = pd.read_csv(csv_file_path)
    
    # Convert BaseDateTime to datetime if it's a string
    if df['BaseDateTime'].dtype == 'object':
        df['BaseDateTime'] = pd.to_datetime(df['BaseDateTime'])
    
    # Extract date for grouping
    df['date'] = df['BaseDateTime'].dt.date
    
    # Group and save individual files
    daily_files = []
    for date, group in df.groupby('date'):
        date_str = date.strftime('%Y-%m-%d')
        daily_file = os.path.join(output_dir, f"ais-{date_str}.csv")
        
        # Remove the temporary date column before saving
        group = group.drop(columns=['date'])
        group.to_csv(daily_file, index=False)
        daily_files.append(os.path.basename(daily_file))
        print(f"  - Created {daily_file}")
    
    # Update metadata file with daily file information
    metadata_file = os.path.join(output_dir, "metadata.txt")
    if os.path.exists(metadata_file):
        with open(metadata_file, 'a') as f:
            f.write("\ndaily_files: [" + ", ".join([f"\"{file}\"" for file in daily_files]) + "]\n")
    
    print(f"Created {len(daily_files)} daily files")
    return [os.path.join(output_dir, file) for file in daily_files]
    
def convert_to_parquet(csv_files):
    """Convert CSV files to Parquet format and save them in a Parquet subdirectory
    
    Args:
        csv_files: List of paths to CSV files to convert
        
    Returns:
        List of paths to created Parquet files
    """
    if not csv_files:
        print("No CSV files to convert to Parquet")
        return []
        
    # Get the directory from the first CSV file
    base_dir = os.path.dirname(csv_files[0])
    
    # Create Parquet subdirectory
    parquet_dir = os.path.join(base_dir, "Parquet")
    os.makedirs(parquet_dir, exist_ok=True)
    print(f"\nCreated Parquet directory: {parquet_dir}")
    
    # Convert each CSV file to Parquet
    parquet_files = []
    for csv_file in csv_files:
        try:
            # Read CSV
            df = pd.read_csv(csv_file)
            
            # Create Parquet filename with same basename but .parquet extension
            basename = os.path.basename(csv_file)
            parquet_basename = os.path.splitext(basename)[0] + ".parquet"
            parquet_file = os.path.join(parquet_dir, parquet_basename)
            
            # Write to Parquet format
            df.to_parquet(parquet_file, engine='pyarrow', index=False)
            
            parquet_files.append(parquet_file)
            print(f"  - Converted {basename} to {parquet_basename}")
        except Exception as e:
            print(f"  - Error converting {os.path.basename(csv_file)}: {str(e)}")
    
    print(f"Created {len(parquet_files)} Parquet files")
    
    # Update metadata file with Parquet file information
    metadata_file = os.path.join(base_dir, "metadata.txt")
    if os.path.exists(metadata_file):
        with open(metadata_file, 'a') as f:
            f.write("\nparquet_files: [" + ", ".join([f"\"{os.path.basename(file)}\"" for file in parquet_files]) + "]\n")
    
    return parquet_files


if __name__ == "__main__":
    print("AIS Shipping Fraud Detection - Test Data Generator")
    print("-" * 50)
    
    df = generate_test_data()
    output_file = save_data(df)
    
    # Split the large CSV file into daily files
    daily_files = split_into_daily_files(output_file)
    
    # Convert daily CSV files to Parquet format
    convert_to_parquet(daily_files)
    
    print("\nDone! Test data created successfully.")

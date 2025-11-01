#!/usr/bin/env python3
"""
Generate sample AIS data for testing the shipping fraud detection system.
This script creates realistic AIS data files with known anomalies.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import argparse

def generate_mmsi():
    """Generate a random valid MMSI number."""
    return random.randint(100000000, 999999999)

def generate_ship_name():
    """Generate a random ship name."""
    prefixes = ["MV", "SS", "MS", "MT"]
    names = ["Horizon", "Voyager", "Serenity", "Poseidon", "Neptune", "Atlantic", 
             "Pacific", "Mariner", "Explorer", "Discovery", "Endeavor", "Pioneer",
             "Nautilus", "Triton", "Oceanic", "Seafarer", "Navigator", "Adventurer"]
    return f"{random.choice(prefixes)} {random.choice(names)}"

def generate_coordinates(base_lat, base_lon, max_distance_deg=1.0):
    """Generate coordinates within a certain distance of a base point."""
    lat = base_lat + random.uniform(-max_distance_deg, max_distance_deg)
    lon = base_lon + random.uniform(-max_distance_deg, max_distance_deg)
    return lat, lon

def generate_timestamp(date, hour_range=(0, 23)):
    """Generate a random timestamp for the given date."""
    hour = random.randint(hour_range[0], hour_range[1])
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return f"{date} {hour:02d}:{minute:02d}:{second:02d}"

def create_ship_data(num_ships, date, ship_type_min=70, ship_type_max=89):
    """Create a dataframe with ship data for a single day."""
    mmsi_list = [generate_mmsi() for _ in range(num_ships)]
    ship_names = [generate_ship_name() for _ in range(num_ships)]
    ship_types = [random.randint(ship_type_min, ship_type_max) for _ in range(num_ships)]
    
    # Base coordinates for different regions
    regions = [
        (40.7128, -74.0060),  # New York
        (51.5074, -0.1278),   # London
        (35.6762, 139.6503),  # Tokyo
        (22.3193, 114.1694),  # Hong Kong
        (1.3521, 103.8198)    # Singapore
    ]
    
    # Assign each ship to a random region
    ship_regions = [random.choice(regions) for _ in range(num_ships)]
    
    # Generate coordinates based on the assigned region
    coordinates = [generate_coordinates(lat, lon, 0.5) for lat, lon in ship_regions]
    latitudes = [coord[0] for coord in coordinates]
    longitudes = [coord[1] for coord in coordinates]
    
    # Generate timestamps
    timestamps = [generate_timestamp(date) for _ in range(num_ships)]
    
    # Generate speeds, headings, and COG
    speeds = [random.uniform(5, 20) for _ in range(num_ships)]
    headings = [random.uniform(0, 359) for _ in range(num_ships)]
    
    # Generate COG values - mostly close to heading but with some anomalies
    cogs = []
    for i in range(num_ships):
        # 10% chance of significant COG-Heading difference (potential anomaly)
        if random.random() < 0.1 and speeds[i] > 10:
            # Generate COG that's significantly different from heading (> 45 degrees)
            diff = random.choice([random.uniform(46, 90), random.uniform(-90, -46)])
            cog = (headings[i] + diff) % 360
        else:
            # Normal case: COG close to heading with small variation
            diff = random.uniform(-20, 20)  # Small variation
            cog = (headings[i] + diff) % 360
        cogs.append(cog)
    
    # Create dataframe
    df = pd.DataFrame({
        'MMSI': mmsi_list,
        'ShipName': ship_names,
        'ShipType': ship_types,
        'Latitude': latitudes,
        'Longitude': longitudes,
        'Timestamp': timestamps,
        'Speed': speeds,
        'Heading': headings,
        'COG': cogs
    })
    
    return df, mmsi_list, ship_names

def create_consecutive_days_data(output_dir, num_days, num_ships_per_day, 
                                 ship_type_min=70, ship_type_max=89,
                                 inject_anomalies=True):
    """
    Create AIS data for consecutive days with optional anomalies.
    
    Args:
        output_dir (str): Directory to save the CSV files
        num_days (int): Number of days to generate data for
        num_ships_per_day (int): Base number of ships per day
        ship_type_min (int): Minimum ship type code
        ship_type_max (int): Maximum ship type code
        inject_anomalies (bool): Whether to inject anomalies into the data
        
    Returns:
        list: Paths to the generated CSV files
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Start date (today - num_days)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=num_days-1)
    
    # Generate data for each day
    file_paths = []
    all_ships = {}  # Track ships across days for continuity
    
    for i in range(num_days):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime('%Y-%m-%d')
        file_path = os.path.join(output_dir, f"{date_str}.csv")
        file_paths.append(file_path)
        
        # Determine number of ships for this day (add some randomness)
        day_num_ships = num_ships_per_day + random.randint(-5, 5)
        
        if i == 0:
            # First day - create all new ships
            df, mmsi_list, ship_names = create_ship_data(
                day_num_ships, date_str, ship_type_min, ship_type_max
            )
            
            # Store ship information for continuity
            for j in range(len(mmsi_list)):
                all_ships[mmsi_list[j]] = {
                    'name': ship_names[j],
                    'type': df.loc[j, 'ShipType'],
                    'lat': df.loc[j, 'Latitude'],
                    'lon': df.loc[j, 'Longitude'],
                    'last_seen': 0  # Day index when last seen
                }
        else:
            # Subsequent days - use some existing ships and add some new ones
            
            # Get ships from previous day
            prev_ships = [mmsi for mmsi, info in all_ships.items() if info['last_seen'] == i-1]
            
            # Determine how many new ships to add
            num_existing = min(len(prev_ships), int(day_num_ships * 0.8))  # Keep up to 80% of previous day's ships
            num_new = day_num_ships - num_existing
            
            # Create data for new ships
            new_df, new_mmsi, new_names = create_ship_data(
                num_new, date_str, ship_type_min, ship_type_max
            )
            
            # Store new ship information
            for j in range(len(new_mmsi)):
                all_ships[new_mmsi[j]] = {
                    'name': new_names[j],
                    'type': new_df.loc[j, 'ShipType'],
                    'lat': new_df.loc[j, 'Latitude'],
                    'lon': new_df.loc[j, 'Longitude'],
                    'last_seen': i  # Current day index
                }
            
            # Create data for existing ships
            existing_mmsi = random.sample(prev_ships, num_existing)
            existing_data = []
            
            for mmsi in existing_mmsi:
                ship = all_ships[mmsi]
                
                # Update last seen
                ship['last_seen'] = i
                
                # Generate new position (with some movement)
                if inject_anomalies and random.random() < 0.05:  # 5% chance of anomalous movement
                    # Anomalous movement - either very far or very little
                    if random.random() < 0.5:
                        # Excessive movement
                        new_lat, new_lon = generate_coordinates(ship['lat'], ship['lon'], 5.0)
                    else:
                        # Almost no movement
                        new_lat, new_lon = generate_coordinates(ship['lat'], ship['lon'], 0.01)
                else:
                    # Normal movement
                    new_lat, new_lon = generate_coordinates(ship['lat'], ship['lon'], 0.5)
                
                # Update stored position
                ship['lat'] = new_lat
                ship['lon'] = new_lon
                
                # Add to existing data
                existing_data.append({
                    'MMSI': mmsi,
                    'ShipName': ship['name'],
                    'ShipType': ship['type'],
                    'Latitude': new_lat,
                    'Longitude': new_lon,
                    'Timestamp': generate_timestamp(date_str),
                    'Speed': random.uniform(5, 20),
                    'Heading': random.uniform(0, 359)
                })
            
            # Combine new and existing data
            if existing_data:
                existing_df = pd.DataFrame(existing_data)
                df = pd.concat([existing_df, new_df], ignore_index=True)
            else:
                df = new_df
            
            # Inject beacon on/off anomalies
            if inject_anomalies:
                # Some ships from previous days might reappear
                if i >= 2 and random.random() < 0.7:  # 70% chance if we're at least on day 3
                    old_ships = [mmsi for mmsi, info in all_ships.items() 
                                if info['last_seen'] < i-1 and info['last_seen'] >= i-3]
                    
                    if old_ships:
                        num_reappear = min(len(old_ships), int(day_num_ships * 0.05))  # Up to 5% reappearing ships
                        if num_reappear > 0:
                            reappear_mmsi = random.sample(old_ships, num_reappear)
                            reappear_data = []
                            
                            for mmsi in reappear_mmsi:
                                ship = all_ships[mmsi]
                                ship['last_seen'] = i  # Update last seen
                                
                                # Generate new position (with significant movement)
                                new_lat, new_lon = generate_coordinates(ship['lat'], ship['lon'], 2.0)
                                ship['lat'] = new_lat
                                ship['lon'] = new_lon
                                
                                reappear_data.append({
                                    'MMSI': mmsi,
                                    'ShipName': ship['name'],
                                    'ShipType': ship['type'],
                                    'Latitude': new_lat,
                                    'Longitude': new_lon,
                                    'Timestamp': generate_timestamp(date_str),
                                    'Speed': random.uniform(5, 20),
                                    'Heading': random.uniform(0, 359)
                                })
                            
                            if reappear_data:
                                reappear_df = pd.DataFrame(reappear_data)
                                df = pd.concat([df, reappear_df], ignore_index=True)
        
        # Save to CSV
        df.to_csv(file_path, index=False)
        print(f"Generated {file_path} with {len(df)} ships")
    
    return file_paths

def main():
    """Main function to parse arguments and generate data."""
    parser = argparse.ArgumentParser(description='Generate sample AIS data for testing')
    parser.add_argument('--output', type=str, default='sample_data',
                        help='Output directory for CSV files')
    parser.add_argument('--days', type=int, default=5,
                        help='Number of days to generate data for')
    parser.add_argument('--ships', type=int, default=100,
                        help='Base number of ships per day')
    parser.add_argument('--no-anomalies', action='store_true',
                        help='Do not inject anomalies into the data')
    
    args = parser.parse_args()
    
    create_consecutive_days_data(
        args.output,
        args.days,
        args.ships,
        inject_anomalies=not args.no_anomalies
    )
    
    print(f"Sample data generation complete. Files saved to {args.output}")

if __name__ == "__main__":
    main()

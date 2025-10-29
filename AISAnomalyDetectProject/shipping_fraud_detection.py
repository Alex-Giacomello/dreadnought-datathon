#!/usr/bin/env python3
"""
AIS Shipping Fraud Detection System

This module implements an anomaly detection system for shipping vessels using AIS data.
It identifies potential fraud patterns by analyzing daily ship movement data and detecting:
1. AIS Beacon Off (ships disappearing from tracking)
2. AIS Beacon On (ships suddenly reappearing)
3. Excessive Travel Distance (both unusually fast and slow movements)

The system is designed to handle large datasets efficiently using Dask for parallel processing
and provides visualization capabilities for detected anomalies.
"""

import os
import argparse
import configparser
import logging
from datetime import datetime, timedelta
import pandas as pd
import dask.dataframe as dd
import numpy as np
from geopy.distance import great_circle
import folium
from folium.plugins import MarkerCluster
import matplotlib.pyplot as plt
import seaborn as sns

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("shipping_fraud_detection.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Required columns for AIS data
REQUIRED_COLUMNS = [
    'MMSI', 'ShipName', 'ShipType', 'Latitude', 'Longitude',
    'Timestamp', 'Speed', 'Heading'
]

def load_config(config_file='config.ini'):
    """
    Load configuration from config.ini file.
    
    Args:
        config_file (str): Path to the configuration file
        
    Returns:
        dict: Configuration parameters
    """
    if not os.path.exists(config_file):
        logger.warning(f"Config file {config_file} not found. Using default values.")
        return {
            'DATA_DIRECTORY': 'C:\\AIS_Data',
            'OUTPUT_DIRECTORY': 'C:\\AIS_Data\\Reports',
            'SHIP_TYPE_MIN': 70,
            'SHIP_TYPE_MAX': 89,
            'MIN_TRAVEL_NM': 200,
            'MAX_TRAVEL_NM': 550,
            'TIMESTAMP_FORMAT': '%Y-%m-%d %H:%M:%S'
        }
    
    config = configparser.ConfigParser()
    config.read(config_file)
    
    return {
        'DATA_DIRECTORY': config['DEFAULT']['DATA_DIRECTORY'],
        'OUTPUT_DIRECTORY': config['DEFAULT'].get('OUTPUT_DIRECTORY', config['DEFAULT']['DATA_DIRECTORY'] + '\\Reports'),
        'SHIP_TYPE_MIN': int(config['SHIP_FILTERS']['SHIP_TYPE_MIN']),
        'SHIP_TYPE_MAX': int(config['SHIP_FILTERS']['SHIP_TYPE_MAX']),
        'MIN_TRAVEL_NM': float(config['ANOMALY_THRESHOLDS']['MIN_TRAVEL_NM']),
        'MAX_TRAVEL_NM': float(config['ANOMALY_THRESHOLDS']['MAX_TRAVEL_NM']),
        'TIMESTAMP_FORMAT': config['TIMESTAMPS']['FORMAT']
    }

def haversine_distance_nm(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the Earth
    (specified in decimal degrees) in nautical miles.
    
    Args:
        lat1 (float): Latitude of point 1
        lon1 (float): Longitude of point 1
        lat2 (float): Latitude of point 2
        lon2 (float): Longitude of point 2
        
    Returns:
        float: Distance in nautical miles
    """
    if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
        return None
    return great_circle((lat1, lon1), (lat2, lon2)).nm

def haversine_vectorized(df):
    """
    Vectorized implementation of the Haversine formula for Dask DataFrames.
    
    Args:
        df (DataFrame): DataFrame with prev_Latitude, prev_Longitude, curr_Latitude, curr_Longitude columns
        
    Returns:
        Series: Distances in nautical miles
    """
    # Convert latitude and longitude from degrees to radians
    lat1_rad = np.radians(df['prev_Latitude'])
    lon1_rad = np.radians(df['prev_Longitude'])
    lat2_rad = np.radians(df['curr_Latitude'])
    lon2_rad = np.radians(df['curr_Longitude'])
    
    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 3440.065  # Radius of earth in nautical miles
    
    return c * r

def get_most_recent_files(data_dir, num_days):
    """
    Identify the most recent AIS .csv files based on their filenames (date).
    Assumes filenames are in YYYY-MM-DD.csv format.
    
    Args:
        data_dir (str): Directory containing AIS data files
        num_days (int): Number of days to analyze
        
    Returns:
        tuple: (list of file paths, list of dates)
    """
    try:
        all_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        dated_files = {}
        
        for f in all_files:
            try:
                date_str = f.replace('.csv', '')
                file_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                dated_files[file_date] = os.path.join(data_dir, f)
            except ValueError:
                logger.warning(f"Skipping malformed filename {f}. Expected YYYY-MM-DD.csv")
                continue
        
        if not dated_files:
            logger.error(f"No valid CSV files found in {data_dir}")
            return [], []
            
        sorted_dates = sorted(dated_files.keys(), reverse=True)
        selected_files = []
        selected_dates = []
        
        for i in range(min(num_days + 1, len(sorted_dates))):
            selected_files.append(dated_files[sorted_dates[i]])
            selected_dates.append(sorted_dates[i])
        
        # Ensure files are in chronological order for processing
        selected_files.reverse()
        selected_dates.reverse()
        
        return selected_files, selected_dates
        
    except Exception as e:
        logger.error(f"Error finding files in {data_dir}: {e}")
        return [], []

def load_and_preprocess_day(file_path, config, use_dask=True):
    """
    Load a single daily CSV, handle errors, and perform initial preprocessing.
    
    Args:
        file_path (str): Path to the CSV file
        config (dict): Configuration parameters
        use_dask (bool): Whether to use Dask for processing
        
    Returns:
        DataFrame or Dask DataFrame: Processed data or None if an error occurs
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        logger.info(f"Loading data from {file_path}")
        
        if use_dask:
            # Use Dask for large files
            df = dd.read_csv(file_path)
            
            # Check for required columns
            missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")
            
            # Select only required columns and filter ship types early
            df = df[REQUIRED_COLUMNS]
            df = df[(df['ShipType'] >= config['SHIP_TYPE_MIN']) & 
                    (df['ShipType'] <= config['SHIP_TYPE_MAX'])]
            
            # Convert Timestamp
            df['Timestamp'] = dd.to_datetime(df['Timestamp'], 
                                           format=config['TIMESTAMP_FORMAT'], 
                                           errors='coerce')
            
            # Ensure numeric types for coordinates and speed
            for col in ['Latitude', 'Longitude', 'Speed', 'Heading']:
                df[col] = dd.to_numeric(df[col], errors='coerce')
            
            # Drop rows with missing essential data
            df = df.dropna(subset=['Timestamp', 'Latitude', 'Longitude', 'MMSI'])
            
            # Add a 'date' column for easy grouping/identification
            df['Date'] = df['Timestamp'].dt.date
            
            # Compute the final result
            return df.compute()
            
        else:
            # Use pandas for smaller files
            df = pd.read_csv(file_path, low_memory=False)
            
            # Check for required columns
            missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")
            
            # Select only required columns and filter ship types early
            df = df[REQUIRED_COLUMNS]
            df = df[(df['ShipType'] >= config['SHIP_TYPE_MIN']) & 
                    (df['ShipType'] <= config['SHIP_TYPE_MAX'])]
            
            # Convert Timestamp
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], 
                                           format=config['TIMESTAMP_FORMAT'], 
                                           errors='coerce')
            
            # Ensure numeric types for coordinates and speed
            for col in ['Latitude', 'Longitude', 'Speed', 'Heading']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Drop rows with missing essential data
            df.dropna(subset=['Timestamp', 'Latitude', 'Longitude', 'MMSI'], inplace=True)
            
            # Add a 'date' column for easy grouping/identification
            df['Date'] = df['Timestamp'].dt.date
            
            return df
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {file_path}")
    except pd.errors.EmptyDataError:
        logger.error(f"Empty CSV file: {file_path}")
    except pd.errors.ParserError:
        logger.error(f"Malformed CSV content: {file_path}")
    except ValueError as e:
        logger.error(f"Error in {file_path}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing {file_path}: {e}")
        
    return None

def create_map_visualization(anomalies_df, output_path):
    """
    Create an interactive map visualization of detected anomalies.
    
    Args:
        anomalies_df (DataFrame): DataFrame containing anomaly data
        output_path (str): Path to save the HTML map
        
    Returns:
        None
    """
    if anomalies_df.empty:
        logger.warning("No anomalies to visualize")
        return
        
    # Create a map centered on the mean coordinates
    center_lat = anomalies_df['Latitude'].mean()
    center_lon = anomalies_df['Longitude'].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=4)
    
    # Add a marker cluster
    marker_cluster = MarkerCluster().add_to(m)
    
    # Add markers for each anomaly
    for _, row in anomalies_df.iterrows():
        # Define color based on anomaly type
        if 'Beacon Off' in row['Type of Anomaly Detected']:
            color = 'red'
            icon = 'times-circle'
        elif 'Beacon On' in row['Type of Anomaly Detected']:
            color = 'blue'
            icon = 'play-circle'
        elif 'Fast' in row['Type of Anomaly Detected']:
            color = 'orange'
            icon = 'bolt'
        else:  # Slow
            color = 'green'
            icon = 'anchor'
            
        # Create popup content
        popup_content = f"""
        <b>Ship:</b> {row['Ship Name']}<br>
        <b>MMSI:</b> {row['MMSI']}<br>
        <b>Anomaly:</b> {row['Type of Anomaly Detected']}<br>
        <b>Date:</b> {row['Date of Anomaly']}<br>
        <b>Position:</b> {row['Latitude']:.4f}, {row['Longitude']:.4f}
        """
        
        # Add marker
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.Icon(color=color, icon=icon, prefix='fa')
        ).add_to(marker_cluster)
    
    # Save the map
    m.save(output_path)
    logger.info(f"Map visualization saved to {output_path}")

def create_summary_charts(anomalies_df, output_dir):
    """
    Create summary charts for anomaly analysis.
    
    Args:
        anomalies_df (DataFrame): DataFrame containing anomaly data
        output_dir (str): Directory to save the charts
        
    Returns:
        None
    """
    if anomalies_df.empty:
        logger.warning("No anomalies to visualize in charts")
        return
        
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Anomaly types distribution
    plt.figure(figsize=(10, 6))
    sns.countplot(x='Type of Anomaly Detected', data=anomalies_df)
    plt.title('Distribution of Anomaly Types')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'anomaly_types_distribution.png'))
    
    # 2. Anomalies by date
    if 'Date of Anomaly' in anomalies_df.columns:
        plt.figure(figsize=(12, 6))
        anomalies_df['Date of Anomaly'] = pd.to_datetime(anomalies_df['Date of Anomaly'])
        date_counts = anomalies_df.groupby([anomalies_df['Date of Anomaly'].dt.date, 'Type of Anomaly Detected']).size().unstack()
        date_counts.plot(kind='bar', stacked=True)
        plt.title('Anomalies by Date')
        plt.xlabel('Date')
        plt.ylabel('Number of Anomalies')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'anomalies_by_date.png'))
    
    logger.info(f"Summary charts saved to {output_dir}")

def detect_shipping_anomalies(num_days_to_analyze, config_file='config.ini', use_dask=True):
    """
    Main function to orchestrate the loading, processing, and anomaly detection.
    
    Args:
        num_days_to_analyze (int): Number of days to analyze
        config_file (str): Path to the configuration file
        use_dask (bool): Whether to use Dask for processing
        
    Returns:
        DataFrame: Detected anomalies
    """
    logger.info(f"Starting AIS Fraud Detection for the last {num_days_to_analyze} days")
    
    # Load configuration
    config = load_config(config_file)
    
    # Create output directory if it doesn't exist
    os.makedirs(config['OUTPUT_DIRECTORY'], exist_ok=True)
    
    # Get file paths
    file_paths, dates_in_order = get_most_recent_files(config['DATA_DIRECTORY'], num_days_to_analyze)
    
    if not file_paths or len(file_paths) <= 1:
        logger.error("Not enough valid daily files found for comparison. Need at least 2 days.")
        return pd.DataFrame()
    
    # Process files day by day for comparisons
    df_previous_day = None
    processed_first_day = False
    all_anomalies = []
    
    for i in range(len(file_paths)):
        current_file_path = file_paths[i]
        current_date = dates_in_order[i]
        logger.info(f"Processing data for: {current_date.strftime('%Y-%m-%d')} ({current_file_path})")
        
        df_current_day = load_and_preprocess_day(current_file_path, config, use_dask)
        
        if df_current_day is None:
            logger.warning(f"Skipping {current_file_path} due to loading errors.")
            df_previous_day = None  # Reset previous day if current fails
            continue
        
        if not processed_first_day:
            df_previous_day = df_current_day
            processed_first_day = True
            logger.info(f"Loaded initial day: {current_date.strftime('%Y-%m-%d')}. No comparisons possible yet.")
            continue  # Skip to the next day for comparisons
        
        # --- ANOMALY DETECTION ---
        anomalies = []
        report_date = current_date.strftime('%Y-%m-%d')
        
        # 1. AIS Beacon Off (No Report)
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
        beacon_on_mmsi = list(mmsi_current_day - mmsi_prev_day)
        if beacon_on_mmsi:
            beacon_on_ships = df_current_day[df_current_day['MMSI'].isin(beacon_on_mmsi)]
            # Get first known position for beacon on
            beacon_on_first_positions = beacon_on_ships.groupby('MMSI').first().reset_index()
            for _, row in beacon_on_first_positions.iterrows():
                anomalies.append({
                    'Date of Anomaly': report_date,
                    'Ship Name': row['ShipName'],
                    'MMSI': row['MMSI'],
                    'Latitude': row['Latitude'],
                    'Longitude': row['Longitude'],
                    'Type of Anomaly Detected': 'AIS Beacon On'
                })
        
        # 3. Excessive Travel Distance
        common_mmsi = list(mmsi_prev_day.intersection(mmsi_current_day))
        
        if common_mmsi:
            # Get the last position from previous day and first position from current day for each MMSI
            df_prev_common = df_previous_day[df_previous_day['MMSI'].isin(common_mmsi)]
            df_prev_common = df_prev_common.sort_values('Timestamp').groupby('MMSI').last().reset_index()
            
            df_curr_common = df_current_day[df_current_day['MMSI'].isin(common_mmsi)]
            df_curr_common = df_curr_common.sort_values('Timestamp').groupby('MMSI').first().reset_index()
            
            # Merge to get previous and current positions side-by-side
            merged_df = pd.merge(
                df_prev_common[['MMSI', 'Latitude', 'Longitude', 'ShipName']],
                df_curr_common[['MMSI', 'Latitude', 'Longitude']],
                on='MMSI',
                suffixes=('_prev', '_curr')
            )
            
            # Calculate distance using vectorized Haversine
            if use_dask and len(merged_df) > 10000:  # Only use Dask for large datasets
                ddf = dd.from_pandas(merged_df, npartitions=max(1, len(merged_df) // 10000))
                ddf['Distance_NM'] = ddf.map_partitions(haversine_vectorized)
                merged_df = ddf.compute()
            else:
                # Use apply for smaller datasets
                merged_df['Distance_NM'] = merged_df.apply(
                    lambda row: haversine_distance_nm(
                        row['Latitude_prev'], row['Longitude_prev'],
                        row['Latitude_curr'], row['Longitude_curr']
                    ), axis=1
                )
            
            # Flag based on distance
            fast_travel_ships = merged_df[merged_df['Distance_NM'] > config['MAX_TRAVEL_NM']]
            slow_travel_ships = merged_df[merged_df['Distance_NM'] < config['MIN_TRAVEL_NM']]
            
            for _, row in fast_travel_ships.iterrows():
                anomalies.append({
                    'Date of Anomaly': report_date,
                    'Ship Name': row['ShipName'],
                    'MMSI': row['MMSI'],
                    'Latitude': row['Latitude_curr'],
                    'Longitude': row['Longitude_curr'],
                    'Type of Anomaly Detected': f'Excessive Travel Distance (Fast): {row["Distance_NM"]:.1f} NM'
                })
            
            for _, row in slow_travel_ships.iterrows():
                anomalies.append({
                    'Date of Anomaly': report_date,
                    'Ship Name': row['ShipName'],
                    'MMSI': row['MMSI'],
                    'Latitude': row['Latitude_curr'],
                    'Longitude': row['Longitude_curr'],
                    'Type of Anomaly Detected': f'Excessive Travel Distance (Slow): {row["Distance_NM"]:.1f} NM'
                })
        
        # --- Output Report for the Current Day ---
        if anomalies:
            anomalies_df = pd.DataFrame(anomalies)
            all_anomalies.extend(anomalies)
            
            # Save CSV report
            output_filename = f"Report for {report_date}.csv"
            output_path = os.path.join(config['OUTPUT_DIRECTORY'], output_filename)
            anomalies_df.to_csv(output_path, index=False)
            logger.info(f"Generated anomaly report: {output_path} with {len(anomalies)} anomalies.")
            
            # Create map visualization
            map_filename = f"Map for {report_date}.html"
            map_path = os.path.join(config['OUTPUT_DIRECTORY'], map_filename)
            create_map_visualization(anomalies_df, map_path)
        else:
            logger.info(f"No anomalies detected for {report_date}.")
        
        # Prepare for the next iteration
        df_previous_day = df_current_day
    
    # Create summary report and visualizations if we have anomalies
    if all_anomalies:
        all_anomalies_df = pd.DataFrame(all_anomalies)
        summary_path = os.path.join(config['OUTPUT_DIRECTORY'], "Summary Report.csv")
        all_anomalies_df.to_csv(summary_path, index=False)
        
        # Create summary charts
        charts_dir = os.path.join(config['OUTPUT_DIRECTORY'], "Charts")
        create_summary_charts(all_anomalies_df, charts_dir)
        
        # Create overall map
        overall_map_path = os.path.join(config['OUTPUT_DIRECTORY'], "All Anomalies Map.html")
        create_map_visualization(all_anomalies_df, overall_map_path)
        
        logger.info(f"AIS Fraud Detection Complete. Found {len(all_anomalies)} anomalies across {num_days_to_analyze} days.")
        return all_anomalies_df
    else:
        logger.info(f"AIS Fraud Detection Complete. No anomalies detected.")
        return pd.DataFrame()

def main():
    """
    Main entry point for the script.
    """
    parser = argparse.ArgumentParser(description='AIS Shipping Fraud Detection System')
    parser.add_argument('--days', type=int, default=5, help='Number of days to analyze')
    parser.add_argument('--config', type=str, default='config.ini', help='Path to configuration file')
    parser.add_argument('--no-dask', action='store_true', help='Disable Dask processing for large files')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Run anomaly detection
    detect_shipping_anomalies(args.days, args.config, not args.no_dask)

if __name__ == "__main__":
    main()

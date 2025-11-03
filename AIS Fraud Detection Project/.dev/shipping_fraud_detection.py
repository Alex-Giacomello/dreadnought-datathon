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
import glob
import argparse
import configparser
import logging
from datetime import datetime, timedelta
import boto3
import botocore.exceptions
from urllib.parse import urlparse
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
    'MMSI', 'VesselName', 'VesselType', 'LAT', 'LON',
    'BaseDateTime', 'SOG', 'Heading', 'COG'
]

def normalize_angle_difference(angle_diff):
    """
    Normalize angle difference to be between -180 and 180 degrees.
    
    Args:
        angle_diff (float): Angle difference in degrees
        
    Returns:
        float: Normalized angle difference
    """
    # Ensure the angle is between -180 and 180 degrees
    while angle_diff > 180:
        angle_diff -= 360
    while angle_diff < -180:
        angle_diff += 360
    return angle_diff

def is_s3_uri(path):
    """
    Check if the given path is an S3 URI.
    
    Args:
        path (str): Path to check
        
    Returns:
        bool: True if the path is an S3 URI, False otherwise
    """
    return path.startswith('s3://')

def parse_s3_uri(uri):
    """
    Parse an S3 URI into bucket name and prefix.
    
    Args:
        uri (str): S3 URI to parse
        
    Returns:
        tuple: (bucket_name, prefix)
    """
    parsed = urlparse(uri)
    bucket = parsed.netloc
    prefix = parsed.path.lstrip('/')
    return bucket, prefix

def list_s3_files_by_date_range(s3_uri, start_date, end_date):
    """
    Get AIS data files from S3 for a specific date range based on their filenames.
    Supports both .csv and .parquet files with filenames in YYYY-MM-DD format.
    
    Args:
        s3_uri (str): S3 URI pointing to the folder with AIS data files
        start_date (datetime.date): Start date (inclusive)
        end_date (datetime.date): End date (inclusive)
        
    Returns:
        tuple: (list of file paths, list of dates)
    """
    try:
        bucket_name, prefix = parse_s3_uri(s3_uri)
        
        # Create an S3 client
        s3 = boto3.client('s3')
        
        # Make sure prefix ends with a slash
        if prefix and not prefix.endswith('/'):
            prefix += '/'
        
        # List objects in the bucket with the given prefix
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        
        if 'Contents' not in response:
            logger.warning(f"No files found in S3 bucket {bucket_name} with prefix {prefix}")
            return [], []
        
        dated_files = {}
        
        for item in response['Contents']:
            key = item['Key']
            filename = os.path.basename(key)
            
            # Skip if the file doesn't have an extension
            if '.' not in filename:
                continue
                
            file_ext = os.path.splitext(filename)[1].lower()  # Get lowercase extension
            if file_ext not in ['.csv', '.parquet']:
                continue
                
            file_name_without_ext = filename.replace(file_ext, '')  # Remove file extension
            
            # Check if filename has 'ais-' prefix
            if file_name_without_ext.startswith('ais-'):
                date_str = file_name_without_ext[4:]  # Skip 'ais-' prefix
            else:
                date_str = file_name_without_ext
                
            try:
                file_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                dated_files[file_date] = f"s3://{bucket_name}/{key}"
            except ValueError:
                logger.warning(f"Skipping malformed filename {filename}. Expected ais-YYYY-MM-DD{file_ext} or YYYY-MM-DD{file_ext}")
                continue
        
        if not dated_files:
            logger.error(f"No valid data files found in S3 bucket {bucket_name} with prefix {prefix}")
            return [], []
        
        # Select files within the date range
        selected_files = []
        selected_dates = []
        
        for file_date, file_path in sorted(dated_files.items()):
            if start_date <= file_date <= end_date:
                selected_files.append(file_path)
                selected_dates.append(file_date)
        
        if not selected_files:
            logger.warning(f"No files found in date range {start_date} to {end_date}")
            
        return selected_files, selected_dates
            
    except botocore.exceptions.NoCredentialsError:
        logger.error("AWS credentials not found. Please configure AWS credentials.")
        return [], []
    except botocore.exceptions.ClientError as e:
        logger.error(f"Error accessing S3: {e}")
        return [], []
    except Exception as e:
        logger.error(f"Error finding files in S3 bucket: {e}")
        return [], []

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
            'COG_HEADING_MAX_DIFF': 45,
            'MIN_SPEED_FOR_COG_CHECK': 10,
            'DATA_DIRECTORY': 'C:\\AIS_Data',
            'OUTPUT_DIRECTORY': 'C:\\AIS_Data\\Reports',
            'SELECTED_SHIP_TYPES': [70, 80],  # Default to cargo and tanker main types
            'MIN_TRAVEL_NM': 200,
            'MAX_TRAVEL_NM': 550,
            'TIMESTAMP_FORMAT': '%Y-%m-%d %H:%M:%S',
            'DETECT_BEACON_OFF': True,
            'DETECT_BEACON_ON': True,
            'DETECT_FAST_TRAVEL': True,
            'DETECT_SLOW_TRAVEL': True,
            'DETECT_COG_HEADING': True
        }
    
    config = configparser.ConfigParser()
    config.read(config_file)
    
    result = {
        'COG_HEADING_MAX_DIFF': float(config['ANOMALY_THRESHOLDS'].get('COG_HEADING_MAX_DIFF', 45)),
        'MIN_SPEED_FOR_COG_CHECK': float(config['ANOMALY_THRESHOLDS'].get('MIN_SPEED_FOR_COG_CHECK', 10)),
        'DATA_DIRECTORY': config['DEFAULT']['DATA_DIRECTORY'],
        'OUTPUT_DIRECTORY': config['DEFAULT'].get('OUTPUT_DIRECTORY', config['DEFAULT']['DATA_DIRECTORY'] + '\\Reports'),
        'MIN_TRAVEL_NM': float(config['ANOMALY_THRESHOLDS']['MIN_TRAVEL_NM']),
        'MAX_TRAVEL_NM': float(config['ANOMALY_THRESHOLDS']['MAX_TRAVEL_NM']),
        'TIMESTAMP_FORMAT': config.get('TIMESTAMPS', {}).get('FORMAT', '%Y-%m-%d %H:%M:%S').replace('%%', '%') if 'TIMESTAMPS' in config else '%Y-%m-%d %H:%M:%S',
        'USE_S3': config.get('S3_SETTINGS', {}).getboolean('USE_S3', False) if 'S3_SETTINGS' in config else False,
        'S3_DATA_URI': config.get('S3_SETTINGS', {}).get('S3_DATA_URI', '') if 'S3_SETTINGS' in config else ''
    }
    
    # Load selected ship types
    if 'SHIP_FILTERS' in config and 'SELECTED_SHIP_TYPES' in config['SHIP_FILTERS']:
        selected_types_str = config['SHIP_FILTERS']['SELECTED_SHIP_TYPES']
        try:
            # Parse comma-separated ship types
            result['SELECTED_SHIP_TYPES'] = [int(t.strip()) for t in selected_types_str.split(',') if t.strip()]
        except ValueError:
            logger.warning("Invalid ship type values in config. Using default cargo and tanker types.")
            result['SELECTED_SHIP_TYPES'] = [70, 80]  # Default to cargo and tanker main types
    else:
        # For backward compatibility with older config files
        if 'SHIP_FILTERS' in config and 'SHIP_TYPE_MIN' in config['SHIP_FILTERS'] and 'SHIP_TYPE_MAX' in config['SHIP_FILTERS']:
            min_type = int(config['SHIP_FILTERS']['SHIP_TYPE_MIN'])
            max_type = int(config['SHIP_FILTERS']['SHIP_TYPE_MAX'])
            result['SELECTED_SHIP_TYPES'] = list(range(min_type, max_type + 1))
        else:
            # Default to all cargo and tanker types if not specified
            result['SELECTED_SHIP_TYPES'] = list(range(70, 90))  # 70-89 inclusive
    
    # Load anomaly detection flags if present
    if 'ANOMALY_TYPES' in config:
        result['DETECT_BEACON_OFF'] = config['ANOMALY_TYPES'].getboolean('AIS_Beacon_Off', True)
        result['DETECT_BEACON_ON'] = config['ANOMALY_TYPES'].getboolean('AIS_Beacon_On', True)
        result['DETECT_FAST_TRAVEL'] = config['ANOMALY_TYPES'].getboolean('Excessive_Travel_Distance_Fast', True)
        result['DETECT_SLOW_TRAVEL'] = config['ANOMALY_TYPES'].getboolean('Excessive_Travel_Distance_Slow', True)
        result['DETECT_COG_HEADING'] = config['ANOMALY_TYPES'].getboolean('COG-Heading_Inconsistency', True)
    else:
        # Default to detecting all anomaly types
        result['DETECT_BEACON_OFF'] = True
        result['DETECT_BEACON_ON'] = True
        result['DETECT_FAST_TRAVEL'] = True
        result['DETECT_SLOW_TRAVEL'] = True
        result['DETECT_COG_HEADING'] = True
    
    return result

def haversine_distance_nm(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the Earth
    (specified in decimal degrees) in nautical miles.
    
    Args:
        lat1 (float): LAT of point 1
        lon1 (float): LON of point 1
        lat2 (float): LAT of point 2
        lon2 (float): LON of point 2
        
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
        df (DataFrame): DataFrame with prev_LAT, prev_LON, curr_LAT, curr_LON columns
        
    Returns:
        Series: Distances in nautical miles
    """
    # Convert latitude and longitude from degrees to radians
    lat1_rad = np.radians(df['prev_LAT'])
    lon1_rad = np.radians(df['prev_LON'])
    lat2_rad = np.radians(df['curr_LAT'])
    lon2_rad = np.radians(df['curr_LON'])
    
    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 3440.065  # Radius of earth in nautical miles
    
    return c * r

def get_files_for_date_range(data_dir, start_date, end_date):
    """
    Get AIS data files for a specific date range based on their filenames.
    Supports both .csv and .parquet files with filenames in YYYY-MM-DD format.
    Also supports S3 URIs for cloud storage.
    
    Args:
        data_dir (str): Directory containing AIS data files or S3 URI
        start_date (datetime.date): Start date (inclusive)
        end_date (datetime.date): End date (inclusive)
        
    Returns:
        tuple: (list of file paths, list of dates)
    """
    try:
        # Check if the data_dir is an S3 URI
        if is_s3_uri(data_dir):
            # Use S3-specific function to get files
            return list_s3_files_by_date_range(data_dir, start_date, end_date)
            
        # Local filesystem handling
        # Look for both CSV and Parquet files
        csv_pattern = os.path.join(data_dir, "*.csv")
        parquet_pattern = os.path.join(data_dir, "*.parquet")
        
        csv_files = glob.glob(csv_pattern)
        parquet_files = glob.glob(parquet_pattern)
        
        all_files = csv_files + parquet_files
        dated_files = {}
        
        for f in all_files:
            try:
                base_name = os.path.basename(f)
                file_ext = os.path.splitext(base_name)[1].lower()  # Get lowercase extension
                file_name_without_ext = base_name.replace(file_ext, '')  # Remove file extension
                
                # Check if filename has 'ais-' prefix
                if file_name_without_ext.startswith('ais-'):
                    date_str = file_name_without_ext[4:]  # Skip 'ais-' prefix
                else:
                    date_str = file_name_without_ext
                    
                file_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                dated_files[file_date] = f
            except ValueError:
                logger.warning(f"Skipping malformed filename {f}. Expected ais-YYYY-MM-DD{file_ext} or YYYY-MM-DD{file_ext}")
                continue
        
        if not dated_files:
            logger.error(f"No valid data files found in {data_dir}")
            return [], []
        
        # Select files within the date range
        selected_files = []
        selected_dates = []
        
        for file_date, file_path in sorted(dated_files.items()):
            if start_date <= file_date <= end_date:
                selected_files.append(file_path)
                selected_dates.append(file_date)
        
        if not selected_files:
            logger.warning(f"No files found in date range {start_date} to {end_date}")
            
        return selected_files, selected_dates
            
    except Exception as e:
        logger.error(f"Error finding files in {data_dir}: {e}")
        return [], []

def get_most_recent_files(data_dir, num_days):
    """
    Identify the most recent AIS data files based on their filenames (date).
    Supports both .csv and .parquet files with filenames in YYYY-MM-DD format.
    Also supports S3 URIs for cloud storage.
    
    Args:
        data_dir (str): Directory containing AIS data files or S3 URI
        num_days (int): Number of days to analyze
        
    Returns:
        tuple: (list of file paths, list of dates)
    """
    try:
        # Check if the data_dir is an S3 URI
        if is_s3_uri(data_dir):
            # For S3, we need to list all files and then filter by date
            bucket_name, prefix = parse_s3_uri(data_dir)
            s3 = boto3.client('s3')
            
            # Make sure prefix ends with a slash
            if prefix and not prefix.endswith('/'):
                prefix += '/'
            
            # List objects in the bucket with the given prefix
            response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            
            if 'Contents' not in response:
                logger.warning(f"No files found in S3 bucket {bucket_name} with prefix {prefix}")
                return [], []
            
            # Process all files to extract dates
            all_dated_files = {}
            
            for item in response['Contents']:
                key = item['Key']
                filename = os.path.basename(key)
                
                # Skip if the file doesn't have an extension
                if '.' not in filename:
                    continue
                    
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext not in ['.csv', '.parquet']:
                    continue
                    
                file_name_without_ext = filename.replace(file_ext, '')
                
                # Check if filename has 'ais-' prefix
                if file_name_without_ext.startswith('ais-'):
                    date_str = file_name_without_ext[4:]
                else:
                    date_str = file_name_without_ext
                
                try:
                    file_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    all_dated_files[file_date] = f"s3://{bucket_name}/{key}"
                except ValueError:
                    continue
            
            if not all_dated_files:
                logger.error(f"No valid data files found in S3 bucket {bucket_name} with prefix {prefix}")
                return [], []
                
            # Get the most recent date
            sorted_dates = sorted(all_dated_files.keys(), reverse=True)
            if not sorted_dates:
                return [], []
                
            end_date = sorted_dates[0]
            start_date = end_date - timedelta(days=num_days)
            
            # Filter files within date range
            selected_files = []
            selected_dates = []
            
            for date, path in all_dated_files.items():
                if start_date <= date <= end_date:
                    selected_files.append(path)
                    selected_dates.append(date)
                    
            return sorted(zip(selected_files, selected_dates), key=lambda x: x[1])
            
        # Local file system handling
        # Look for both CSV and Parquet files
        csv_pattern = os.path.join(data_dir, "*.csv")
        parquet_pattern = os.path.join(data_dir, "*.parquet")
        
        csv_files = glob.glob(csv_pattern)
        parquet_files = glob.glob(parquet_pattern)
        
        all_files = csv_files + parquet_files
        dated_files = {}
        
        for f in all_files:
            try:
                base_name = os.path.basename(f)
                file_ext = os.path.splitext(base_name)[1].lower()  # Get lowercase extension
                file_name_without_ext = base_name.replace(file_ext, '')  # Remove file extension
                
                # Check if filename has 'ais-' prefix
                if file_name_without_ext.startswith('ais-'):
                    date_str = file_name_without_ext[4:]  # Skip 'ais-' prefix
                else:
                    date_str = file_name_without_ext
                    
                file_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                dated_files[file_date] = f
            except ValueError:
                logger.warning(f"Skipping malformed filename {f}. Expected ais-YYYY-MM-DD{file_ext} or YYYY-MM-DD{file_ext}")
                continue
        
        if not dated_files:
            logger.error(f"No valid data files found in {data_dir}")
            return [], []
            
        sorted_dates = sorted(dated_files.keys(), reverse=True)
        selected_files = []
        selected_dates = []
        
        # Get files from the most recent days
        end_date = sorted_dates[0]  # Most recent date
        start_date = end_date - timedelta(days=num_days)  # Calculate start date based on num_days
        
        logger.info(f"Selecting files between {start_date} and {end_date}")
        
        # Get files in the calculated date range
        return get_files_for_date_range(data_dir, start_date, end_date)
        
    except Exception as e:
        logger.error(f"Error finding files in {data_dir}: {e}")
        return [], []

def load_and_preprocess_day(file_path, config, use_dask=True):
    """
    Load a single daily CSV or Parquet file, handle errors, and perform initial preprocessing.
    
    Args:
        file_path (str): Path to the CSV or Parquet file
        config (dict): Configuration parameters
        use_dask (bool): Whether to use Dask for processing
        
    Returns:
        DataFrame or Dask DataFrame: Processed data or None if an error occurs
    """
    try:
        # Skip file existence check for S3 URIs - we'll let pandas/dask handle errors
        if not is_s3_uri(file_path) and not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        logger.info(f"Loading data from {file_path}")
        file_ext = os.path.splitext(file_path)[1].lower()
        is_parquet = file_ext == '.parquet'
        
        if use_dask:
            # Use Dask for large files
            if is_s3_uri(file_path):
                if is_parquet:
                    df = dd.read_parquet(file_path)
                else:  # Default to CSV
                    # Handle the 'anomaly' column as object type to avoid conversion errors
                    df = dd.read_csv(file_path, dtype={'anomaly': 'object'}, storage_options={'anon': False})
            else:  # Local filesystem
                if is_parquet:
                    df = dd.read_parquet(file_path)
                else:  # Default to CSV
                    # Handle the 'anomaly' column as object type to avoid conversion errors
                    df = dd.read_csv(file_path, dtype={'anomaly': 'object'})
            
            # Check for required columns
            missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")
            
            # Select only required columns
            df = df[REQUIRED_COLUMNS]
            
            # Filter by selected ship types
            if 'SELECTED_SHIP_TYPES' in config and config['SELECTED_SHIP_TYPES']:
                df = df[df['VesselType'].isin(config['SELECTED_SHIP_TYPES'])]
            
            # Convert BaseDateTime
            df['BaseDateTime'] = dd.to_datetime(df['BaseDateTime'], 
                                           format=config['TIMESTAMP_FORMAT'], 
                                           errors='coerce')
            
            # Ensure numeric types for coordinates, speed, heading, and COG
            for col in ['LAT', 'LON', 'SOG', 'Heading', 'COG']:
                df[col] = dd.to_numeric(df[col], errors='coerce')
            
            # Only drop rows with missing MMSI as it's the primary identifier
            # Keep rows with other null values for analysis
            df = df.dropna(subset=['MMSI'])
            
            # Add a 'date' column for easy grouping/identification
            df['Date'] = df['BaseDateTime'].dt.date
            
            # Compute the final result
            return df.compute()
            
        else:
            # Use pandas for smaller files
            if is_s3_uri(file_path):
                if is_parquet:
                    df = pd.read_parquet(file_path, storage_options={'anon': False})
                else:  # Default to CSV
                    df = pd.read_csv(file_path, low_memory=False, dtype={'anomaly': 'object'}, storage_options={'anon': False})
            else:  # Local filesystem
                if is_parquet:
                    df = pd.read_parquet(file_path)
                else:  # Default to CSV
                    df = pd.read_csv(file_path, low_memory=False, dtype={'anomaly': 'object'})
            
            # Check for required columns
            missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")
            
            # Select only required columns
            df = df[REQUIRED_COLUMNS]
            
            # Filter by selected ship types
            if 'SELECTED_SHIP_TYPES' in config and config['SELECTED_SHIP_TYPES']:
                df = df[df['VesselType'].isin(config['SELECTED_SHIP_TYPES'])]
            
            # Convert BaseDateTime
            df['BaseDateTime'] = pd.to_datetime(df['BaseDateTime'], 
                                           format=config['TIMESTAMP_FORMAT'], 
                                           errors='coerce')
            
            # Ensure numeric types for coordinates, speed, heading, and COG
            for col in ['LAT', 'LON', 'SOG', 'Heading', 'COG']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Only drop rows with missing MMSI as it's the primary identifier
            # Keep rows with other null values for analysis
            df.dropna(subset=['MMSI'], inplace=True)
            
            # Add a 'date' column for easy grouping/identification
            df['Date'] = df['BaseDateTime'].dt.date
            
            return df
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {file_path}")
    except pd.errors.EmptyDataError:
        logger.error(f"Empty data file: {file_path}")
    except pd.errors.ParserError:
        logger.error(f"Malformed file content: {file_path}")
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
    center_lat = anomalies_df['LAT'].mean()
    center_lon = anomalies_df['LON'].mean()
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
        elif 'Slow' in row['Type of Anomaly Detected']:
            color = 'green'
            icon = 'anchor'
        elif 'COG-Heading' in row['Type of Anomaly Detected']:
            color = 'purple'
            icon = 'compass'
        elif 'Null Value' in row['Type of Anomaly Detected']:
            color = 'black'
            icon = 'exclamation-triangle'
            
        # Create popup content
        popup_content = f"""
        <b>Ship:</b> {row['Ship Name']}<br>
        <b>MMSI:</b> {row['MMSI']}<br>
        <b>Anomaly:</b> {row['Type of Anomaly Detected']}<br>
        <b>Date:</b> {row['Date of Anomaly']}<br>
        <b>Position:</b> {row['LAT']:.4f}, {row['LON']:.4f}
        """
        
        # Add marker
        folium.Marker(
            location=[row['LAT'], row['LON']],
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

def detect_shipping_anomalies_by_date_range(start_date, end_date, config_input='config.ini', use_dask=True):
    """
    Main function to orchestrate the loading, processing, and anomaly detection using date range.
    
    Args:
        start_date (datetime.date or str): Start date (inclusive) - can be string in format YYYY-MM-DD
        end_date (datetime.date or str): End date (inclusive) - can be string in format YYYY-MM-DD
        config_input (str or dict): Path to configuration file or config dictionary
        use_dask (bool): Whether to use Dask for processing
        
    Returns:
        DataFrame: Detected anomalies
    """
    # Convert string dates to datetime.date objects if needed
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    logger.info(f"Starting AIS Fraud Detection for date range {start_date} to {end_date}")
    
    # Load configuration if needed
    if isinstance(config_input, dict):
        config = config_input
    else:
        config = load_config(config_input)
    
    # Create output directory if it doesn't exist
    os.makedirs(config['OUTPUT_DIRECTORY'], exist_ok=True)
    
    # Get file paths for the date range
    file_paths, dates_in_order = get_files_for_date_range(config['DATA_DIRECTORY'], start_date, end_date)
    
    return _process_anomaly_detection(file_paths, dates_in_order, config, use_dask)

def detect_shipping_anomalies(num_days_to_analyze, config_input='config.ini', use_dask=True):
    """
    Main function to orchestrate the loading, processing, and anomaly detection using days back from today.
    
    Args:
        num_days_to_analyze (int): Number of days to analyze
        config_input (str or dict): Path to configuration file or config dictionary
        use_dask (bool): Whether to use Dask for processing
        
    Returns:
        DataFrame: Detected anomalies
    """
    logger.info(f"Starting AIS Fraud Detection for the last {num_days_to_analyze} days")
    
    # Load configuration if needed
    if isinstance(config_input, dict):
        config = config_input
    else:
        config = load_config(config_input)
    
    # Create output directory if it doesn't exist
    os.makedirs(config['OUTPUT_DIRECTORY'], exist_ok=True)
    
    # Get file paths for most recent days
    file_paths, dates_in_order = get_most_recent_files(config['DATA_DIRECTORY'], num_days_to_analyze)
    
    return _process_anomaly_detection(file_paths, dates_in_order, config, use_dask)

def _process_anomaly_detection(file_paths, dates_in_order, config, use_dask=True):
    """
    Internal function that handles the actual anomaly detection process.
    
    Args:
        file_paths (list): List of file paths to process
        dates_in_order (list): List of dates corresponding to file_paths
        config (dict): Configuration dictionary
        use_dask (bool): Whether to use Dask for processing
        
    Returns:
        DataFrame: Detected anomalies
    """
    
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
        
        # Check for null values in critical fields and report them as anomalies
        null_value_columns = ['LAT', 'LON', 'SOG', 'Heading', 'COG']
        for col in null_value_columns:
            if col in df_current_day.columns:
                # Find ships with null values in this column
                null_ships = df_current_day[df_current_day[col].isnull()]
                if not null_ships.empty:
                    # Group by MMSI to get one entry per ship
                    null_ships = null_ships.groupby('MMSI').first().reset_index()
                    
                    for _, row in null_ships.iterrows():
                        # Use non-null values for coordinates if available, otherwise use 0,0
                        lat = row['LAT'] if not pd.isna(row['LAT']) else 0
                        lon = row['LON'] if not pd.isna(row['LON']) else 0
                        
                        anomalies.append({
                            'Date of Anomaly': report_date,
                            'Ship Name': row['VesselName'],
                            'MMSI': row['MMSI'],
                            'LAT': lat,
                            'LON': lon,
                            'Type of Anomaly Detected': f'Null Value in {col}'
                        })
        
        # 0. COG-Heading Inconsistency (for current day only)
        # Check if COG and Heading are not within 90 degrees (45 degrees port or starboard of heading)
        # and ship speed is greater than 10 knots
        if config.get('DETECT_COG_HEADING', True) and 'COG' in df_current_day.columns:
            # Filter for ships with speed > MIN_SPEED_FOR_COG_CHECK
            high_speed_ships = df_current_day[df_current_day['SOG'] >= config['MIN_SPEED_FOR_COG_CHECK']]
            
            if not high_speed_ships.empty:
                # Calculate absolute difference between COG and Heading
                high_speed_ships['angle_diff'] = (high_speed_ships['COG'] - high_speed_ships['Heading']).apply(normalize_angle_difference).abs()
                
                # Find ships where the difference exceeds the threshold
                cog_heading_anomalies = high_speed_ships[high_speed_ships['angle_diff'] > config['COG_HEADING_MAX_DIFF']]
                
                # Group by MMSI to get one entry per ship
                if not cog_heading_anomalies.empty:
                    cog_heading_anomalies = cog_heading_anomalies.sort_values('angle_diff', ascending=False).groupby('MMSI').first().reset_index()
                    
                    for _, row in cog_heading_anomalies.iterrows():
                        anomalies.append({
                            'Date of Anomaly': report_date,
                            'Ship Name': row['VesselName'],
                            'MMSI': row['MMSI'],
                            'LAT': row['LAT'],
                            'LON': row['LON'],
                            'Type of Anomaly Detected': f'COG-Heading Inconsistency: {row["angle_diff"]:.1f}° (COG: {row["COG"]:.1f}°, Heading: {row["Heading"]:.1f}°)'
                        })
        
        # 1. AIS Beacon Off (No Report)
        mmsi_prev_day = set(df_previous_day['MMSI'].unique())
        mmsi_current_day = set(df_current_day['MMSI'].unique())
        
        if config.get('DETECT_BEACON_OFF', True):
            beacon_off_mmsi = list(mmsi_prev_day - mmsi_current_day)
            if beacon_off_mmsi:
                beacon_off_ships = df_previous_day[df_previous_day['MMSI'].isin(beacon_off_mmsi)]
                # Get last known position for beacon off
                beacon_off_last_positions = beacon_off_ships.groupby('MMSI').last().reset_index()
                for _, row in beacon_off_last_positions.iterrows():
                    anomalies.append({
                        'Date of Anomaly': report_date,
                        'Ship Name': row['VesselName'],
                        'MMSI': row['MMSI'],
                        'LAT': row['LAT'],
                        'LON': row['LON'],
                        'Type of Anomaly Detected': 'AIS Beacon Off'
                    })
        
        # 2. AIS Beacon On (Sudden Reappearance)
        if config.get('DETECT_BEACON_ON', True):
            beacon_on_mmsi = list(mmsi_current_day - mmsi_prev_day)
            if beacon_on_mmsi:
                beacon_on_ships = df_current_day[df_current_day['MMSI'].isin(beacon_on_mmsi)]
                # Get first known position for beacon on
                beacon_on_first_positions = beacon_on_ships.groupby('MMSI').first().reset_index()
                for _, row in beacon_on_first_positions.iterrows():
                    anomalies.append({
                        'Date of Anomaly': report_date,
                        'Ship Name': row['VesselName'],
                        'MMSI': row['MMSI'],
                        'LAT': row['LAT'],
                        'LON': row['LON'],
                        'Type of Anomaly Detected': 'AIS Beacon On'
                    })
        
        # 3. Excessive Travel Distance
        common_mmsi = list(mmsi_prev_day.intersection(mmsi_current_day))
        
        if common_mmsi:
            # Get the last position from previous day and first position from current day for each MMSI
            df_prev_common = df_previous_day[df_previous_day['MMSI'].isin(common_mmsi)]
            df_prev_common = df_prev_common.sort_values('BaseDateTime').groupby('MMSI').last().reset_index()
            
            df_curr_common = df_current_day[df_current_day['MMSI'].isin(common_mmsi)]
            df_curr_common = df_curr_common.sort_values('BaseDateTime').groupby('MMSI').first().reset_index()
            
            # Merge to get previous and current positions side-by-side
            merged_df = pd.merge(
                df_prev_common[['MMSI', 'LAT', 'LON', 'VesselName']],
                df_curr_common[['MMSI', 'LAT', 'LON']],
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
                        row['LAT_prev'], row['LON_prev'],
                        row['LAT_curr'], row['LON_curr']
                    ), axis=1
                )
            
            # Flag based on distance
            if config.get('DETECT_FAST_TRAVEL', True):
                fast_travel_ships = merged_df[merged_df['Distance_NM'] > config['MAX_TRAVEL_NM']]
                for _, row in fast_travel_ships.iterrows():
                    anomalies.append({
                        'Date of Anomaly': report_date,
                        'Ship Name': row['VesselName'],
                        'MMSI': row['MMSI'],
                        'LAT': row['LAT_curr'],
                        'LON': row['LON_curr'],
                        'Type of Anomaly Detected': f'Excessive Travel Distance (Fast): {row["Distance_NM"]:.1f} NM'
                    })
            
            if config.get('DETECT_SLOW_TRAVEL', True):
                slow_travel_ships = merged_df[merged_df['Distance_NM'] < config['MIN_TRAVEL_NM']]
                for _, row in slow_travel_ships.iterrows():
                    anomalies.append({
                        'Date of Anomaly': report_date,
                        'Ship Name': row['VesselName'],
                        'MMSI': row['MMSI'],
                        'LAT': row['LAT_curr'],
                        'LON': row['LON_curr'],
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
        
        logger.info(f"AIS Fraud Detection Complete. Found {len(all_anomalies)} anomalies across {len(dates_in_order)} days.")
        return all_anomalies_df
    else:
        logger.info(f"AIS Fraud Detection Complete. No anomalies detected.")
        return pd.DataFrame()

def main():
    """
    Main entry point for the script.
    """
    parser = argparse.ArgumentParser(description='AIS Shipping Fraud Detection System')
    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument('--days', type=int, default=5, help='Number of days to analyze')
    date_group.add_argument('--start-date', type=str, help='Start date in format YYYY-MM-DD')
    parser.add_argument('--end-date', type=str, help='End date in format YYYY-MM-DD (required if --start-date is specified)')
    parser.add_argument('--config', type=str, default='config.ini', help='Path to configuration file')
    parser.add_argument('--no-dask', action='store_true', help='Disable Dask processing for large files')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--ship-types', type=str, help='Comma-separated list of ship types to analyze (e.g., "70,80,81")')
    parser.add_argument('--s3-uri', type=str, help='S3 URI for data location (e.g., "s3://bucket-name/path/to/data/")')
    parser.add_argument('--profile', type=str, help='AWS profile name to use for S3 access')
    parser.add_argument('--profile', type=str, help='AWS profile name to use for S3 access')
    parser.add_argument('--access-key', type=str, help='AWS access key ID for S3 access')
    parser.add_argument('--secret-key', type=str, help='AWS secret access key for S3 access')
    parser.add_argument('--region', type=str, help='AWS region name', default='us-east-1')
    parser.add_argument('--role-arn', type=str, help='AWS IAM role ARN to assume for S3 access')
    
    args = parser.parse_args()
    
    # Validate date arguments
    if args.start_date and not args.end_date:
        parser.error("--end-date is required when --start-date is specified")
    
    if args.end_date and not args.start_date:
        parser.error("--start-date is required when --end-date is specified")
    
    # Set debug logging if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Load the config first
    config = load_config(args.config)
    
    # Override selected ship types if specified on command line
    if args.ship_types:
        try:
            selected_types = [int(t.strip()) for t in args.ship_types.split(',') if t.strip()]
            if selected_types:
                logger.info(f"Using command-line specified ship types: {selected_types}")
                config['SELECTED_SHIP_TYPES'] = selected_types
        except ValueError as e:
            logger.warning(f"Invalid ship type format in command line. Using config file values instead. Error: {e}")
    
    # Override data directory with S3 URI if specified
    if args.s3_uri:
        logger.info(f"Using S3 URI for data: {args.s3_uri}")
        config['USE_S3'] = True
        config['S3_DATA_URI'] = args.s3_uri
        # When using S3, override the data directory with the S3 URI
        config['DATA_DIRECTORY'] = args.s3_uri
    else:
        # Use S3 settings from config if present
        if config.get('USE_S3', False) and config.get('S3_DATA_URI', ''):
            logger.info(f"Using S3 URI from config: {config['S3_DATA_URI']}")
            config['DATA_DIRECTORY'] = config['S3_DATA_URI']
    
    # Set AWS profile if specified
    if args.profile:
        logger.info(f"Using AWS profile: {args.profile}")
        config['AWS_PROFILE'] = args.profile
        
        # Set up boto3 session with profile
        import boto3
        boto3.setup_default_session(profile_name=args.profile)
    # Set AWS credentials if provided
    if args.access_key and args.secret_key:
        logger.info(f"Using provided AWS access keys")
        os.environ['AWS_ACCESS_KEY_ID'] = args.access_key
        os.environ['AWS_SECRET_ACCESS_KEY'] = args.secret_key
        if args.region:
            os.environ['AWS_DEFAULT_REGION'] = args.region
            
    # Set up role assumption if specified
    if args.role_arn:
        try:
            logger.info(f"Assuming IAM role: {args.role_arn}")
            import boto3
            sts_client = boto3.client('sts', region_name=args.region)
            assumed_role = sts_client.assume_role(
                RoleArn=args.role_arn,
                RoleSessionName="FraudDetectionSession"
            )
            credentials = assumed_role['Credentials']
            
            os.environ['AWS_ACCESS_KEY_ID'] = credentials['AccessKeyId']
            os.environ['AWS_SECRET_ACCESS_KEY'] = credentials['SecretAccessKey']
            os.environ['AWS_SESSION_TOKEN'] = credentials['SessionToken']
            if args.region:
                os.environ['AWS_DEFAULT_REGION'] = args.region
        except Exception as e:
            logger.error(f"Error assuming role: {e}")
    
    # Run anomaly detection based on provided parameters
    use_dask = not args.no_dask
    
    # Check if we're using date range or days back
    if args.start_date:
        # Using date range
        if not args.end_date:
            # If no end date specified, use today
            end_date = datetime.now().date()
            logger.info(f"No end date specified, using today: {end_date}")
        else:
            try:
                end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
            except ValueError:
                logger.error(f"Invalid end date format: {args.end_date}. Using today's date.")
                end_date = datetime.now().date()
        
        try:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
            # Run with date range
            detect_shipping_anomalies_by_date_range(start_date, end_date, config, use_dask)
        except ValueError as e:
            logger.error(f"Invalid start date format: {args.start_date}. Error: {e}")
            return
    else:
        # Using days back
        detect_shipping_anomalies(args.days, config, use_dask)

if __name__ == "__main__":
    main()

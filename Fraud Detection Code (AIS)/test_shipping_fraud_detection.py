#!/usr/bin/env python3
"""
Unit tests for the shipping fraud detection system.
"""

import os
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import shutil
from shipping_fraud_detection import (
    haversine_distance_nm,
    haversine_vectorized,
    get_most_recent_files,
    load_and_preprocess_day,
    load_config,
    normalize_angle_difference
)

class TestHaversineDistance(unittest.TestCase):
    """Test the Haversine distance calculation functions."""
    
    def test_haversine_distance_nm(self):
        """Test the haversine_distance_nm function with known values."""
        # New York to London coordinates
        ny_lat, ny_lon = 40.7128, -74.0060
        london_lat, london_lon = 51.5074, -0.1278
        
        # Expected distance is approximately 3000 nautical miles
        distance = haversine_distance_nm(ny_lat, ny_lon, london_lat, london_lon)
        self.assertAlmostEqual(distance, 3000, delta=100)
        
        # Test with NaN values
        self.assertIsNone(haversine_distance_nm(np.nan, ny_lon, london_lat, london_lon))
        self.assertIsNone(haversine_distance_nm(ny_lat, np.nan, london_lat, london_lon))
        self.assertIsNone(haversine_distance_nm(ny_lat, ny_lon, np.nan, london_lon))
        self.assertIsNone(haversine_distance_nm(ny_lat, ny_lon, london_lat, np.nan))
    
    def test_haversine_vectorized(self):
        """Test the vectorized Haversine function."""
        # Create a test dataframe
        df = pd.DataFrame({
            'prev_Latitude': [40.7128, 34.0522],
            'prev_Longitude': [-74.0060, -118.2437],
            'curr_Latitude': [51.5074, 37.7749],
            'curr_Longitude': [-0.1278, -122.4194]
        })
        
        # Calculate distances
        distances = haversine_vectorized(df)
        
        # Check that we get reasonable values
        self.assertEqual(len(distances), 2)
        self.assertGreater(distances[0], 2900)  # NY to London
        self.assertLess(distances[0], 3100)
        self.assertGreater(distances[1], 300)   # LA to SF
        self.assertLess(distances[1], 400)

class TestFileOperations(unittest.TestCase):
    """Test file operations like loading and preprocessing."""
    
    def setUp(self):
        """Set up temporary directory and test files."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test config
        self.config = {
            'DATA_DIRECTORY': self.temp_dir,
            'OUTPUT_DIRECTORY': os.path.join(self.temp_dir, 'reports'),
            'SHIP_TYPE_MIN': 70,
            'SHIP_TYPE_MAX': 89,
            'MIN_TRAVEL_NM': 200,
            'MAX_TRAVEL_NM': 550,
            'TIMESTAMP_FORMAT': '%Y-%m-%d %H:%M:%S'
        }
        
        # Create test data files
        self.create_test_files()
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def create_test_files(self):
        """Create test CSV files for different dates."""
        # Create files for 3 consecutive days
        today = datetime.now().date()
        
        for i in range(3):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            file_path = os.path.join(self.temp_dir, f"{date_str}.csv")
            
            # Create a dataframe with test data
            df = pd.DataFrame({
                'MMSI': [123456789, 987654321, 555555555],
                'ShipName': [f"Ship{i}A", f"Ship{i}B", f"Ship{i}C"],
                'ShipType': [70, 80, 85],
                'Latitude': [40.7128, 34.0522, 37.7749],
                'Longitude': [-74.0060, -118.2437, -122.4194],
                'Timestamp': [
                    f"{date_str} 12:00:00", 
                    f"{date_str} 13:00:00", 
                    f"{date_str} 14:00:00"
                ],
                'Speed': [10.5, 12.3, 8.7],
                'Heading': [90, 180, 270]
            })
            
            # Save to CSV
            df.to_csv(file_path, index=False)
    
    def test_get_most_recent_files(self):
        """Test the get_most_recent_files function."""
        files, dates = get_most_recent_files(self.temp_dir, 2)
        
        # Should return 2 files in chronological order
        self.assertEqual(len(files), 2)
        self.assertEqual(len(dates), 2)
        
        # First date should be earlier than second
        self.assertLess(dates[0], dates[1])
    
    def test_load_and_preprocess_day(self):
        """Test the load_and_preprocess_day function."""
        # Get the most recent file
        files, _ = get_most_recent_files(self.temp_dir, 1)
        self.assertTrue(files)
        
        # Load and preprocess
        df = load_and_preprocess_day(files[0], self.config, use_dask=False)
        
        # Check that the dataframe was loaded correctly
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 3)  # 3 rows in test data
        self.assertIn('Date', df.columns)  # Should have added Date column
        
        # Check that types were converted correctly
        self.assertTrue(pd.api.types.is_datetime64_dtype(df['Timestamp']))
        self.assertTrue(pd.api.types.is_numeric_dtype(df['Latitude']))
        self.assertTrue(pd.api.types.is_numeric_dtype(df['Longitude']))
        self.assertTrue(pd.api.types.is_numeric_dtype(df['Speed']))
        self.assertTrue(pd.api.types.is_numeric_dtype(df['Heading']))

class TestAngleNormalization(unittest.TestCase):
    """Test the angle normalization function."""
    
    def test_normalize_angle_difference(self):
        """Test the normalize_angle_difference function."""
        # Test positive angles
        self.assertAlmostEqual(normalize_angle_difference(45), 45)
        self.assertAlmostEqual(normalize_angle_difference(185), -175)
        self.assertAlmostEqual(normalize_angle_difference(370), 10)
        
        # Test negative angles
        self.assertAlmostEqual(normalize_angle_difference(-45), -45)
        self.assertAlmostEqual(normalize_angle_difference(-185), 175)
        self.assertAlmostEqual(normalize_angle_difference(-370), -10)

class TestConfigLoading(unittest.TestCase):
    """Test configuration loading."""
    
    def setUp(self):
        """Set up temporary directory and config file."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'config.ini')
        
        # Create a test config file
        with open(self.config_path, 'w') as f:
            f.write("""[DEFAULT]
DATA_DIRECTORY = C:\\Test\\Data
OUTPUT_DIRECTORY = C:\\Test\\Reports

[SHIP_FILTERS]
SHIP_TYPE_MIN = 75
SHIP_TYPE_MAX = 85

[ANOMALY_THRESHOLDS]
MIN_TRAVEL_NM = 150
MAX_TRAVEL_NM = 600
COG_HEADING_MAX_DIFF = 40
MIN_SPEED_FOR_COG_CHECK = 12

[TIMESTAMPS]
FORMAT = %Y-%m-%d %H:%M:%S
""")
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_load_config(self):
        """Test loading configuration from a file."""
        config = load_config(self.config_path)
        
        # Check that values were loaded correctly
        self.assertEqual(config['DATA_DIRECTORY'], 'C:\\Test\\Data')
        self.assertEqual(config['OUTPUT_DIRECTORY'], 'C:\\Test\\Reports')
        self.assertEqual(config['SHIP_TYPE_MIN'], 75)
        self.assertEqual(config['SHIP_TYPE_MAX'], 85)
        self.assertEqual(config['MIN_TRAVEL_NM'], 150)
        self.assertEqual(config['MAX_TRAVEL_NM'], 600)
        self.assertEqual(config['COG_HEADING_MAX_DIFF'], 40)
        self.assertEqual(config['MIN_SPEED_FOR_COG_CHECK'], 12)
        self.assertEqual(config['TIMESTAMP_FORMAT'], '%Y-%m-%d %H:%M:%S')
    
    def test_load_config_default(self):
        """Test loading default configuration when file doesn't exist."""
        config = load_config('nonexistent_file.ini')
        
        # Check that default values were used
        self.assertEqual(config['DATA_DIRECTORY'], 'C:\\AIS_Data')
        self.assertEqual(config['OUTPUT_DIRECTORY'], 'C:\\AIS_Data\\Reports')
        self.assertEqual(config['SHIP_TYPE_MIN'], 70)
        self.assertEqual(config['SHIP_TYPE_MAX'], 89)
        self.assertEqual(config['MIN_TRAVEL_NM'], 200)
        self.assertEqual(config['MAX_TRAVEL_NM'], 550)
        self.assertEqual(config['COG_HEADING_MAX_DIFF'], 45)
        self.assertEqual(config['MIN_SPEED_FOR_COG_CHECK'], 10)
        self.assertEqual(config['TIMESTAMP_FORMAT'], '%Y-%m-%d %H:%M:%S')

if __name__ == '__main__':
    unittest.main()

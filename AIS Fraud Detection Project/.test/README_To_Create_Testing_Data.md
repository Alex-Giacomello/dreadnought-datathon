# AIS Test Data Generator

This script creates synthetic AIS (Automatic Identification System) data for testing the AIS Shipping Fraud Detection system. The generated data includes normal vessel movements as well as examples of various anomalies that the system is designed to detect.

## Features

- Generates 30 consecutive days of AIS data starting on October 1, 2024
- Creates data for 100 unique vessels with realistic parameters:
  - 90 normal ships (45 Tankers with code 80 and 45 CargoShips with code 70)
  - 10 bad ships (5 BadTankers and 5 BadCargoShips) that exhibit anomalous behavior
- Generates one data point per day for each ship
- Creates daily CSV files in the format "ais-YYYY-MM-DD.csv"
- Converts CSV files to Parquet format for optimized storage and query performance
- Includes 3 examples of each of the following anomaly types:
  - AIS Beacon Off (ships disappearing from tracking)
  - AIS Beacon On (ships suddenly reappearing)
  - Excessive Travel Fast (unusually fast movements >500 NM/day)
  - Excessive Travel Slow (unusually slow movements <200 NM/day)
  - COG-Heading Inconsistency (significant deviations in heading and COG >45 degrees)
- Saves data to a 'Test_data' folder in the user's home directory

## Usage

To generate the test data, simply run the script:

```
python Post-Install_Data_Creator.py
```

## Output

The script creates the following files in the Test_data folder:

1. `testing_data.csv` - The complete dataset containing all AIS transmissions
2. Daily files in the format `ais-YYYY-MM-DD.csv` - One file for each day in the dataset
3. `metadata.txt` - Information about the generated dataset and files
4. A `Parquet` subdirectory containing Parquet versions of all daily files

## Data Format

The generated CSV files contain the following standard AIS data columns:

- `MMSI` - Maritime Mobile Service Identity (unique vessel identifier)
- `BaseDateTime` - Date and time of the AIS transmission
- `LAT` - Latitude coordinate
- `LON` - Longitude coordinate
- `SOG` - Speed over ground in knots
- `COG` - Course over ground in degrees
- `Heading` - Vessel heading in degrees (typically close to course, but with variations)
- `VesselName` - Vessel name
- `IMO` - International Maritime Organization number
- `CallSign` - Vessel call sign
- `VesselType` - AIS vessel type code:
  - For Cargo vessels: AIS type code 70
  - For Tankers: AIS type code 80
- `Status` - Navigation status (0=underway, 1=anchored, 5=moored)
- `Length` - Vessel length in meters
- `Width` - Vessel width in meters
- `Draft` - Vessel draft (depth below waterline)
- `Cargo` - Cargo type identifier
- `TransceiverClass` - AIS transceiver class
- `anomaly` - Type of anomaly if present (e.g., 'AIS_Beacon_Off Day 1'), otherwise NULL

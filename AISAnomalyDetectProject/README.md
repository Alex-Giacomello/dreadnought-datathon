# AIS Shipping Fraud Detection System

This system analyzes AIS (Automatic Identification System) data to detect potential fraudulent shipping activities. It identifies anomalies such as vessels turning off their AIS beacons, sudden reappearances, and unusual travel distances.

## Features

- **Configurable Parameters**: All thresholds and settings can be adjusted via a config file
- **Efficient Processing**: Uses Dask for parallel processing of large datasets
- **Visualization**: Creates interactive maps and summary charts of detected anomalies
- **Comprehensive Reporting**: Generates detailed CSV reports for each day and a summary report

## Anomaly Types Detected

1. **AIS Beacon Off**: Ships present in previous day's data but missing in current day
2. **AIS Beacon On**: Ships suddenly appearing that weren't in previous day's data
3. **Excessive Travel Distance (Fast)**: Ships traveling farther than expected in a day
4. **Excessive Travel Distance (Slow)**: Ships traveling less than expected in a day

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

Create a `config.ini` file with the following structure:

```ini
[DEFAULT]
DATA_DIRECTORY = C:\Path\To\AIS_Data
OUTPUT_DIRECTORY = C:\Path\To\AIS_Data\Reports

[SHIP_FILTERS]
SHIP_TYPE_MIN = 70
SHIP_TYPE_MAX = 89

[ANOMALY_THRESHOLDS]
MIN_TRAVEL_NM = 200
MAX_TRAVEL_NM = 550

[TIMESTAMPS]
FORMAT = %Y-%m-%d %H:%M:%S
```

## Usage

### Command Line

```
python shipping_fraud_detection.py --days 5 --config config.ini
```

Options:
- `--days`: Number of days to analyze (default: 5)
- `--config`: Path to configuration file (default: config.ini)
- `--no-dask`: Disable Dask processing for large files
- `--debug`: Enable debug logging

### As a Module

```python
from shipping_fraud_detection import detect_shipping_anomalies

# Run detection with default config
anomalies_df = detect_shipping_anomalies(num_days_to_analyze=5)

# Run detection with custom config
anomalies_df = detect_shipping_anomalies(
    num_days_to_analyze=5,
    config_file='custom_config.ini',
    use_dask=True
)
```

## Data Format

The system expects AIS data in CSV format with filenames in the format `YYYY-MM-DD.csv`. Each file should contain at least the following columns:

- MMSI (Maritime Mobile Service Identity)
- ShipName
- ShipType
- Latitude
- Longitude
- Timestamp
- Speed
- Heading

## Output

The system generates:

1. Daily CSV reports of detected anomalies
2. Interactive HTML maps showing anomaly locations
3. Summary charts in PNG format
4. An overall summary report and map

## Testing

Run the unit tests:

```
python -m unittest test_shipping_fraud_detection.py
```

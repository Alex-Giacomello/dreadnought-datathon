# AIS Shipping Fraud Detection System

This system analyzes AIS (Automatic Identification System) data to detect potential fraudulent shipping activities. It identifies anomalies such as vessels turning off their AIS beacons, sudden reappearances, unusual travel distances, and inconsistencies between reported Course Over Ground (COG) and Heading.

## Quick Start Guide

1. **Run the Setup Tool**: Double-click on `Open_to_Begin.bat` to start the setup process.
2. **Follow the Instructions**: The setup tool will guide you through the installation process.
3. **Launch the Application**: After installation, use the desktop shortcut to run the program.

## Table of Contents

- [System Requirements](#system-requirements)
- [Installation Options](#installation-options)
- [First-Time Setup](#first-time-setup)
- [Features](#features)
- [Anomaly Types Detected](#anomaly-types-detected)
- [Installation](#installation)
  - [Easy Installation (Windows)](#easy-installation-windows)
  - [Manual Installation](#manual-installation)
  - [Windows-Specific Instructions](#windows-specific-instructions)
- [Configuration](#configuration)
  - [Ship Type Selection](#ship-type-selection)
  - [File Format Support](#file-format-support)
- [Using the AIS Shipping Fraud Detection System](#using-the-ais-shipping-fraud-detection-system)
- [Data Format Requirements](#data-format-requirements)
- [Output](#output)
- [Building Instructions](#building-instructions)
  - [Build System Overview](#build-system-overview)
  - [Building the Executable](#building-the-executable)
  - [Building the Installer and Uninstaller](#building-the-installer-and-uninstaller)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Support](#support)

## System Requirements

- Windows 10 or Windows 11
- Python 3.8 or higher (will be installed if missing)
- Minimum 4GB RAM (8GB recommended)
- At least 500MB of free disk space

## Installation Options

The setup tool provides several options:

1. **Build Application**: Creates a standalone executable (.exe) for the AIS Shipping Fraud Detection System.
2. **Build Installer**: Creates an installer that can be distributed to other computers.
3. **Build Uninstaller**: Creates an uninstaller for the application.
4. **Build All Components**: Builds all the above components at once.
5. **Open README**: Opens this comprehensive guide.

## First-Time Setup

If you're running the application for the first time, follow these steps:

1. **Python Installation**: If Python is not installed, the setup tool will offer to install the Python Install Manager, which will help you install the correct version of Python.
2. **Required Packages**: The setup will automatically install required Python packages:
   - pandas, numpy, dask (for data processing)
   - folium, matplotlib, seaborn (for visualization)
   - geopy (for geospatial calculations)
   - tkcalendar (for date range selection)

## Features

- **Configurable Parameters**: All thresholds and settings can be adjusted via a config file
- **Efficient Processing**: Uses Dask for parallel processing of large datasets
- **Flexible Date Selection**: Analyze by specific date range or by number of days from the most recent data
- **Ship Type Selection**: Choose specific ship types to analyze instead of using ranges
- **Multiple File Formats**: Support for both CSV and Parquet file formats
- **Visualization**: Creates interactive maps and summary charts of detected anomalies
- **Comprehensive Reporting**: Generates detailed CSV reports for each day and a summary report

## Anomaly Types Detected

1. **AIS Beacon Off**: Ships present in previous day's data but missing in current day
2. **AIS Beacon On**: Ships suddenly appearing that weren't in previous day's data
3. **Excessive Travel Distance (Fast)**: Ships traveling farther than expected in a day
4. **Excessive Travel Distance (Slow)**: Ships traveling less than expected in a day
5. **COG-Heading Inconsistency**: Ships where Course Over Ground (COG) differs significantly from Heading while moving at high speed
6. **Null Values**: Ships with missing data in critical fields (Latitude, Longitude, Speed, Heading, COG)

## Installation

### Easy Installation (Windows)

1. Run the installer by double-clicking `AIS_Fraud_Detection_Installer.exe`
2. Follow the on-screen instructions
3. The installer will:
   - Check for required dependencies and install them if needed
   - Create necessary directories
   - Set up the configuration file
   - Create a desktop shortcut

### Manual Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application using one of the methods described in the Usage section

### Windows-Specific Instructions

1. **Python Installation**:
   - Download and install Python 3.8 or higher from [python.org](https://www.python.org/downloads/)
   - During installation, make sure to check the option "Add Python to PATH"

2. **Running the Application**:
   - Option 1: Double-click the `Shipping Fraud Detection.bat` file
   - Option 2: Create and use the desktop shortcut by running `create_desktop_shortcut.bat`

## Configuration

Create a `config.ini` file with the following structure:

```ini
[DEFAULT]
DATA_DIRECTORY = C:\Path\To\AIS_Data
OUTPUT_DIRECTORY = C:\Path\To\AIS_Data\Reports

[SHIP_FILTERS]
SELECTED_SHIP_TYPES = 70,80,81,82

[ANOMALY_THRESHOLDS]
MIN_TRAVEL_NM = 200
MAX_TRAVEL_NM = 550
COG_HEADING_MAX_DIFF = 45
MIN_SPEED_FOR_COG_CHECK = 10

[ANOMALY_TYPES]
AIS_Beacon_Off = True
AIS_Beacon_On = True
Excessive_Travel_Distance_Fast = True
Excessive_Travel_Distance_Slow = True
COG-Heading_Inconsistency = True

[TIMESTAMPS]
FORMAT = %Y-%m-%d %H:%M:%S
```

### Ship Type Selection

Instead of using a min/max range, you can now specify exactly which ship types to analyze using the SELECTED_SHIP_TYPES parameter. Ship types include:

- **Cargo Ships (70-79)**:
  - 70: Cargo, all ships of this type
  - 71: Cargo, Hazardous category A
  - 72: Cargo, Hazardous category B
  - 73: Cargo, Hazardous category C
  - 74: Cargo, Hazardous category D
  - 75-78: Cargo, Reserved for future use
  - 79: Cargo, No additional information

- **Tanker Ships (80-89)**:
  - 80: Tanker, all ships of this type
  - 81: Tanker, Hazardous category A
  - 82: Tanker, Hazardous category B
  - 83: Tanker, Hazardous category C
  - 84: Tanker, Hazardous category D
  - 85-88: Tanker, Reserved for future use
  - 89: Tanker, No additional information

### File Format Support

The system supports both CSV and Parquet file formats with filenames in ais-YYYY-MM-DD format (e.g., `ais-2023-05-15.csv` or `ais-2023-05-15.parquet`). For backward compatibility, filenames without the 'ais-' prefix are also supported. The application will automatically detect the file format based on the extension.

## Using the AIS Shipping Fraud Detection System

After installation, the application allows you to:

1. **Select Data Source**: Specify the directory containing AIS data files.
2. **Choose Analysis Parameters**: Select which types of anomalies to detect.
3. **Filter by Ship Type**: Focus analysis on specific types of vessels.
4. **Select Date Range**: Analyze data for specific dates or for a number of recent days.
5. **Visualize Results**: View interactive maps and charts of detected anomalies.

### Graphical User Interface

The system includes a GUI for easier configuration and operation:

```
run_gui.bat
```

Or run directly with Python:

```
python AnomalyDetectGUI_new.py
```

The GUI allows you to:
- Configure data and output directories
- Select specific ship types to analyze
- Choose which anomaly types to detect
- Set detection thresholds
- Select data by number of days or specific date range
- Run the analysis

> **Note**: For the best date range selection experience, install the `tkcalendar` package (`pip install tkcalendar`). If not installed, the application will fall back to basic text entry fields for dates.

### Command Line

```
python shipping_fraud_detection.py --days 5 --config config.ini --ship-types "70,80,81"
```

Or use a specific date range:

```
python shipping_fraud_detection.py --start-date 2023-10-01 --end-date 2023-10-15 --config config.ini
```

Options:
- `--days`: Number of days to analyze (default: 5)
- `--start-date`: Start date for analysis in YYYY-MM-DD format (must be used with --end-date)
- `--end-date`: End date for analysis in YYYY-MM-DD format (must be used with --start-date)
- `--config`: Path to configuration file (default: config.ini)
- `--ship-types`: Comma-separated list of ship types to analyze
- `--no-dask`: Disable Dask processing for large files
- `--debug`: Enable debug logging

### As a Module

```python
from shipping_fraud_detection import detect_shipping_anomalies, detect_shipping_anomalies_by_date_range

# Run detection with default config (days-based)
anomalies_df = detect_shipping_anomalies(num_days_to_analyze=5)

# Run detection with custom config (days-based)
anomalies_df = detect_shipping_anomalies(
    num_days_to_analyze=5,
    config_input='custom_config.ini',
    use_dask=True
)

# Run with specific date range
from datetime import date
start_date = date(2023, 10, 1)
end_date = date(2023, 10, 15)
anomalies_df = detect_shipping_anomalies_by_date_range(
    start_date=start_date,
    end_date=end_date,
    config_input='config.ini',
    use_dask=True
)
```

## Data Format Requirements

AIS data files should include these columns:
- MMSI (Maritime Mobile Service Identity)
- ShipName
- ShipType
- Latitude
- Longitude
- Timestamp
- Speed
- Heading
- COG (Course Over Ground)

File naming convention: `YYYY-MM-DD.csv` or `ais-YYYY-MM-DD.csv` (or .parquet format)

## Output

The system generates:

1. Daily CSV reports of detected anomalies
2. Interactive HTML maps showing anomaly locations
3. Summary charts in PNG format
4. An overall summary report and map

## Building Instructions

### Build System Overview

The build system consists of the following components:

1. `build_all.bat` - Main build script that builds both installer and uninstaller
2. `build_exe.bat` - Script to build the standalone executable
3. `build_installer.bat` - Script to build the installer executable
4. `build_uninstaller.bat` - Script to build the uninstaller executable
5. `installer.py` - GUI application for installing the system
6. `uninstaller.py` - GUI application for uninstalling the system

### Building the Executable

#### Method 1: Using the Build Script

1. Open Command Prompt as Administrator
2. Navigate to the project directory:
   ```
   cd "path\to\AISAnomalyDetectProject"
   ```
3. Run the build script:
   ```
   build_exe.bat
   ```
4. The executable will be created in the `dist` folder

#### Method 2: Manual Build

1. Open Command Prompt as Administrator
2. Navigate to the project directory
3. Run PyInstaller with the following command:
   ```
   pyinstaller --name="Shipping Fraud Detection" --windowed --onefile --add-data="shipping_fraud_detection.py;." --add-data="config.ini;." AnomalyDetectGUI_new.py
   ```

### Building the Installer and Uninstaller

#### Method 1: Using the Build All Script

1. Open Command Prompt as Administrator
2. Navigate to the project directory:
   ```
   cd "path\to\AISAnomalyDetectProject"
   ```
3. Run the build script:
   ```
   build_all.bat
   ```
4. The installer and uninstaller executables will be created in the `dist` folder

#### Method 2: Building Components Separately

1. To build only the installer:
   ```
   build_installer.bat
   ```

2. To build only the uninstaller:
   ```
   build_uninstaller.bat
   ```

## Testing

Run the unit tests:

```
python -m unittest test_shipping_fraud_detection.py
```

## Troubleshooting

1. **Python not found**:
   - Make sure Python is installed and added to PATH
   - Restart your computer after installing Python
   - If the setup fails to detect Python, use the Python Install Manager to install it, then restart the setup.

2. **Missing dependencies**:
   - Install all required packages: `pip install pandas numpy dask folium matplotlib seaborn geopy tkcalendar`
   - Ensure you have an active internet connection for package downloads.

3. **Executable fails to run**:
   - Try running from Command Prompt to see error messages

4. **File format issues**:
   - Ensure your data files follow the required naming convention
   - Check that all required columns are present in your data files

5. **Performance issues**: 
   - For large datasets, consider enabling the Dask processing option.

## Support

For assistance with the AIS Shipping Fraud Detection System, please contact your system administrator or IT support team. 
Yeah, Right, just kidding, but let me know what you need/find. -Chris

---

**Note**: This application is designed for detecting potentially fraudulent shipping activities based on AIS data analysis. The effectiveness of detection depends on the quality and completeness of input data.

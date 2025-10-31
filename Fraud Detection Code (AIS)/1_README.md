# AIS Shipping Fraud Detection System

This system analyzes AIS (Automatic Identification System) data to detect potential fraudulent shipping activities. It identifies anomalies such as vessels turning off their AIS beacons, sudden reappearances, unusual travel distances, and inconsistencies between reported Course Over Ground (COG) and Heading.

## Table of Contents

- [Features](#features)
- [Anomaly Types Detected](#anomaly-types-detected)
- [Installation](#installation)
  - [Easy Installation (Windows)](#easy-installation-windows)
  - [Manual Installation](#manual-installation)
  - [Windows-Specific Instructions](#windows-specific-instructions)
- [Configuration](#configuration)
  - [Ship Type Selection](#ship-type-selection)
  - [File Format Support](#file-format-support)
- [Usage](#usage)
  - [Graphical User Interface](#graphical-user-interface)
  - [Command Line](#command-line)
  - [As a Module](#as-a-module)
- [Data Format](#data-format)
- [Output](#output)
- [Building the Executable](#building-the-executable)
  - [Method 1: Using the Build Script](#method-1-using-the-build-script-1)
  - [Method 2: Manual Build](#method-2-manual-build-1)
- [Building the Installer and Uninstaller](#building-the-installer-and-uninstaller)
  - [Method 1: Using the Build All Script](#method-1-using-the-build-all-script)
  - [Method 2: Building Components Separately](#method-2-building-components-separately)
  - [Build System Components](#build-system-components)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Features

- **Configurable Parameters**: All thresholds and settings can be adjusted via a config file
- **Efficient Processing**: Uses Dask for parallel processing of large datasets
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
Ensure the executable has been built before attempting Install.  See [Building the Executable](#building-the-executable) section for details.

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
   - Download and install Python 3.7 or higher from [python.org](https://www.python.org/downloads/)
   - During installation, make sure to check the option "Add Python to PATH"

2. **Running the Application**:
   - Option 1: Double-click the `Shipping Fraud Detection.bat` file
   - Option 2: Create and use the desktop shortcut by running `create_desktop_shortcut.bat`

3. **System Requirements**:
   - Windows 10 or Windows 11
   - At least 4GB of RAM (8GB recommended for large datasets)
   - At least 500MB of free disk space

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

You can specify exactly which ship types to analyze using the SELECTED_SHIP_TYPES parameter. Ship types include:

- **Cargo Ships (70-79)**:
  - 70: Cargo, General category for ships of this type
  - 71: Cargo, Hazardous category A
  - 72: Cargo, Hazardous category B
  - 73: Cargo, Hazardous category C
  - 74: Cargo, Hazardous category D
  - 75-78: Cargo, Reserved for future use
  - 79: Cargo, No additional information

- **Tanker Ships (80-89)**:
  - 80: Tanker, General category for ships of this type
  - 81: Tanker, Hazardous category A
  - 82: Tanker, Hazardous category B
  - 83: Tanker, Hazardous category C
  - 84: Tanker, Hazardous category D
  - 85-88: Tanker, Reserved for future use
  - 89: Tanker, No additional information

### File Format Support

The system now supports both CSV and Parquet file formats with filenames in ais-YYYY-MM-DD format (e.g., `ais-2023-05-15.csv` or `ais-2023-05-15.parquet`). For backward compatibility, filenames without the 'ais-' prefix are also supported. The application will automatically detect the file format based on the extension.

## Usage

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
- Run the analysis

### Command Line

```
python shipping_fraud_detection.py --days 5 --config config.ini --ship-types "70,80,81"
```

Options:
- `--days`: Number of days to analyze (default: 5)
- `--config`: Path to configuration file (default: config.ini)
- `--ship-types`: Comma-separated list of ship types to analyze (for example [70, 80, 81]
- `--no-dask`: Disable Dask processing for large files (disabling DASK is NOT recommended)
- `--debug`: Enable debug logging

### As a Module

```python
from shipping_fraud_detection import detect_shipping_anomalies

# Run detection with default config
anomalies_df = detect_shipping_anomalies(num_days_to_analyze=5)

# Run detection with custom config
anomalies_df = detect_shipping_anomalies(
    num_days_to_analyze=5,
    config_input='custom_config.ini',
    use_dask=True
)

# Run with specific ship types
config = load_config('config.ini')
config['SELECTED_SHIP_TYPES'] = [70, 80, 81]
anomalies_df = detect_shipping_anomalies(
    num_days_to_analyze=5,
    config_input=config,
    use_dask=True
)
```

## Data Format

The system expects AIS data in CSV or Parquet format with filenames in the format `ais-YYYY-MM-DD.csv` or `ais-YYYY-MM-DD.parquet`. Each file should contain at least the following columns:

- MMSI (Maritime Mobile Service Identity)
- ShipName
- ShipType
- Latitude
- Longitude
- Timestamp
- Speed
- Heading
- COG (Course Over Ground)

## Output

The system generates:

1. Daily CSV reports of detected anomalies
2. Interactive HTML maps showing anomaly locations
3. Summary charts in PNG format
4. An overall summary report and map

## Building the Executable

### Method 1: Using the Build Script

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

### Method 2: Manual Build

1. Open Command Prompt as Administrator
2. Navigate to the project directory
3. Run PyInstaller with the following command:
   ```
   pyinstaller --name="Shipping Fraud Detection" --windowed --onefile --add-data="shipping_fraud_detection.py;." --add-data="config.ini;." AnomalyDetectGUI_new.py
   ```

## Building the Installer and Uninstaller

### Method 1: Using the Build All Script

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

### Method 2: Building Components Separately

1. To build only the installer:
   ```
   python build_installer_exe.py
   ```

2. To build only the uninstaller:
   ```
   python build_uninstaller_exe.py
   ```

3. To build with a custom icon:
   ```
   python build_installer_exe.py --icon SFD.ico
   python build_uninstaller_exe.py --icon SFD.ico
   ```

### Build System Components

- `build_all.bat` - Main build script that builds both installer and uninstaller
- `build_installer_exe.py` - Script to build the installer executable
- `build_uninstaller_exe.py` - Script to build the uninstaller executable
- `installer.py` - GUI application for installing the system
- `uninstaller.py` - GUI application for uninstalling the system

### Requirements

- Python 3.6 or higher
- PyInstaller (will be automatically installed if missing)
- Required Python packages will be installed by the installer at runtime

### Cleanup

After building, you can delete the temporary files created by PyInstaller:
- `build` directory
- `*.spec` files

## Testing

Run the unit tests:

```
python -m unittest test_shipping_fraud_detection.py
```

## Troubleshooting

1. **Python not found**:
   - Make sure Python is installed and added to PATH
   - Restart your computer after installing Python

2. **Missing dependencies**:
   - Install all required packages: `pip install pandas numpy dask folium matplotlib seaborn geopy`

3. **Executable fails to run**:
   - Try running from Command Prompt to see error messages

4. **File format issues**:
   - Ensure your data files follow the ais-YYYY-MM-DD.csv or ais-YYYY-MM-DD.parquet naming convention (filenames without the 'ais-' prefix are also supported)
   - Check that all required columns are present in your data files


[def]: #building-the-installer-and-uninstaller

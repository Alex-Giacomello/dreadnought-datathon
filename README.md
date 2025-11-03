# dreadnought-datathon

## **2 NOV 2025 updates**

**Updates to \.test**

KNOWN BUGS
1) ISSUE (02NOV2025): Once created, the executables Cannot be run from \dist folder, returns the following error:
	Executable error:
	Missing Files
		The following files are missing:
		shipping_fraud_detection.py(Main detection script)
		config.ini (configuration file)

	Please ensure all required files are in the same directory as this application

WORKAROUND: To run, Shipping Fraud Detection.exe must be copied back to test folder


**Fixed Issues: as of: (02NOV2025)**

1) Fixed Config.ini missing [TIMESTAMPS] warning message

2) For GUI: set 1-5 October 2024 as the default dates in the application

3) Code now can review both .csv and .parquet file types

4) Shipping fraud detection addresses columns that exactly match the data format from EDL:

Data columns (total 17 columns):
 #   Column            Dtype  
---  ------            -----  
 0   MMSI              uint64 
 1   BaseDateTime      object 
 2   LAT               float64
 3   LON               float64
 4   SOG               float64
 5   COG               float64
 6   Heading           float64
 7   VesselName        object 
 8   IMO               object 
 9   CallSign          object 
 10  VesselType        object 
 11  Status            object 
 12  Length            float64
 13  Width             float64
 14  Draft             float64
 15  Cargo             float64
 16  TransceiverClass  object 

5) ISSUE (02NOV2025): GUI needs instructions.

Adjusted the GUI Tabs to a more logical order.
Added basic overview (Purpose) and Instructions to the first tab:
"This system analyzes Automatic Identification System (AIS) data to detect potential fraudulent shipping activities. It does so by identifying anomalies such as vessels turning off their AIS beacons (sudden disappearances), sudden reappearances, unusual travel distances, and large inconsistencies between reported Course Over Ground (COG) and Heading.  Users have the option of examining data over specific date ranges, or examining data leading up to the current date.  
NOTE: In this test implementation only data from 1 OCT 2024 to 31 MAR 2025 is available for use.

Select the time period on this tab and press the search button to execute your inquiry.  You can select the specific types of ships and anomalies you want to search for in those tabs.  The Data and Results folders can be set on the Advanced Tab."

**Added:**
1) A test data creation script that creates 30 days of data for 100 ships with examples of each type of anomaly the project is designed to detect (creates both .csv and .parquet versions).  Once run, copy contents of test data folder to the AIS_Data folder (or other folder as specified in config) to test.




## **For .dev**
BUGS
1) ISSUE (02NOV2025): Once created, the executables Cannot be run from \dist folder, returns the following error:
	Executable error:
	Missing Files
		The following files are missing:
		shipping_fraud_detection.py(Main detection script)
		config.ini (configuration file)

	Please ensure all required files are in the same directory as this application


2) ISSUE (02NOV2025): Executable files take a LONG time (~45 sec.) to open



3) ISSUE (02NOV2025):  Program needs S3 integration

4) ISSUE (02NOV2025): Install GUI and related CMD window interface is clunky and not user friendly.1. Working on code base to implement this as multi-platform to enable test/run on non-windows systems






## **1 NOV 2025 updates and bug fixes**

File Structure updated to include \.Dev, \.Test, and \.Prod 

Code Version 0.3 moved from \.Prod to \.Test 

Code Updates in Version 0.3:
  1. Date selection changed from unspecified number to a discrete date selection
  2. Updated Requirements and dependencies between scripts
  3. Reduced the number of seperate scripts
  4. AIS Fraud Detection Project README.md updated to consolidate all instructions


# dreadnought-datathon

# **28 November SFD Beta 2.1 update**
 -I cleaned out a lot of "dead wood" on this repository to ensure that old code wasn't gettingmixed up with new.c
The "best_model.pt" file can't upload to github - it IS in the teams channel, it needs to be copied into the ~/mol_course-prediction/models/trained/ directory for everything to work correctly.

# **25 November SFD Beta 2.1 Release**

## The Beta version is out.  
-SFD_Beta_Release is in the Final Testing Folder!
-Test, test, and test some more
-With the exception of the AI path predection module this is done.
-There are lots of changes from the original so take a look at the README.md file

## Drop bugs into the BugDrop.md file in the Final Testing Folder


## This is the version we should build the presentation with - there is a placeholder for teh AI Path generation already, so until we need to demo, we are GTG.



# Happy Thanksgiving!




# **12 NOV Updates**

## MVP edition is out.  Should be ready to go.  Give it a try when you can.

## Started LLM development
-I've switched over to LLM development (in .dev) that is going slowly as I'm learning by doing with this one.

# **7 NOV Updates**

## **Updates to .test**

**Beta 1.0 is posted for testing - Please help me out and try it on *your* machine**

## Instructions:
- Download the files from .test into a single folder
- Open SFD_GUI.py in a python environment
- Set your search and output parameters.  Don't forget to set your Data and Output Folders.  If you don't, it won't find any data.  If it found data, but didn't set you output folder - it defaults to a C: drive folder.
- Click Run Analysis, sit back, and watch the magic..

**NOTE Start Small, just use the defaults for your first run.**

Large dataset searches will take *HOURS* if you are producing the Pathway Maps

## Other updates:
- Moved the .test folder forward in the repository to ease access
- Significantly trimmed down the number of files required to run the code
- Added S3 integration to the project

## *Current Variables to play with (defaults shown)

[DEFAULT]\
data_directory = C:/AIS_Data\
output_directory = C:/AIS_SFD_Results\
start_date = 2024-10-15\
end_date = 2024-10-17\
\
[Paths]\
data_directory = C:/YourDataFolder/Data
output_directory = C:/YourResultsFolder
\
[SHIP_FILTERS]\
selected_ship_types = 70\
\
[ANOMALY_THRESHOLDS]\
min_travel_nm = 200.0\
max_travel_nm = 550.0\
cog_heading_max_diff = 45.0\
min_speed_for_cog_check = 10.0\
beacon_time_threshold_hours = 6\
\
[ANOMALY_TYPES]\
ais_beacon_off = True\
ais_beacon_on = True\
excessive_travel_distance_fast = True\
excessive_travel_distance_slow = True\
cog-heading_inconsistency = True\
\
[ANALYSIS_FILTERS]\
min_latitude = -90.0\
max_latitude = 90.0 min_longitude = -180.0\
max_longitude = 180.0\
time_start_hour = 0\
time_end_hour = 24\
min_confidence = 75\
max_anomalies_per_vessel = 10000\
filter_mmsi_list = \
\
[OUTPUT_CONTROLS]\
generate_statistics_excel = True\
generate_statistics_csv = True\
generate_overall_map = True\
generate_vessel_path_maps = False\
generate_charts = True\
generate_anomaly_type_chart = True\
generate_vessel_anomaly_chart = True\
generate_date_anomaly_chart = True\
filter_to_anomaly_vessels_only = True\
show_lat_long_grid = False\
show_anomaly_heatmap = True\
\
[ADVANCED]\
aws_session_token = \
aws_access_key_id = \
aws_secret_access_key = \
\
[LOGGING]\
log_level = INFO\
log_file = SDF_GUI.log\
suppress_warnings = True\
  \
  \



## **Updates to .dev**
- working on some GUI-to-Results enhancements,
- working on heatmap and path map enhancements. Any ideas on speeding up pathway generation are welcome,
- beginning to work on AI integration by building an LLM that uses Claud Sonnet as the base,
- *trying* to speed up processing, we will need GPUs (plural) to put everything together for a *"live"* demo.


## **3 NOV 2025 updates**

## **Updates to .dev**
- [1. Long Loading Items](#long-loading-items)
- [2. S3 Integration](#s3-integration)
- [3. Requirements and Dependencies Update](#requirements-and-dependencies-update)
- [4. Project has grown in size and complexity](#project-has-grown-in-size-and-complexity)

## Bug Fixes in .dev

1. ISSUE (02NOV2025): Executable files take a LONG time (~45 sec.) to open - Added loading screen to let user see progress 

2. ISSUE (02NOV2025): Program needs S3 integration - Updatesd script to integrate multiple methods

## Long Loading items:

Created a loading splash screen to show user that the file is running.
Created splash_screen.py
 - A module that displays SFDLoad.png with a progress bar
Created launch_with_splash.py
 - A launcher script that shows the splash screen while the main app loads
Updated AnomalyDetectGUI_new.py
 - Added a proper main()  function to support integration with the splash screen
Created splash_build.spec
 - A PyInstaller spec file for building the .exe with the splash screen
Created build_with_splash.py
 - A build script to easily create the executable

How to Build the Executable:
1. Make sure SFDLoad.png is in the .dev folder
2. Run the build script: python build_with_splash.py
3. The executable will be created in the dist folder

How it Works:
When the .exe starts, it shows SFDLoad.png with a loading bar. The loading bar will gradually progress from 0% to 90% during the ~45 second loading time. Once the application is fully loaded, the loading bar completes to 100% and the splash screen closes. The application window opens immediately afterward

Notes:
-The progress bar doesn't track actual loading progress (that would be complicated) but simulates it with timing
-If SFDLoad.png isn't found, the build script will create a placeholder image
-The splash screen includes status messages that change during loading to inform the user
-The solution works with PyInstaller, which you're already using for your builds
-This provides the visual cue you requested without needing to actually speed up the loading time.

## S3 Integration

The project needs to access to the account "Cakes and Tensors (372184463766)" with "BAHSSO_372184463766_Dreadnought" to access AWS resources programmatically or from the AWS CLI. 

AWS recommends that configure the AWS CLI to retrieve them automatically using the "aws configure sso"  command. 
SSO Start URL:  https://bahextendedenterprise.awsapps.com/start/#
SSO Region:  us-east-1

AWS IAM Identity Center credentials CLI:
$ aws configure sso-session
SSO session name: my-sso
SSO start URL [None]: https://bahextendedenterprise.awsapps.com/start/#
SSO region [None]: us-east-1
SSO registration scopes [None]: sso:account:access

Use command prompt to set the AWS environment variables:
SET AWS_ACCESS_KEY_ID=ASIAVNJ7MHGLBDXB3RHB
SET AWS_SECRET_ACCESS_KEY=cbtSohqXAMag/FCSNlUAut0WEVZ6lVwELk5VrgUO
SET AWS_SESSION_TOKEN=IQoJb3JpZ2luX2VjEIz//////////wEaCXVzLWVhc3QtMSJHMEUCIBUfR2M5f00bdg018qiBVFPY00DDvCPYns9C4PM7uEduAiEAw4F1KTyBuWEm0/RbDIR9hfYHkFddDyXXCQluKNiD1dwq+wIIVBACGgwzNzIxODQ0NjM3NjYiDP26KeLH7FYuK5Zn5irYAvynuaNjIuQYvppqAktZchxf/BoN4iu6LExRNhlU1/WgDs/SG+WI6TcJzeCaxSn4oqF7CKBpFY1gClCkcl4680G+mfXHC31fPc00cRRz+G6Rq7V4UpMQV3iTzTMMOGKFxNxDLCrDfnP3n6FQtb5OQKPhezUIANJIBmlVPq5HqIGqOLIWaqQpdZ3tdem+xlX0kl2BACyzly0cnwVGF1kPn9+YmrHEX7tFE7sQjqWvUex3/58W/kKDyq6aq2Vv3esUpGmb55x7CwPEHtDwx0pcQEJPtYtRu4b6hTCzXCaxJoPmzaOJ/Q4xxWmlhY6ieQRmO4XloswamN5TvYSgmUP8H5PqW8zQtZvkfae5fT8mfTjC1auyeqeAr4XrsiwIFxqtVCsxv3hRrXXbkUDcoGzdNr8QgG2HiQJTvH4acWf2v9b63S1BR+GjvfAnNi+X1V1ysJU6U/FsEMzZMNe4oMgGOqUBWcIJs0jg5NNkf7ztcrHiw+3UVvsEJ+eMlx7MF9o7Ei2dnM7k9uCC+KgY3MBWj3Ip6D3vTXeQe3qCYVWZbCfQwMb6rPogZdngf0zkt+hAk3DjZhosL66mDv02dN+Y0UBs1MtuXZuy3pIJobU/bejxMx0//txgBM8VdQpIivX/NxGbemYuQ3LayNGz81vnQq88i5TjieCUTu1TWDE41pgumuov63Q4

To implement: Created a new file called enhanced_s3_auth.py that provides different authentication methods:
-Default credential provider chain
-AWS profile
-Access keys
-IAM role ARN

2. GUI Updates
-Updated AnomalyDetectGUI_new.py to include:
--Authentication method dropdown (default, profile, keys, role)
--Input fields for different authentication methods
--A new authentication method frame in the S3 settings section

3. Authentication Logic
-Implemented Dynamic UI that shows/hides input fields based on the selected authentication method
-Test connection functionality that tests the connection with the selected authentication method
-Configuration saving and loading for all authentication settings

4. Command Line Integration
Updated shipping_fraud_detection.py to:
-Accept new command-line arguments for access keys, region, and IAM role
-Set appropriate environment variables based on the provided authentication parameters
-The implementation is now complete and supports all the requested authentication methods. The GUI allows users to select their preferred method and enter the necessary credentials, which are then used for testing the connection and for actual data processing.


## Requirements and Dependencies Update

1. Updated the project's dependencies to include all necessary packages for the new splash screen functionality.
New Requirements
Restructured and expanded the requirements.txt file to include all dependencies needed for the new functionality:

Added Pillow (≥9.0.0) - Essential for handling images in the splash screen
Added tkhtmlview (≥0.1.0) and markdown (≥3.3.0) - For better README rendering
Added boto3 (≥1.24.0) - For AWS integration
Added pywin32 (≥300) - For Windows-specific functionality
Organized dependencies into logical categories with comments
Maintained all existing dependencies with their version requirements

2. Created an Installation Script, install_dependencies.py, that:

-Automatically installs all dependencies from requirements.txt
-Checks for optional dependencies and provides warnings if they're missing
-Shows detailed output about the installation process
-Provides helpful guidance for manually installing specific packages if needed

3. Added Documentation file, SPLASH_SCREEN_README.md, that

-Explains the new splash screen feature
-Lists all added files and their purposes
-Details the new dependencies
-Provides instructions for building with the splash screen
-Includes customization options and troubleshooting tips

## Project has grown in size and complexity

-Created a ProjectFileList.txt to ensure all required project files are tracked.

## Bug Fixes in .dev

1. ISSUE (02NOV2025): Executable files take a LONG time (~45 sec.) to open - Added loading screen to let user see progress 

2. ISSUE (02NOV2025): Program needs S3 integration - Updatesd script to integrate multiple methods



## **2 NOV 2025 updates**

## **Updates to \.test**

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

4) Shipping fraud detection addresses columns that exactly match the data format from EDL

5) Adjusted the GUI Tabs to a more logical order.
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


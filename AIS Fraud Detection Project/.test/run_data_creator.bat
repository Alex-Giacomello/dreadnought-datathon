@echo off
setlocal enabledelayedexpansion
echo AIS Shipping Fraud Detection - Test Data Generator
echo =================================================

echo Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python first.
    pause
    exit /b 1
)

echo Checking required Python packages...
python -m pip show pandas >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing pandas package...
    python -m pip install pandas
    if %ERRORLEVEL% NEQ 0 (
        echo Error: Failed to install pandas
        pause
        exit /b 1
    )
)

echo Generating test data...
python Post-Install_Data_Creator.py

if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to generate test data
    pause
    exit /b 1
)

echo.
echo Test data generation complete!
echo The data has been saved to the Test_data folder in your home directory.
echo.

pause
exit /b 0

@echo off
title Shipping Fraud Detection System
echo Starting Shipping Fraud Detection System...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

REM Check if required packages are installed and install them if needed
echo Checking required packages...
python -c "import pandas" >nul 2>&1 || pip install pandas
python -c "import numpy" >nul 2>&1 || pip install numpy
python -c "import dask" >nul 2>&1 || pip install dask
python -c "import folium" >nul 2>&1 || pip install folium
python -c "import matplotlib" >nul 2>&1 || pip install matplotlib
python -c "import seaborn" >nul 2>&1 || pip install seaborn
python -c "import geopy" >nul 2>&1 || pip install geopy
python -c "import pyarrow" >nul 2>&1 || pip install pyarrow

echo Checking for tkcalendar...
python -c "import tkcalendar" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing tkcalendar for improved date selection...
    pip install tkcalendar
)

REM Run the GUI
echo Starting application...
start pythonw AnomalyDetectGUI_new.py

exit /b 0

@echo off
setlocal enabledelayedexpansion
echo AIS Shipping Fraud Detection System - Build Script
echo ================================================
echo.

REM Get the script directory
set "SCRIPT_DIR=%~dp0"

REM Check for command line parameter
if not "%1"=="" (
    set CHOICE=%1
    goto PROCESS_CHOICE
)

REM Check for Python installation
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH
    echo Please run Open_to_Begin.py to install Python first.
    pause
    exit /b 1
)

:MENU
cls
echo.
echo AIS Shipping Fraud Detection System - Build Menu
echo -----------------------------------------------
echo.
echo [1] Build Application Executable
echo [2] Build Installer
echo [3] Build Uninstaller
echo [4] Build All Components
echo [5] Exit
echo.
set /p CHOICE=Enter your choice (1-5): 

:PROCESS_CHOICE
if "%CHOICE%"=="1" goto BUILD_EXE
if "%CHOICE%"=="2" goto BUILD_INSTALLER
if "%CHOICE%"=="3" goto BUILD_UNINSTALLER
if "%CHOICE%"=="4" goto BUILD_ALL
if "%CHOICE%"=="5" goto EXIT
echo Invalid choice. Please try again.
timeout /t 2 >nul
goto MENU

:BUILD_EXE
echo.
echo Building Shipping Fraud Detection executable...
echo.
REM Install required packages if not already installed
echo Installing required packages...
python -m pip install pyinstaller pandas numpy dask folium matplotlib seaborn geopy tkcalendar

REM Create the executable
echo Creating executable...
python -m PyInstaller --name="Shipping Fraud Detection" --windowed --onefile ^
  --add-data="shipping_fraud_detection.py;." ^
  --add-data="config.ini;." ^
  --icon="SFD.ico" ^
  --hidden-import=pandas ^
  --hidden-import=numpy ^
  --hidden-import=dask ^
  --hidden-import=folium ^
  --hidden-import=matplotlib ^
  --hidden-import=seaborn ^
  --hidden-import=geopy ^
  --hidden-import=tkcalendar ^
  AnomalyDetectGUI_new.py

echo.
echo Application executable built successfully!
echo Executable located at: %SCRIPT_DIR%dist\Shipping Fraud Detection.exe
echo.
pause
goto MENU

:BUILD_INSTALLER
echo.
echo Building AIS Shipping Fraud Detection System Installer...
echo.
REM Install PyInstaller if not already installed
python -m pip install pyinstaller

REM Build command
echo Creating installer executable...
python -m PyInstaller --clean --name=AIS_Shipping_Fraud_Detection_Installer --add-data="shipping_fraud_detection.py;." --add-data="config.ini;." --add-data="AnomalyDetectGUI_new.py;." --add-data="uninstaller.py;." --add-data="SFD.ico;." --add-data="SFDuninstaller.ico;." --icon="SFD.ico" --onefile installer.py

echo.
echo Installer built successfully!
echo Executable located at: %SCRIPT_DIR%dist\AIS_Shipping_Fraud_Detection_Installer.exe
echo.
pause
goto MENU

:BUILD_UNINSTALLER
echo.
echo Building AIS Shipping Fraud Detection System Uninstaller...
echo.
REM Install PyInstaller if not already installed
python -m pip install pyinstaller

REM Build command
echo Creating uninstaller executable...
python -m PyInstaller --clean --name=AIS_Fraud_Detection_Uninstaller --add-data="config.ini;." --add-data="SFDuninstaller.ico;." --icon="SFDuninstaller.ico" --onefile uninstaller.py

echo.
echo Uninstaller built successfully!
echo Executable located at: %SCRIPT_DIR%dist\AIS_Fraud_Detection_Uninstaller.exe
echo.
pause
goto MENU

:BUILD_ALL
echo.
echo Building all components...
echo.

call :BUILD_EXE_SILENT
call :BUILD_INSTALLER_SILENT
call :BUILD_UNINSTALLER_SILENT

echo.
echo All components have been built successfully!
echo The files can be found in the 'dist' folder.
echo.
pause
goto MENU

:BUILD_EXE_SILENT
echo Step 1: Building Application Executable...
REM Install required packages if not already installed
python -m pip install pyinstaller pandas numpy dask folium matplotlib seaborn geopy tkcalendar >nul 2>&1

REM Create the executable
python -m PyInstaller --name="Shipping Fraud Detection" --windowed --onefile ^
  --add-data="shipping_fraud_detection.py;." ^
  --add-data="config.ini;." ^
  --icon="SFD.ico" ^
  --hidden-import=pandas ^
  --hidden-import=numpy ^
  --hidden-import=dask ^
  --hidden-import=folium ^
  --hidden-import=matplotlib ^
  --hidden-import=seaborn ^
  --hidden-import=geopy ^
  --hidden-import=tkcalendar ^
  AnomalyDetectGUI_new.py >nul 2>&1
echo   - Application executable built successfully
exit /b 0

:BUILD_INSTALLER_SILENT
echo Step 2: Building Installer...
REM Install PyInstaller if not already installed
python -m pip install pyinstaller >nul 2>&1

REM Build command
python -m PyInstaller --clean --name=AIS_Shipping_Fraud_Detection_Installer --add-data="shipping_fraud_detection.py;." --add-data="config.ini;." --add-data="AnomalyDetectGUI_new.py;." --add-data="uninstaller.py;." --add-data="SFD.ico;." --add-data="SFDuninstaller.ico;." --icon="SFD.ico" --onefile installer.py >nul 2>&1
echo   - Installer built successfully
exit /b 0

:BUILD_UNINSTALLER_SILENT
echo Step 3: Building Uninstaller...
REM Install PyInstaller if not already installed
python -m pip install pyinstaller >nul 2>&1

REM Build command
python -m PyInstaller --clean --name=AIS_Fraud_Detection_Uninstaller --add-data="config.ini;." --add-data="SFDuninstaller.ico;." --icon="SFDuninstaller.ico" --onefile uninstaller.py >nul 2>&1
echo   - Uninstaller built successfully
exit /b 0

:EXIT
echo.
echo Thank you for using the AIS Shipping Fraud Detection System Build Tool.
echo.
endlocal
exit /b 0

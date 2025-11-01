@echo off
setlocal enabledelayedexpansion
echo Starting AIS Shipping Fraud Detection System Setup...

:: Check if winget is available before we might need it
where winget >nul 2>&1
set WINGET_AVAILABLE=%ERRORLEVEL%

:: Check if Python is installed
echo Checking for Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 goto PYTHON_NOT_FOUND
goto RUN_SCRIPT

:PYTHON_NOT_FOUND
echo Python is not installed or not in PATH.
echo.

if %WINGET_AVAILABLE% NEQ 0 (
    echo Warning: winget is not available on this system.
    echo You will not be able to automatically install Python.
    echo.
)

:PYTHON_CHOICE
set CHOICE=
set /p CHOICE=Do you want to install Python, continue without it, or exit? (I/C/E): 
if /i "!CHOICE!"=="I" goto INSTALL_PYTHON
if /i "!CHOICE!"=="C" goto CONTINUE_ANYWAY
if /i "!CHOICE!"=="E" goto EXIT_SCRIPT
echo Invalid choice. Please enter I, C, or E.
goto PYTHON_CHOICE

:INSTALL_PYTHON
if %WINGET_AVAILABLE% NEQ 0 (
    echo Cannot install Python: winget is not available.
    echo Please install Python manually, then restart this script.
    pause
    exit /b 1
)
echo Attempting to install Python using winget...
winget install 9NQ7512CXL7T
if !ERRORLEVEL! NEQ 0 (
    echo Failed to install Python. Please install it manually.
    echo.
    goto PYTHON_CHOICE
)
echo Python installation completed. Please restart this batch file.
pause
exit /b

:CONTINUE_ANYWAY
echo Continuing without Python. Some features may not work correctly.
echo.
goto RUN_SCRIPT

:EXIT_SCRIPT
echo Exiting setup.
exit /b 1

:RUN_SCRIPT
:: Check if the Python script exists
if not exist Open_to_Begin.py (
    echo Error: Cannot find Open_to_Begin.py in the current directory.
    echo Current directory: %CD%
    echo.
    echo Please ensure you are running this batch file from the correct location.
    pause
    exit /b 1
)

:: Run the setup script
echo Running Python setup script...
python Open_to_Begin.py
set SCRIPT_RESULT=%ERRORLEVEL%

:: If there was an error, show a message
if %SCRIPT_RESULT% NEQ 0 (
    echo.
    echo An error occurred while running the setup script.
    echo Error code: %SCRIPT_RESULT%
    echo Please check the error message above.
    pause
    exit /b %SCRIPT_RESULT%
) else (
    echo.
    echo Setup completed successfully.
)

endlocal
exit /b 0

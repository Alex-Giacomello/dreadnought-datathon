@echo off
echo Starting Shipping Fraud Detection System...

REM Check if the executable exists in the dist folder
if exist "dist\Shipping Fraud Detection.exe" (
    start "" "dist\Shipping Fraud Detection.exe"
) else (
    REM Check if the executable exists in the current directory
    if exist "Shipping Fraud Detection.exe" (
        start "" "Shipping Fraud Detection.exe"
    ) else (
        echo Error: Executable not found.
        echo Please run build_exe.bat first to create the executable.
        pause
    )
)

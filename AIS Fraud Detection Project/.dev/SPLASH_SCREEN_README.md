# Splash Screen Feature

This document explains the new splash screen feature added to the AIS Fraud Detection application.

## Overview

The splash screen provides a visual indicator that the application is loading when started as an executable (.exe). 
It displays an image (SFDLoad.png) with a progress bar to indicate that the application is loading.

## Files Added

- `splash_screen.py`: Module that handles the splash screen display and progress bar
- `launch_with_splash.py`: Launcher script that shows the splash screen while loading the main app
- `splash_build.spec`: PyInstaller spec file for building the executable with splash screen
- `build_with_splash.py`: Script to build the executable with the splash screen

## Dependencies Added

The following new dependencies were added to support the splash screen:
- **Pillow**: Used for image handling in the splash screen
- **tkhtmlview** and **markdown**: Optional dependencies for README rendering
- **pywin32**: For Windows-specific functionality (only needed on Windows)

## How to Build with Splash Screen

1. Make sure the image file `SFDLoad.png` is placed in the same directory as the application files
2. Run the build script:
   ```
   python build_with_splash.py
   ```
3. The executable will be created in the `dist` folder

## How It Works

1. When the .exe starts, it shows the splash screen with SFDLoad.png and a progress bar
2. The progress bar advances automatically over approximately 45 seconds
3. The main application loads in the background
4. When loading is complete, the splash screen closes and the main application window appears

## Customizing the Splash Screen

- Replace `SFDLoad.png` with your own image (recommended size: 600×400 pixels)
- Adjust timing in `splash_screen.py` if needed (the `time.sleep(0.4)` value in `_simulate_progress`)

## Troubleshooting

If the splash screen doesn't appear or the application doesn't start:

1. Make sure all dependencies are installed:
   ```
   python install_dependencies.py
   ```
2. Verify that the image file exists and is readable
3. Check the build log for any errors

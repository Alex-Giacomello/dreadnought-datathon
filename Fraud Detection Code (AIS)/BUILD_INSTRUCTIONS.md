# AIS Shipping Fraud Detection System Build Instructions

## Build System Overview

The build system for the AIS Shipping Fraud Detection System consists of the following components:

1. `build_all.bat` - Main build script that builds both installer and uninstaller
2. `build_installer_exe.py` - Script to build the installer executable
3. `build_uninstaller_exe.py` - Script to build the uninstaller executable
4. `installer.py` - GUI application for installing the system
5. `uninstaller.py` - GUI application for uninstalling the system

## Build Process

To build the complete system, simply run the `build_all.bat` script. This will:

1. Build the installer executable using PyInstaller
2. Build the uninstaller executable using PyInstaller

The resulting executables will be placed in the `dist` directory.

## Requirements

- Python 3.6 or higher
- PyInstaller (will be automatically installed if missing)
- Required Python packages will be installed by the installer at runtime

## Manual Building

If you want to build the components individually:

1. To build only the installer: `python build_installer_exe.py`
2. To build only the uninstaller: `python build_uninstaller_exe.py`

You can also specify options such as icons:

```
python build_installer_exe.py --icon path/to/icon.ico
python build_uninstaller_exe.py --icon path/to/icon.ico
```

## Cleanup

After building, you can delete the temporary files created by PyInstaller:
- `build` directory
- `*.spec` files

## Notes

- The installer and uninstaller are GUI applications.
- The installer will create desktop shortcuts for both the application and the uninstaller.
- Both installer and uninstaller use the same code structure for consistency.

@echo off
echo Building AIS Shipping Fraud Detection System Installer and Uninstaller...
echo.
echo Building Installer...
python build_installer_exe.py
echo.
echo Building Uninstaller...
python build_uninstaller_exe.py
echo.
echo Build process completed!
pause

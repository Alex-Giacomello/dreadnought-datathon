@echo off
echo Creating desktop shortcut for Shipping Fraud Detection...

REM Get the current directory
set "SCRIPT_DIR=%~dp0"
set "TARGET=%SCRIPT_DIR%Shipping Fraud Detection.bat"
set "SHORTCUT=%USERPROFILE%\Desktop\Shipping Fraud Detection.lnk"

REM Create the shortcut using PowerShell
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT%'); $Shortcut.TargetPath = '%TARGET%'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.Description = 'AIS Shipping Fraud Detection System'; $Shortcut.Save()"

echo Desktop shortcut created successfully.
echo.
pause

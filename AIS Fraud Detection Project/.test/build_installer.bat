@echo off
setlocal enabledelayedexpansion
echo Running build script for Installer...
echo.

REM Call the main build script with parameter 2
call "%~dp0\build.bat" 2

endlocal
exit /b %ERRORLEVEL%

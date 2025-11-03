@echo off
setlocal enabledelayedexpansion
echo Running build script for Uninstaller...
echo.

REM Call the main build script with parameter 3
call "%~dp0\build.bat" 3

endlocal
exit /b %ERRORLEVEL%

@echo off
setlocal enabledelayedexpansion
echo Running build script for Application Executable...
echo.

REM Call the main build script with parameter 1
call "%~dp0\build.bat" 1

endlocal
exit /b %ERRORLEVEL%

@echo off
setlocal enabledelayedexpansion
echo Running build script for All Components...
echo.

REM Call the main build script with parameter 4
call "%~dp0\build.bat" 4

endlocal
exit /b %ERRORLEVEL%

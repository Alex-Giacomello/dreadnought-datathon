#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build script to create an executable installer for AIS Shipping Fraud Detection System
"""

import os
import sys
import subprocess
import shutil
import argparse

def check_pyinstaller():
    """Check if PyInstaller is installed, install if not"""
    try:
        import PyInstaller
        print("PyInstaller is already installed.")
    except ImportError:
        print("PyInstaller not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("PyInstaller installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install PyInstaller: {e}")
            sys.exit(1)

def build_exe(icon=None, onefile=True):
    """Build the executable installer using PyInstaller"""
    # Get the current script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    installer_script = os.path.join(script_dir, "installer.py")
    
    if not os.path.exists(installer_script):
        print(f"Error: Installer script not found at {installer_script}")
        sys.exit(1)
    
    # Build command
    cmd = [
        "pyinstaller",
        "--clean",
        "--name", "AIS_Shipping_Fraud_Detection_Installer",
        "--add-data", f"{script_dir};."
    ]
    
    # Add icon if provided
    if icon and os.path.exists(icon):
        cmd.extend(["--icon", icon])
    
    # Onefile option
    if onefile:
        cmd.append("--onefile")
    
    # Add windowed mode for GUI application
    cmd.append("--windowed")
    
    # Add the main script
    cmd.append(installer_script)
    
    # Run PyInstaller
    print("Building executable with PyInstaller...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd)
        print("Executable built successfully!")
        print(f"Executable located at: {os.path.join(script_dir, 'dist', 'AIS_Shipping_Fraud_Detection_Installer.exe')}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to build executable: {e}")
        sys.exit(1)

def main():
    """Main function to parse arguments and build the executable"""
    parser = argparse.ArgumentParser(description="Build an executable installer for AIS Shipping Fraud Detection System")
    parser.add_argument("--icon", help="Path to an icon file (.ico) to use for the executable", default=None)
    parser.add_argument("--no-onefile", help="Create a directory with multiple files instead of a single executable", action="store_true")
    
    args = parser.parse_args()
    
    # Check if PyInstaller is installed
    check_pyinstaller()
    
    # Build the executable
    build_exe(icon=args.icon, onefile=not args.no_onefile)
    
    print("Build process completed!")

if __name__ == "__main__":
    main()

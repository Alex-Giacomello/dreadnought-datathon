#!/usr/bin/env python3
"""
Dependency installation script for AIS Fraud Detection System

This script installs all the required dependencies for the AIS Fraud Detection System,
including the new splash screen functionality.
"""

import os
import sys
import subprocess
import platform

def install_requirements():
    """Install the required packages from requirements.txt"""
    print("Installing dependencies for AIS Fraud Detection System...")
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    requirements_path = os.path.join(script_dir, "requirements.txt")
    
    if not os.path.exists(requirements_path):
        print(f"Error: requirements.txt not found at {requirements_path}")
        return False
    
    try:
        # Install the requirements using pip
        print("Running pip install...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", requirements_path],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        
        if result.stderr:
            print("Warnings/errors during installation:")
            print(result.stderr)
        
        print("\nAll dependencies installed successfully!")
        
        # Check for optional dependencies
        try:
            import tkhtmlview
        except ImportError:
            print("\nWARNING: tkhtmlview is not installed. README rendering will fall back to plain text.")
            print("To enable markdown rendering, install tkhtmlview manually:")
            print("    pip install tkhtmlview")
        
        try:
            import tkcalendar
        except ImportError:
            print("\nWARNING: tkcalendar is not installed. Date selection will use basic entry fields.")
            print("To enable calendar date picker, install tkcalendar manually:")
            print("    pip install tkcalendar")
            
        try:
            import boto3
        except ImportError:
            print("\nWARNING: boto3 is not installed. AWS S3 functionality will be disabled.")
            print("To enable AWS S3 integration, install boto3 manually:")
            print("    pip install boto3")
            
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        if e.output:
            print(e.output)
        if e.stderr:
            print(e.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error installing dependencies: {e}")
        return False

if __name__ == "__main__":
    install_requirements()
    
    # Check if on Windows and display final message
    if platform.system() == "Windows":
        input("\nPress Enter to exit...")

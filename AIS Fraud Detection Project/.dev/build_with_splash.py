#!/usr/bin/env python3
"""
Build script for AIS Fraud Detection System with splash screen
"""

import os
import sys
import subprocess
import platform
import shutil

def build_executable():
    """Build the executable with PyInstaller"""
    print("Building AIS Fraud Detection System with splash screen...")
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"Using PyInstaller version {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller not installed. Installing now...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Build using our spec file
    spec_path = os.path.join(script_dir, "splash_build.spec")
    
    # Check if the splash image exists
    splash_path = os.path.join(script_dir, "SFDLoad.png")
    if not os.path.exists(splash_path):
        print(f"WARNING: Splash image not found at {splash_path}")
        print("Creating a placeholder splash image...")
        
        # Create a simple placeholder image using PIL
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a blank image with a blue background
            img = Image.new('RGB', (600, 400), color='#003366')
            draw = ImageDraw.Draw(img)
            
            # Add text
            try:
                font = ImageFont.truetype("arial.ttf", 40)
            except:
                font = ImageFont.load_default()
                
            draw.text((150, 150), "AIS Fraud Detection", fill='white', font=font)
            draw.text((180, 220), "Loading...", fill='white', font=font)
            
            # Save the image
            img.save(splash_path)
            print(f"Created placeholder splash image at {splash_path}")
        except Exception as e:
            print(f"Failed to create placeholder image: {e}")
            print("Continuing without splash image...")
    
    # Run PyInstaller with the spec file
    result = subprocess.run([
        sys.executable,
        "-m",
        "PyInstaller",
        spec_path,
        "--clean",
        "--distpath", os.path.join(script_dir, "dist"),
        "--workpath", os.path.join(script_dir, "build"),
    ], check=False)
    
    if result.returncode != 0:
        print(f"ERROR: PyInstaller failed with exit code {result.returncode}")
        return False
    
    print("\nBuild completed successfully!")
    exe_path = os.path.join(script_dir, "dist", "AIS_Fraud_Detection.exe")
    if os.path.exists(exe_path):
        print(f"Executable created at: {exe_path}")
    else:
        print("WARNING: Could not find the built executable.")
    
    return True

if __name__ == "__main__":
    build_executable()

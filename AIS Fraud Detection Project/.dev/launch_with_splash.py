#!/usr/bin/env python3
"""
Launcher script for AIS Fraud Detection Project with splash screen
This will display a splash screen while the main application loads
"""

import os
import sys
import tkinter as tk

def start_app_with_splash():
    """Start the application with a splash screen"""
    try:
        from splash_screen import SplashScreen
    except ImportError:
        print("Error importing splash_screen module. Make sure PIL is installed.")
        # Fall back to direct launch if splash screen fails
        from AnomalyDetectGUI_new import main
        main()
        return
    
    # Find the image path
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running as script
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to SFDLoad.png
    image_path = os.path.join(base_dir, 'SFDLoad.png')
    if not os.path.exists(image_path):
        print(f"Warning: Loading image not found at {image_path}")
    
    def initialize_main_app():
        """Import and initialize the main application"""
        try:
            # Check if there's a 'main' function in AnomalyDetectGUI_new
            from AnomalyDetectGUI_new import main
            main()
        except (ImportError, AttributeError):
            # If not, try to run the main class directly
            from AnomalyDetectGUI_new import AnomalyDetectApp
            app = AnomalyDetectApp()
            global root
            root = app  # Keep reference to prevent garbage collection
    
    # Create and start splash screen
    splash = SplashScreen(image_path, initialize_main_app)
    splash.start_progress()
    splash.mainloop()

if __name__ == "__main__":
    # Add the current directory to sys.path for imports
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.append(script_dir)
        
    start_app_with_splash()

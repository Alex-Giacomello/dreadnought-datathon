#!/usr/bin/env python3
"""
AIS Shipping Fraud Detection System GUI
Integrated version for SFD.py

[VERSION]
Event = Datathon 2025
Team = Dreadnaught
Author = Chris Matherne
version = 1.0 Beta
"""

import os
import sys
import configparser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime
import subprocess
import platform
import logging
import time
import re
import glob
import traceback
import threading
import importlib
import importlib.metadata  # Modern replacement for pkg_resources


def check_dependencies():
    """
    Check if all required dependencies are installed.
    If not, offer to install them from requirements.txt.
    
    Returns:
        bool: True if all dependencies are satisfied, False otherwise
    """
    logger = logging.getLogger("SDF_GUI")
    logger.info("Checking dependencies...")
    
    # Find the requirements.txt file (look in script directory first)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    req_file = os.path.join(script_dir, "requirements.txt")
    
    # If not found in script directory, check current working directory
    if not os.path.exists(req_file):
        req_file = os.path.join(os.getcwd(), "requirements.txt")
        if not os.path.exists(req_file):
            logger.warning("requirements.txt not found in script directory or current working directory")
            return True  # Continue without checking
    
    try:
        # Parse requirements file
        requirements = []
        with open(req_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-e'):
                    # Strip off version specifiers
                    if ';' in line:
                        # Handle platform-specific requirements
                        req, condition = line.split(';', 1)
                        req = req.strip()
                        condition = condition.strip()
                        
                        # Check if this requirement applies to current platform
                        if 'platform_system==' in condition:
                            platform_name = condition.split('==')[1].strip().strip("'").strip('"')
                            if platform.system() != platform_name:
                                continue  # Skip this requirement if platform doesn't match
                    else:
                        req = line
                    
                    if '>=' in req:
                        req = req.split('>=')[0]
                    elif '==' in req:
                        req = req.split('==')[0]
                    elif '<=' in req:
                        req = req.split('<=')[0]
                    
                    req = req.strip()
                    if req:
                        requirements.append(req)
        
        # Check installed packages
        missing = []
        for req in requirements:
            try:
                importlib.import_module(req.lower().replace('-', '_'))
            except ImportError:
                try:
                    # Double-check with importlib.metadata as some package names don't match import names
                    importlib.metadata.version(req)
                except importlib.metadata.PackageNotFoundError:
                    missing.append(req)
        
        if missing:
            logger.warning(f"Missing dependencies: {', '.join(missing)}")
            
            # Show dialog in GUI context
            result = messagebox.askyesno(
                "Missing Dependencies",
                f"The following dependencies are missing: {', '.join(missing)}\n\nWould you like to install them now?"
            )
            
            if result:
                logger.info("Installing missing dependencies...")
                try:
                    # Create a progress dialog
                    progress_window = tk.Toplevel()
                    progress_window.title("Installing Dependencies")
                    progress_window.geometry("400x150")
                    progress_window.transient()
                    progress_window.grab_set()
                    
                    # Add progress label
                    label = ttk.Label(progress_window, text=f"Installing dependencies: {', '.join(missing)}")
                    label.pack(pady=10)
                    
                    # Add progress bar
                    progress = ttk.Progressbar(progress_window, mode="indeterminate")
                    progress.pack(fill="x", padx=20, pady=10)
                    progress.start()
                    
                    # Update function to keep GUI responsive
                    def update_gui():
                        progress_window.update()
                        progress_window.after(100, update_gui)
                    
                    progress_window.after(100, update_gui)
                    
                    # Run pip install
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-r", req_file],
                        capture_output=True,
                        text=True
                    )
                    
                    # Stop progress
                    progress.stop()
                    progress_window.destroy()
                    
                    if result.returncode == 0:
                        messagebox.showinfo(
                            "Installation Complete", 
                            "Dependencies installed successfully!"
                        )
                        logger.info("Dependencies installed successfully!")
                        return True
                    else:
                        logger.error(f"Failed to install dependencies: {result.stderr}")
                        messagebox.showerror(
                            "Installation Failed",
                            f"Failed to install dependencies. Please install them manually:\n\n{result.stderr[:500]}..."
                        )
                        return False
                except Exception as e:
                    logger.error(f"Error installing dependencies: {e}")
                    messagebox.showerror(
                        "Installation Error",
                        f"Error installing dependencies: {str(e)}"
                    )
                    return False
            else:
                logger.warning("User chose not to install missing dependencies")
                messagebox.showwarning(
                    "Missing Dependencies",
                    "Some features may not work without the required dependencies.\nYou can install them manually with:\n\n"
                    f"pip install {' '.join(missing)}"
                )
                return False
        
        logger.info("All dependencies are satisfied.")
        return True
    
    except Exception as e:
        logger.error(f"Error checking dependencies: {e}")
        return True  # Continue anyway

# Import PIL for image processing
try:
    from PIL import Image, ImageTk
    pil_available = True
except ImportError:
    pil_available = False

# Check for tkcalendar
try:
    from tkcalendar import DateEntry
    tkcalendar_available = True
except ImportError:
    tkcalendar_available = False

# Check for AWS boto3
try:
    import boto3
    import botocore.exceptions
    from urllib.parse import urlparse
    aws_available = True
except ImportError:
    aws_available = False

# Import Windows constants if on Windows
if platform.system() == "Windows":
    try:
        import win32con
    except ImportError:
        pass

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ais_fraud_detection_gui.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SDF_GUI")

# Define constants
BATCH_FILE_NAME = "run_sfd.bat"

class ProgressWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Analysis in Progress")
        self.geometry("1000x1200")  # Increased window size
        self.resizable(True, True)  # Allow resizing
        self.transient(parent)
        self.parent = parent
        
        # Load and display the SFDLoad.png image with resizing
        try:
            img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SFDLoad.png")
            if os.path.exists(img_path):
                if pil_available:  # Use PIL to resize if available
                    # Load and resize the image
                    original_img = Image.open(img_path)
                    
                    # Calculate new dimensions (75% of original size)
                    width, height = original_img.size
                    new_width = int(width * 0.75)
                    new_height = int(height * 0.75)
                    
                    # Resize the image
                    resized_img = original_img.resize((new_width, new_height), Image.LANCZOS)
                    
                    # Convert to PhotoImage
                    self.img = ImageTk.PhotoImage(resized_img)
                else:  # Fallback to regular PhotoImage if PIL not available
                    self.img = tk.PhotoImage(file=img_path)
                    
                # Create a frame to better contain the image and add a subtle border
                img_frame = ttk.Frame(self, relief="groove", borderwidth=1)
                img_frame.pack(pady=20, padx=20)  # Increased padding for larger window
                
                # Display the image with better padding
                img_label = ttk.Label(img_frame, image=self.img)
                img_label.pack(padx=10, pady=10)
            else:
                ttk.Label(self, text="Image not found: SFDLoad.png").pack(pady=5)
        except Exception as e:
            ttk.Label(self, text=f"Error loading image: {str(e)}").pack(pady=5)
        
        # Add a header with reduced padding
        ttk.Label(self, text="Analysis Status:", font=("Arial", 11, "bold")).pack(anchor='w', padx=8, pady=(5,0))
        
        # Add a scrolled text widget for progress messages with larger dimensions
        self.log_text = scrolledtext.ScrolledText(self, width=120, height=30, font=("Consolas", 10))
        self.log_text.pack(padx=8, pady=5, fill=tk.BOTH, expand=True)
        
        # Buttons frame with reduced padding
        self.buttons_frame = ttk.Frame(self)
        self.buttons_frame.pack(fill=tk.X, padx=8, pady=5)
        
        # Add a cancel button
        self.cancel_btn = ttk.Button(self.buttons_frame, text="Cancel Analysis", command=self.cancel)
        self.cancel_btn.pack(side=tk.LEFT, padx=3)
        
        # Create an "Open Results" button (hidden initially)
        self.open_results_btn = ttk.Button(self.buttons_frame, text="Open Results Folder", command=self.open_results, state="disabled")
        
        # Create a "Close" button (hidden initially)
        self.close_btn = ttk.Button(self.buttons_frame, text="Close", command=self.destroy, state="disabled")
        
        # Initialize process variable
        self.process = None
        self.canceled = False
        self.output_directory = None
    
    def analysis_complete(self, output_directory):
        """Called when analysis is complete to update the UI"""
        self.output_directory = output_directory
        self.cancel_btn.configure(state="disabled")
        self.open_results_btn.pack(side=tk.LEFT, padx=3)
        self.open_results_btn.configure(state="normal")
        self.close_btn.pack(side=tk.RIGHT, padx=3)
        self.close_btn.configure(state="normal")
    
    def open_results(self):
        """Open the results folder"""
        if self.output_directory and os.path.exists(self.output_directory):
            try:
                if platform.system() == "Windows":
                    os.startfile(self.output_directory)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.call(["open", self.output_directory])
                else:  # Linux
                    subprocess.call(["xdg-open", self.output_directory])
            except Exception:
                messagebox.showerror("Error", f"Could not open folder: {self.output_directory}")
        else:
            messagebox.showerror("Error", "Output directory does not exist.")
    
    def add_message(self, message):
        """Add a message to the log text widget"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)  # Scroll to the end
        self.update()  # Force GUI update
    
    def set_process(self, process):
        """Set the subprocess process"""
        self.process = process
    
    def cancel(self):
        """Cancel the running process"""
        if self.process:
            try:
                self.process.terminate()
                self.add_message("Analysis canceled by user.")
            except Exception as e:
                self.add_message(f"Error canceling process: {str(e)}")
                
        # Try to delete the batch file if it exists
        batch_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), BATCH_FILE_NAME)
        try:
            if os.path.exists(batch_path):
                os.remove(batch_path)
                self.add_message("Temporary batch file removed.")
        except Exception as e:
            self.add_message(f"Could not remove batch file: {e}")
                
        self.canceled = True
        self.destroy()
        
    def withdraw(self):
        """Hide the window but keep it available"""
        super().withdraw()

class SDFGUI:
    def create_collapsible_section(self, parent, title, default_expanded=True):
        """Create a collapsible section with header and content frame"""
        # Create section header
        section_header = ttk.Frame(parent)
        section_header.pack(fill=tk.X, pady=5)
        
        # Create section state variable
        expanded = tk.BooleanVar(value=default_expanded)
        
        # Create content frame
        content_frame = ttk.Frame(parent)
        
        # Define toggle function
        def toggle_section():
            if expanded.get():
                content_frame.pack(fill=tk.X, padx=10, pady=5)
                toggle_btn.configure(text=f"▼ {title}")
            else:
                content_frame.pack_forget()
                toggle_btn.configure(text=f"▶ {title}")
        
        # Create toggle button
        toggle_btn = ttk.Button(
            section_header, 
            text=f"▼ {title}" if default_expanded else f"▶ {title}", 
            command=lambda: [expanded.set(not expanded.get()), toggle_section()]
        )
        toggle_btn.pack(fill=tk.X, padx=10)
        
        # Initial state
        if default_expanded:
            content_frame.pack(fill=tk.X, padx=10, pady=5)
        
        return content_frame
    
    def __init__(self, root):
        self.root = root
        self.root.title("AIS Shipping Fraud Detection System")
        self.root.geometry("1680x840")
        
        # Try to load the banner image
        try:
            # Get the directory of this script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            banner_path = os.path.join(script_dir, "SFD_AI_banner.png")
            
            self.banner_img = tk.PhotoImage(file=banner_path)
            self.banner_label = tk.Label(root, image=self.banner_img)
            self.banner_label.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
            print(f"Loaded banner image from {banner_path}")
        except Exception as e:
            print(f"Warning: Could not load banner image: {e}")
            # Create a text banner instead
            self.banner_label = tk.Label(root, text="AIS SHIPPING FRAUD DETECTION", 
                                    font=("Arial", 16, "bold"), bg="#003366", fg="white", padx=20, pady=15)
            self.banner_label.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        # Create a style for the notebook tabs with rounded top corners and darker borders
        # We need to use ttk.Style().configure directly to style the tabs
        style = ttk.Style()
        
        # Configure the notebook
        style.configure('TNotebook', background='#f0f0f0', borderwidth=2)
        
        # Configure the tabs with darker borders and rounded corners
        style.configure('TNotebook.Tab',
                        padding=[15, 6],  # Increased padding for a better look
                        borderwidth=2,     # Thicker border
                        relief='ridge',    # Ridge relief gives a 3D effect
                        background='#e0e0e0')
        
        # Configure tab states
        style.map('TNotebook.Tab',
                  background=[('selected', '#ffffff'), ('active', '#f0f0f0')],
                  foreground=[('selected', '#000000'), ('active', '#000000')],
                  borderwidth=[('selected', 3), ('active', 2)],
                  relief=[('selected', 'ridge')])
        
        # Apply custom layout for tabs to create rounded corners effect
        # This is the best approximation in tkinter/ttk as it doesn't directly support rounded corners
        # We're using a combination of padding and relief to create a visual effect
        style.layout('TNotebook.Tab', [
            ('Notebook.tab', {
                'sticky': 'nswe',
                'children': [
                    ('Notebook.padding', {
                        'side': 'top',
                        'sticky': 'nswe',
                        'children': [
                            ('Notebook.label', {'side': 'top', 'sticky': ''})],
                    })],
            })
        ])
        
        # Initialize variables
        self.data_directory = tk.StringVar()
        self.output_directory = tk.StringVar(value="C:\\AIS_Data\\Reports")
        
        # Date range variables
        self.start_date = tk.StringVar(value="2024-10-15")  # Default to Oct 15, 2024
        self.end_date = tk.StringVar(value="2024-10-20")  # Default to Oct 20, 2024
        
        # Anomaly types and thresholds
        self.anomaly_types = {
            "AIS Beacon Off": tk.BooleanVar(value=True),
            "AIS Beacon On": tk.BooleanVar(value=True),
            "Excessive Travel Distance (Fast)": tk.BooleanVar(value=True),
            "Excessive Travel Distance (Slow)": tk.BooleanVar(value=True),
            "Course over Ground-Heading Inconsistency": tk.BooleanVar(value=True)
        }
        self.min_travel_nm = tk.DoubleVar(value=200)
        self.max_travel_nm = tk.DoubleVar(value=550)
        self.cog_heading_max_diff = tk.DoubleVar(value=45)
        self.min_speed_for_cog_check = tk.DoubleVar(value=10)
        
        # Output controls variables
        self.output_controls = {
            # Controls which reports and visualizations are generated
            # Statistical analysis reports
            'generate_statistics_excel': tk.BooleanVar(value=True),
            'generate_statistics_csv': tk.BooleanVar(value=True),
            # Visualization maps
            'generate_overall_map': tk.BooleanVar(value=True),
            'generate_vessel_path_maps': tk.BooleanVar(value=True),
            # Charts and visualizations
            'generate_charts': tk.BooleanVar(value=True),
            # Chart types (only used if generate_charts is True)
            'generate_anomaly_type_chart': tk.BooleanVar(value=True),
            'generate_vessel_anomaly_chart': tk.BooleanVar(value=True),
            'generate_date_anomaly_chart': tk.BooleanVar(value=True),
            # Only generate reports for vessels with anomalies
            'filter_to_anomaly_vessels_only': tk.BooleanVar(value=False),
            # Show latitude/longitude grid lines on maps
            'show_lat_long_grid': tk.BooleanVar(value=True),
            # Show vessel heatmaps
            'show_anomaly_heatmap': tk.BooleanVar(value=True)
        }
        
        # Processing options
        self.use_dask = tk.BooleanVar(value=True)
        self.use_gpu = tk.BooleanVar(value=True)
        
        # Analysis Filters
        self.analysis_filters = {
            # Geographic boundaries
            'min_latitude': tk.DoubleVar(value=-90.0),
            'max_latitude': tk.DoubleVar(value=90.0),
            'min_longitude': tk.DoubleVar(value=-180.0),
            'max_longitude': tk.DoubleVar(value=180.0),
            # Time filters
            'time_start_hour': tk.IntVar(value=0),
            'time_end_hour': tk.IntVar(value=24),
            # Confidence and anomaly limits
            'min_confidence': tk.IntVar(value=75),
            'max_anomalies_per_vessel': tk.IntVar(value=10),
            # MMSI filter list (as string)
            'filter_mmsi_list': tk.StringVar(value='')
        }
        
        # S3 variables
        self.use_s3 = tk.BooleanVar(value=False)
        self.s3_data_uri = tk.StringVar(value="s3://ai-dsde-txg-datathon2025/teams/dreadnought/parquet/")
        self.s3_auth_method = tk.StringVar(value="keys") # only keys authentication is supported
        self.s3_access_key = tk.StringVar()
        self.s3_secret_key = tk.StringVar()
        self.s3_session_token = tk.StringVar()
        self.s3_region = tk.StringVar(value="us-east-1")
        self.s3_profile_name = tk.StringVar() # Kept for backward compatibility
        self.s3_role_arn = tk.StringVar() # Kept for backward compatibility
        self.s3_bucket_name = tk.StringVar()
        self.s3_prefix = tk.StringVar()
        self.s3_local_dir = tk.StringVar()
        
        # Ship type variables - using dict with ship type number as key and BooleanVar as value
        self.ship_types = {
            # Wing in ground (WIG)
            20: {'name': 'Wing in ground (WIG), all ships of this type', 'var': tk.BooleanVar(value=True), 'category': 'WIG'},
            21: {'name': 'Wing in ground (WIG), Hazardous category A', 'var': tk.BooleanVar(value=True), 'category': 'WIG'},
            22: {'name': 'Wing in ground (WIG), Hazardous category B', 'var': tk.BooleanVar(value=True), 'category': 'WIG'},
            23: {'name': 'Wing in ground (WIG), Hazardous category C', 'var': tk.BooleanVar(value=True), 'category': 'WIG'},
            24: {'name': 'Wing in ground (WIG), Hazardous category D', 'var': tk.BooleanVar(value=True), 'category': 'WIG'},
            
            # Special craft
            30: {'name': 'Fishing', 'var': tk.BooleanVar(value=True), 'category': 'Special'},
            31: {'name': 'Towing', 'var': tk.BooleanVar(value=True), 'category': 'Special'},
            32: {'name': 'Towing: length exceeds 200m or breadth exceeds 25m', 'var': tk.BooleanVar(value=True), 'category': 'Special'},
            33: {'name': 'Dredging or underwater ops', 'var': tk.BooleanVar(value=True), 'category': 'Special'},
            34: {'name': 'Diving ops', 'var': tk.BooleanVar(value=True), 'category': 'Special'},
            35: {'name': 'Military ops', 'var': tk.BooleanVar(value=True), 'category': 'Special'},
            36: {'name': 'Sailing', 'var': tk.BooleanVar(value=True), 'category': 'Special'},
            37: {'name': 'Pleasure Craft', 'var': tk.BooleanVar(value=True), 'category': 'Special'},
            38: {'name': 'Reserved', 'var': tk.BooleanVar(value=True), 'category': 'Special'},
            39: {'name': 'Reserved', 'var': tk.BooleanVar(value=True), 'category': 'Special'},
            # High speed craft (HSC)
            40: {'name': 'High speed craft (HSC), all ships of this type', 'var': tk.BooleanVar(value=True), 'category': 'HSC'},
            41: {'name': 'High speed craft (HSC), Hazardous category A', 'var': tk.BooleanVar(value=True), 'category': 'HSC'},
            42: {'name': 'High speed craft (HSC), Hazardous category B', 'var': tk.BooleanVar(value=True), 'category': 'HSC'},
            43: {'name': 'High speed craft (HSC), Hazardous category C', 'var': tk.BooleanVar(value=True), 'category': 'HSC'},
            44: {'name': 'High speed craft (HSC), Hazardous category D', 'var': tk.BooleanVar(value=True), 'category': 'HSC'},
            45: {'name': 'High speed craft (HSC), Reserved', 'var': tk.BooleanVar(value=True), 'category': 'HSC'},
            46: {'name': 'High speed craft (HSC), Reserved', 'var': tk.BooleanVar(value=True), 'category': 'HSC'},
            47: {'name': 'High speed craft (HSC), Reserved', 'var': tk.BooleanVar(value=True), 'category': 'HSC'},
            48: {'name': 'High speed craft (HSC), Reserved', 'var': tk.BooleanVar(value=True), 'category': 'HSC'},
            49: {'name': 'High speed craft (HSC), No additional information', 'var': tk.BooleanVar(value=True), 'category': 'HSC'},
            
            # Special purpose
            50: {'name': 'Pilot Vessel', 'var': tk.BooleanVar(value=True), 'category': 'Special Purpose'},
            51: {'name': 'Search and Rescue vessel', 'var': tk.BooleanVar(value=True), 'category': 'Special Purpose'},
            52: {'name': 'Tug', 'var': tk.BooleanVar(value=True), 'category': 'Special Purpose'},
            53: {'name': 'Port Tender', 'var': tk.BooleanVar(value=True), 'category': 'Special Purpose'},
            54: {'name': 'Anti-pollution equipment', 'var': tk.BooleanVar(value=True), 'category': 'Special Purpose'},
            55: {'name': 'Law Enforcement', 'var': tk.BooleanVar(value=True), 'category': 'Special Purpose'},
            56: {'name': 'Spare - Local Vessel', 'var': tk.BooleanVar(value=True), 'category': 'Special Purpose'},
            57: {'name': 'Spare - Local Vessel', 'var': tk.BooleanVar(value=True), 'category': 'Special Purpose'},
            58: {'name': 'Medical Transport', 'var': tk.BooleanVar(value=True), 'category': 'Special Purpose'},
            59: {'name': 'Noncombatant ship (RR Resolution No. 18)', 'var': tk.BooleanVar(value=True), 'category': 'Special Purpose'},
            
            # Passenger
            60: {'name': 'Passenger, all ships of this type', 'var': tk.BooleanVar(value=True), 'category': 'Passenger'},
            61: {'name': 'Passenger, Hazardous category A', 'var': tk.BooleanVar(value=True), 'category': 'Passenger'},
            62: {'name': 'Passenger, Hazardous category B', 'var': tk.BooleanVar(value=True), 'category': 'Passenger'},
            63: {'name': 'Passenger, Hazardous category C', 'var': tk.BooleanVar(value=True), 'category': 'Passenger'},
            64: {'name': 'Passenger, Hazardous category D', 'var': tk.BooleanVar(value=True), 'category': 'Passenger'},
            69: {'name': 'Passenger, No additional information', 'var': tk.BooleanVar(value=True), 'category': 'Passenger'},
            
            # Cargo
            70: {'name': 'Cargo, all ships of this type', 'var': tk.BooleanVar(value=True), 'category': 'Cargo'},
            71: {'name': 'Cargo, Hazardous category A', 'var': tk.BooleanVar(value=True), 'category': 'Cargo'},
            72: {'name': 'Cargo, Hazardous category B', 'var': tk.BooleanVar(value=True), 'category': 'Cargo'},
            73: {'name': 'Cargo, Hazardous category C', 'var': tk.BooleanVar(value=True), 'category': 'Cargo'},
            74: {'name': 'Cargo, Hazardous category D', 'var': tk.BooleanVar(value=True), 'category': 'Cargo'},
            79: {'name': 'Cargo, No additional information', 'var': tk.BooleanVar(value=True), 'category': 'Cargo'},
            
            # Tanker
            80: {'name': 'Tanker, all ships of this type', 'var': tk.BooleanVar(value=True), 'category': 'Tanker'},
            81: {'name': 'Tanker, Hazardous category A', 'var': tk.BooleanVar(value=True), 'category': 'Tanker'},
            82: {'name': 'Tanker, Hazardous category B', 'var': tk.BooleanVar(value=True), 'category': 'Tanker'},
            83: {'name': 'Tanker, Hazardous category C', 'var': tk.BooleanVar(value=True), 'category': 'Tanker'},
            84: {'name': 'Tanker, Hazardous category D', 'var': tk.BooleanVar(value=True), 'category': 'Tanker'},
            89: {'name': 'Tanker, No additional information', 'var': tk.BooleanVar(value=True), 'category': 'Tanker'},
            
            # Other
            90: {'name': 'Other Type, all ships of this type', 'var': tk.BooleanVar(value=True), 'category': 'Other'},
            91: {'name': 'Other Type, Hazardous category A', 'var': tk.BooleanVar(value=True), 'category': 'Other'},
            92: {'name': 'Other Type, Hazardous category B', 'var': tk.BooleanVar(value=True), 'category': 'Other'},
            93: {'name': 'Other Type, Hazardous category C', 'var': tk.BooleanVar(value=True), 'category': 'Other'},
            94: {'name': 'Other Type, Hazardous category D', 'var': tk.BooleanVar(value=True), 'category': 'Other'}
        }
        
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))  # Reduced top padding to account for banner
        
        # Create tabs
        self.create_date_selection_tab()
        self.create_ship_types_tab()
        self.create_anomaly_types_tab()
        self.create_analysis_filters_tab()
        self.create_data_tab()
        self.create_output_controls_tab()
                
        # Create bottom buttons
        self.create_bottom_buttons()
        
        # Make sure all ship types are selected by default
        for ship_type in self.ship_types:
            self.ship_types[ship_type]['var'].set(True)
            
        # Load config if exists
        self.load_config()
        
    def create_date_selection_tab(self):
        """Create the Startup tab with descriptive text and date range settings"""
        date_selection_frame = ttk.Frame(self.notebook)
        self.notebook.add(date_selection_frame, text="Startup")
        
        # Add descriptive text at the top
        desc_frame = ttk.Frame(date_selection_frame)
        desc_frame.grid(row=0, column=0, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=5)
        
        desc_text = """This system analyzes Automatic Identification System (AIS) data to detect potentially fraudulent shipping activities. It does so by identifing anomalies such as vessels turning off their AIS beacons (sudden disappearances), sudden reappearances, unusual travel distances, and large inconsistencies between reported Course Over Ground (COG) and Heading.  Users have the option of examining data over specific date ranges, or examining data leading up to the current date.  
NOTE: In this test implementation only data from OCT 2024 to MAR 2025 is available for use.

Select the time period on this tab and press the Run Analysis button to execute your inquery.  You can select the specific types of ships and anomalies you want to search for in those tabs.  The Data and Results folders can be set on the Advanced Tab."""
        
        desc_label = ttk.Label(desc_frame, text=desc_text, wraplength=750, justify="left")
        desc_label.pack(fill=tk.X, padx=10, pady=10)
        
        # Time Range Selection Frame
        time_frame = ttk.LabelFrame(date_selection_frame, text="Time Range Selection")
        time_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=10)
        
        # Date range label
        ttk.Label(time_frame, text="Date Range Selection", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5, columnspan=3)
        
        date_range_frame = ttk.Frame(time_frame)
        date_range_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Check if tkcalendar is available
        if tkcalendar_available:
            ttk.Label(date_range_frame, text="Start Date:").pack(side=tk.LEFT, padx=2)
            self.start_date_picker = DateEntry(date_range_frame, width=12, background='darkblue',
                                             foreground='white', borderwidth=2, date_pattern='y-mm-dd',
                                             state='readonly')
            self.start_date_picker.pack(side=tk.LEFT, padx=2)
            
            ttk.Label(date_range_frame, text="End Date:").pack(side=tk.LEFT, padx=2)
            self.end_date_picker = DateEntry(date_range_frame, width=12, background='darkblue',
                                           foreground='white', borderwidth=2, date_pattern='y-mm-dd',
                                           state='readonly')
            self.end_date_picker.pack(side=tk.LEFT, padx=2)
            
            # Set default dates to Oct 15-20, 2024
            self.start_date_picker.set_date(datetime(2024, 10, 15).date())
            self.end_date_picker.set_date(datetime(2024, 10, 20).date())
        else:
            # If tkcalendar is not available, use basic entry fields with validation
            self.date_warning = ttk.Label(date_range_frame, 
                                        text="Warning: tkcalendar not installed. Using basic date fields.",
                                        foreground='red')
            self.date_warning.pack(side=tk.TOP, pady=2)
            
            date_fields_frame = ttk.Frame(date_range_frame)
            date_fields_frame.pack(side=tk.TOP)
            
            ttk.Label(date_fields_frame, text="Start Date (YYYY-MM-DD):").pack(side=tk.LEFT, padx=2)
            self.start_date_entry = ttk.Entry(date_fields_frame, textvariable=self.start_date, width=12)
            self.start_date_entry.pack(side=tk.LEFT, padx=2)
            
            ttk.Label(date_fields_frame, text="End Date (YYYY-MM-DD):").pack(side=tk.LEFT, padx=2)
            self.end_date_entry = ttk.Entry(date_fields_frame, textvariable=self.end_date, width=12)
            self.end_date_entry.pack(side=tk.LEFT, padx=2)
            
            # Recommendation to install tkcalendar
            ttk.Label(time_frame, text="For better date selection, install tkcalendar: pip install tkcalendar",
                     foreground='blue').grid(row=2, column=0, columnspan=3, sticky=tk.W, padx=5, pady=2)
        
        # Add buttons frame below time range selection
        button_frame = ttk.Frame(date_selection_frame)
        button_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=20)
        
        ttk.Button(button_frame, text="Save Configuration", command=self.save_config).pack(side=tk.LEFT, padx=5, pady=10)
        ttk.Button(button_frame, text="Run Analysis", command=self.run_analysis).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.root.destroy).pack(side=tk.RIGHT, padx=5)
    
    def create_ship_types_tab(self):
        """Create the Ship Types tab with checkboxes for each ship type"""
        ship_types_frame = ttk.Frame(self.notebook)
        self.notebook.add(ship_types_frame, text="Ship Types")
        
        # Create a canvas with scrollbar for the ship types
        canvas = tk.Canvas(ship_types_frame, width=750)
        scrollbar = ttk.Scrollbar(ship_types_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Instructions and title
        ttk.Label(scrollable_frame, text="Select ship types to include in analysis:", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=10, columnspan=3)
        
        # Group the ship types by category
        categories = {}
        for ship_type, details in self.ship_types.items():
            category = details.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append(ship_type)
            
        # Create frames for each category
        row = 1
        col = 0
        max_columns = 3  # Maximum columns in grid
        
        for category, ship_types_list in sorted(categories.items()):
            # Create a frame for this category
            category_frame = ttk.LabelFrame(scrollable_frame, text=f"{category} Ships")
            category_frame.grid(row=row, column=col, sticky=tk.W, padx=10, pady=5)
            
            # Add checkboxes for each ship type in this category
            frame_row = 0
            for ship_type in sorted(ship_types_list):
                ttk.Checkbutton(
                    category_frame, 
                    text=f"{ship_type}: {self.ship_types[ship_type]['name']}",
                    variable=self.ship_types[ship_type]['var']
                ).grid(row=frame_row, column=0, sticky=tk.W, padx=5, pady=3)
                frame_row += 1
                
            # Move to next column or row
            col += 1
            if col >= max_columns:
                col = 0
                row += 1
        
        # Add select all/none buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=row + 1, column=0, columnspan=max_columns, pady=10)
        
        # Add category-specific select/deselect buttons
        categories_added = []
        for category in sorted(categories.keys()):
            if category not in categories_added:
                select_method = getattr(self, f"select_all_{category.lower().replace(' ', '_')}", None)
                deselect_method = getattr(self, f"deselect_all_{category.lower().replace(' ', '_')}", None)
                
                if select_method is None:
                    # Create method dynamically if it doesn't exist
                    setattr(self, f"select_all_{category.lower().replace(' ', '_')}", lambda c=category: self.select_category(c))
                    select_method = getattr(self, f"select_all_{category.lower().replace(' ', '_')}")
                    
                if deselect_method is None:
                    # Create method dynamically if it doesn't exist
                    setattr(self, f"deselect_all_{category.lower().replace(' ', '_')}", lambda c=category: self.deselect_category(c))
                    deselect_method = getattr(self, f"deselect_all_{category.lower().replace(' ', '_')}")
                
                ttk.Button(button_frame, text=f"Select All {category}", command=select_method).pack(side=tk.LEFT, padx=5)
                ttk.Button(button_frame, text=f"Deselect All {category}", command=deselect_method).pack(side=tk.LEFT, padx=5)
                categories_added.append(category)
        
        # Add overall select/deselect buttons
        ttk.Button(button_frame, text="Select All", command=self.select_all_ships).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Deselect All", command=self.deselect_all_ships).pack(side=tk.LEFT, padx=5)
    
    def select_all_cargo(self):
        """Select all cargo ship types"""
        for ship_type in range(70, 80):
            self.ship_types[ship_type]['var'].set(True)
    
    def deselect_all_cargo(self):
        """Deselect all cargo ship types"""
        for ship_type in range(70, 80):
            self.ship_types[ship_type]['var'].set(False)
    
    def select_all_tanker(self):
        """Select all tanker ship types"""
        for ship_type in range(80, 90):
            self.ship_types[ship_type]['var'].set(True)
    
    def deselect_all_tanker(self):
        """Deselect all tanker ship types"""
        for ship_type in range(80, 90):
            self.ship_types[ship_type]['var'].set(False)
    
    def select_all_ships(self):
        """Select all ship types"""
        for ship_type in self.ship_types:
            self.ship_types[ship_type]['var'].set(True)
    
    def deselect_all_ships(self):
        """Deselect all ship types"""
        for ship_type in self.ship_types:
            self.ship_types[ship_type]['var'].set(False)
            
    def select_category(self, category):
        """Select all ships of a specific category"""
        for ship_type, details in self.ship_types.items():
            if details.get('category', '') == category:
                self.ship_types[ship_type]['var'].set(True)
                
    def deselect_category(self, category):
        """Deselect all ships of a specific category"""
        for ship_type, details in self.ship_types.items():
            if details.get('category', '') == category:
                self.ship_types[ship_type]['var'].set(False)
    
    def create_anomaly_types_tab(self):
        """Create the Anomaly Types tab with checkboxes for each type and thresholds"""
        anomaly_frame = ttk.Frame(self.notebook)
        self.notebook.add(anomaly_frame, text="Anomaly Types")
        
        # Left panel - anomaly types selection
        types_frame = ttk.LabelFrame(anomaly_frame, text="Select Anomaly Types to Detect")
        types_frame.grid(row=0, column=0, sticky=tk.N+tk.W, padx=10, pady=10)
        
        # Create checkboxes for each anomaly type
        for i, (anomaly_type, var) in enumerate(self.anomaly_types.items()):
            ttk.Checkbutton(types_frame, text=anomaly_type, variable=var).grid(row=i, column=0, sticky=tk.W, padx=20, pady=5)
            
        # Add "Select All" buttons
        button_frame = ttk.Frame(types_frame)
        button_frame.grid(row=len(self.anomaly_types), column=0, sticky=tk.W, padx=5, pady=10, columnspan=2)
        ttk.Button(button_frame, text="Select All", command=self.select_all_anomalies).grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Button(button_frame, text="Deselect All", command=self.deselect_all_anomalies).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Right panel - thresholds
        thresholds_frame = ttk.LabelFrame(anomaly_frame, text="Anomaly Detection Thresholds")
        thresholds_frame.grid(row=0, column=1, sticky=tk.N+tk.W, padx=10, pady=10)
        
        # Travel distance thresholds
        ttk.Label(thresholds_frame, text="Travel Distance Thresholds (nautical miles):", font=("", 12)).grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=5, pady=10)
        
        ttk.Label(thresholds_frame, text="Minimum (below this is 'Slow'):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(thresholds_frame, textvariable=self.min_travel_nm, width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(thresholds_frame, text="Maximum (above this is 'Fast'):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(thresholds_frame, textvariable=self.max_travel_nm, width=10).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # COG-Heading thresholds
        ttk.Label(thresholds_frame, text="COG-Heading Inconsistency Thresholds:", font=("", 12)).grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=10)
        
        ttk.Label(thresholds_frame, text="Maximum difference (degrees):").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(thresholds_frame, textvariable=self.cog_heading_max_diff, width=10).grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(thresholds_frame, text="Minimum speed for check (knots):").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(thresholds_frame, textvariable=self.min_speed_for_cog_check, width=10).grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)
    
    def select_all_anomalies(self):
        """Select all anomaly types"""
        for var in self.anomaly_types.values():
            var.set(True)

    def deselect_all_anomalies(self):
        """Deselect all anomaly types"""
        for var in self.anomaly_types.values():
            var.set(False)
            
    def create_analysis_filters_tab(self):
        """Create the Analysis Filters tab with settings for filtering analysis"""
        filters_frame = ttk.Frame(self.notebook)
        self.notebook.add(filters_frame, text="Analysis Filters")
        
        # Create a canvas with scrollbar for the filters tab
        canvas = tk.Canvas(filters_frame, width=750)
        scrollbar = ttk.Scrollbar(filters_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Geographic Boundaries Section
        geo_frame = ttk.LabelFrame(scrollable_frame, text="Geographic Boundaries")
        geo_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Latitude controls
        lat_frame = ttk.Frame(geo_frame)
        lat_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(lat_frame, text="Latitude Range:").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        min_lat_frame = ttk.Frame(lat_frame)
        min_lat_frame.grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Label(min_lat_frame, text="Min:").pack(side=tk.LEFT)
        ttk.Entry(min_lat_frame, textvariable=self.analysis_filters['min_latitude'], width=8).pack(side=tk.LEFT)
        
        max_lat_frame = ttk.Frame(lat_frame)
        max_lat_frame.grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Label(max_lat_frame, text="Max:").pack(side=tk.LEFT)
        ttk.Entry(max_lat_frame, textvariable=self.analysis_filters['max_latitude'], width=8).pack(side=tk.LEFT)
        
        # Longitude controls
        lon_frame = ttk.Frame(geo_frame)
        lon_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(lon_frame, text="Longitude Range:").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        min_lon_frame = ttk.Frame(lon_frame)
        min_lon_frame.grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Label(min_lon_frame, text="Min:").pack(side=tk.LEFT)
        ttk.Entry(min_lon_frame, textvariable=self.analysis_filters['min_longitude'], width=8).pack(side=tk.LEFT)
        
        max_lon_frame = ttk.Frame(lon_frame)
        max_lon_frame.grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Label(max_lon_frame, text="Max:").pack(side=tk.LEFT)
        ttk.Entry(max_lon_frame, textvariable=self.analysis_filters['max_longitude'], width=8).pack(side=tk.LEFT)
        
        # Time Filters Section
        time_frame = ttk.LabelFrame(scrollable_frame, text="Time Filters")
        time_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Hour range controls
        hour_frame = ttk.Frame(time_frame)
        hour_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(hour_frame, text="Hour of Day Range (0-24):").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        start_hour_frame = ttk.Frame(hour_frame)
        start_hour_frame.grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Label(start_hour_frame, text="Start:").pack(side=tk.LEFT)
        ttk.Entry(start_hour_frame, textvariable=self.analysis_filters['time_start_hour'], width=5).pack(side=tk.LEFT)
        
        end_hour_frame = ttk.Frame(hour_frame)
        end_hour_frame.grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Label(end_hour_frame, text="End:").pack(side=tk.LEFT)
        ttk.Entry(end_hour_frame, textvariable=self.analysis_filters['time_end_hour'], width=5).pack(side=tk.LEFT)
        
        # Anomaly Filtering Section
        anomaly_frame = ttk.LabelFrame(scrollable_frame, text="Anomaly Filtering")
        anomaly_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Confidence threshold
        conf_frame = ttk.Frame(anomaly_frame)
        conf_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(conf_frame, text="Minimum Confidence Level (0-100):").pack(side=tk.LEFT, padx=5)
        ttk.Entry(conf_frame, textvariable=self.analysis_filters['min_confidence'], width=5).pack(side=tk.LEFT, padx=5)
        
        # Max anomalies per vessel
        max_anom_frame = ttk.Frame(anomaly_frame)
        max_anom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(max_anom_frame, text="Maximum Anomalies Per Vessel:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(max_anom_frame, textvariable=self.analysis_filters['max_anomalies_per_vessel'], width=5).pack(side=tk.LEFT, padx=5)
        
        # MMSI Filter Section
        mmsi_frame = ttk.LabelFrame(scrollable_frame, text="MMSI Filtering")
        mmsi_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # MMSI list input
        mmsi_input_frame = ttk.Frame(mmsi_frame)
        mmsi_input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(mmsi_input_frame, text="Filter by MMSI (comma-separated, leave empty for all):").pack(anchor=tk.W, padx=5)
        ttk.Entry(mmsi_input_frame, textvariable=self.analysis_filters['filter_mmsi_list'], width=50).pack(fill=tk.X, padx=5, pady=5)
        
        # Note: Anomaly Filter Toggles Section has been removed
        
        # Help text
        help_frame = ttk.Frame(scrollable_frame)
        help_frame.pack(fill=tk.X, padx=10, pady=10)
        
        help_text = """Analysis Filters allow you to narrow down the scope of the analysis by geographical area, 
        time of day, and specific vessels. You can also set the minimum confidence threshold for anomaly detection 
        and limit the number of anomalies reported per vessel. All anomaly types are now automatically enabled."""
        
        ttk.Label(help_frame, text=help_text, wraplength=700, justify="left").pack(anchor=tk.W, padx=5, pady=5)
            
    def create_data_tab(self):
        """Create the Data tab with additional settings and collapsible sections"""
        advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(advanced_frame, text="Data")
        
        # Create a canvas with scrollbar for the advanced tab
        canvas = tk.Canvas(advanced_frame, width=750)
        scrollbar = ttk.Scrollbar(advanced_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # File Locations Section
        file_frame = self.create_collapsible_section(scrollable_frame, "File Locations", True)
        
        # Data Directory
        ttk.Label(file_frame, text="Data Directory:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(file_frame, textvariable=self.data_directory, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="Browse...", command=self.browse_data_directory).grid(row=0, column=2, padx=5, pady=5)
        
        # Output Directory
        ttk.Label(file_frame, text="Output Directory:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(file_frame, textvariable=self.output_directory, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="Browse...", command=self.browse_output_directory).grid(row=1, column=2, padx=5, pady=5)
        
        # Data Source Selection Section
        data_source_frame = self.create_collapsible_section(scrollable_frame, "Data Source Selection", True)
        
        # Radio buttons for data source selection
        self.data_source = tk.StringVar(value="local")
        ttk.Radiobutton(data_source_frame, text="Use Local Data Folder", variable=self.data_source, 
                       value="local", command=self.toggle_data_source).pack(anchor=tk.W, padx=15, pady=5)
            
        ttk.Radiobutton(data_source_frame, text="Use AWS S3 Data Bucket", variable=self.data_source, 
                       value="s3", command=self.toggle_data_source,
                       state="normal" if aws_available else "disabled").pack(anchor=tk.W, padx=15, pady=5)
        
        # S3 Settings Section
        s3_frame = self.create_collapsible_section(scrollable_frame, "Amazon S3 Settings", True)
        
        # Check if boto3 is available
        if not aws_available:
            ttk.Label(s3_frame, text="AWS boto3 library not installed. Install with: pip install boto3", 
                     foreground="red").pack(anchor=tk.W, padx=15, pady=5)
            self.s3_frame_row = 1
        else:
            self.s3_frame_row = 0
        
        # S3 Bucket Configuration
        bucket_frame = ttk.Frame(s3_frame)
        bucket_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create rows for each input
        uri_row = ttk.Frame(bucket_frame)
        uri_row.pack(fill=tk.X, pady=5)
        
        bucket_row = ttk.Frame(bucket_frame)
        bucket_row.pack(fill=tk.X, pady=5)
        
        prefix_row = ttk.Frame(bucket_frame)
        prefix_row.pack(fill=tk.X, pady=5)
        
        # S3 URI (derived from bucket and prefix)
        ttk.Label(uri_row, text="S3 URI:", width=12).pack(side=tk.LEFT, padx=5)
        self.s3_uri_entry = ttk.Entry(uri_row, textvariable=self.s3_data_uri, width=60)
        self.s3_uri_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Bucket name
        ttk.Label(bucket_row, text="Bucket Name:", width=12).pack(side=tk.LEFT, padx=5)
        self.bucket_name_entry = ttk.Entry(bucket_row, textvariable=self.s3_bucket_name, width=40)
        self.bucket_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.s3_bucket_name.set("ai-dsde-txg-datathon2025")
        
        # Prefix
        ttk.Label(prefix_row, text="Prefix:", width=12).pack(side=tk.LEFT, padx=5)
        self.prefix_entry = ttk.Entry(prefix_row, textvariable=self.s3_prefix, width=40)
        self.prefix_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.s3_prefix.set("teams/dreadnought/parquet/")
        
        # Auto-update S3 URI when bucket or prefix changes
        def update_s3_uri(*args):
            bucket = self.s3_bucket_name.get()
            prefix = self.s3_prefix.get()
            if bucket:
                self.s3_data_uri.set(f"s3://{bucket}/{prefix}")
        
        # Register trace callbacks
        self.s3_bucket_name.trace_add("write", update_s3_uri)
        self.s3_prefix.trace_add("write", update_s3_uri)
        
        # Add callback for credential changes (auto-saving removed)
        def save_aws_changes(*args):
            # This function previously auto-saved the config on each change
            # Now we just update the UI as needed but don't save to config.ini
            pass
        
        # Register callbacks for credential changes to save config
        self.s3_access_key.trace_add("write", save_aws_changes)
        self.s3_secret_key.trace_add("write", save_aws_changes)
        self.s3_session_token.trace_add("write", save_aws_changes)
        self.s3_region.trace_add("write", save_aws_changes)
        self.s3_auth_method.trace_add("write", save_aws_changes)
        
        # Initial update
        update_s3_uri()
        
        # AWS Authentication using Access Keys
        ttk.Label(s3_frame, text="AWS Authentication Details (Access Keys):").pack(anchor=tk.W, padx=5, pady=5)
        
        auth_keys_frame = ttk.Frame(s3_frame)
        auth_keys_frame.pack(fill=tk.X, padx=15, pady=5)
        
        # Create rows for each authentication input
        access_key_row = ttk.Frame(auth_keys_frame)
        access_key_row.pack(fill=tk.X, pady=3)
        
        secret_key_row = ttk.Frame(auth_keys_frame)
        secret_key_row.pack(fill=tk.X, pady=3)
        
        token_row = ttk.Frame(auth_keys_frame)
        token_row.pack(fill=tk.X, pady=3)
        
        # Access Key
        ttk.Label(access_key_row, text="Access Key:", width=12).pack(side=tk.LEFT, padx=5)
        self.access_key_entry = ttk.Entry(access_key_row, textvariable=self.s3_access_key, width=40)
        self.access_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Secret Key
        ttk.Label(secret_key_row, text="Secret Key:", width=12).pack(side=tk.LEFT, padx=5)
        self.secret_key_entry = ttk.Entry(secret_key_row, textvariable=self.s3_secret_key, width=40, show="*")
        self.secret_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Session Token - Expanded width to handle very long tokens
        ttk.Label(token_row, text="Session Token:", width=12).pack(side=tk.LEFT, padx=5)
        self.token_entry = ttk.Entry(token_row, textvariable=self.s3_session_token, width=60)
        self.token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Advanced Authentication Options
        # Toggle for advanced auth options (region)
        self.show_advanced_auth = tk.BooleanVar(value=False)
        ttk.Checkbutton(s3_frame, text="Show advanced authentication options", 
                      variable=self.show_advanced_auth, command=self.toggle_advanced_auth).pack(
            anchor=tk.W, padx=5, pady=(15,5))
            
        # Advanced Authentication frame
        self.advanced_auth_frame = ttk.Frame(s3_frame)
        # Don't pack it initially - will be managed by toggle_advanced_auth
        
        # Create frames for each row in advanced auth frame
        # Keys are the only auth method, so we don't need auth method selection UI
        
        region_row = ttk.Frame(self.advanced_auth_frame)
        region_row.pack(fill=tk.X, pady=3)
        
        # Keys are the only supported authentication method
        
        # Region settings
        ttk.Label(region_row, text="AWS Region:", width=12).pack(side=tk.LEFT, padx=5)
        self.region_entry = ttk.Entry(region_row, textvariable=self.s3_region, width=20)
        self.region_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Test Connection Button
        button_frame = ttk.Frame(s3_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.test_s3_button = ttk.Button(button_frame, text="Test S3 Connection", 
                                      command=self.test_s3_connection,
                                      state="normal" if aws_available else "disabled")
        self.test_s3_button.pack(side=tk.RIGHT, padx=15)
        
        # Add Processing Options Section
        processing_frame = self.create_collapsible_section(scrollable_frame, "Processing Options", False)
        
        # Dask option
        dask_option = ttk.Frame(processing_frame)
        dask_option.pack(fill=tk.X, pady=5)
        
        ttk.Checkbutton(dask_option, text="Use Dask for distributed processing", 
                        variable=self.use_dask).pack(anchor=tk.W, padx=15)
        
        # GPU option
        self.gpu_option_frame = ttk.Frame(processing_frame)
        self.gpu_option_frame.pack(fill=tk.X, pady=5)
        
        self.use_gpu = tk.BooleanVar(value=True)  # Default to True, will be disabled if not available
        ttk.Checkbutton(self.gpu_option_frame, text="Use GPU acceleration if available", 
                        variable=self.use_gpu, command=self.check_gpu_support).pack(anchor=tk.W, padx=15)
        
        # Add an install button for GPU support
        self.gpu_status_label = ttk.Label(self.gpu_option_frame, text="GPU status: Checking...")
        self.gpu_status_label.pack(anchor=tk.W, padx=15, pady=2)
        
        self.install_gpu_button = ttk.Button(self.gpu_option_frame, text="Install GPU Support", command=self.install_gpu_packages)
        # Initially hide the button until we check GPU status
        # self.install_gpu_button.pack(anchor=tk.W, padx=15, pady=2)
        
        # Add note label placeholder
        self.gpu_note_label = ttk.Label(self.gpu_option_frame, 
                                     text="Note: GPU acceleration is optional. The application will run without it.")
        
        # Check GPU status on startup
        self.root.after(1000, self.check_gpu_support)
        
        # Initialize the auth method settings
        self.toggle_auth_method()
        
        # Initialize S3 settings
        self.toggle_s3_settings()
    
    def create_output_controls_tab(self):
        """Create the Output Controls tab with checkboxes for each output"""
        output_controls_frame = ttk.Frame(self.notebook)
        self.notebook.add(output_controls_frame, text="Output Controls")
        
        # Output Controls section
        controls_frame = ttk.LabelFrame(output_controls_frame, text="Select Report Outputs")
        controls_frame.grid(row=0, column=0, sticky=tk.N+tk.W, padx=10, pady=10)
        
        # Group the controls by type for better organization
        groups = {
            "Reports": ["generate_statistics_excel", "generate_statistics_csv"],
            "Maps": ["generate_overall_map", "generate_vessel_path_maps", "show_lat_long_grid", "show_anomaly_heatmap"],
            "Charts": ["generate_charts", "generate_anomaly_type_chart", "generate_vessel_anomaly_chart", "generate_date_anomaly_chart"],
            "Filtering": ["filter_to_anomaly_vessels_only"]
        }
        
        row = 0
        # Add section headers and checkboxes for each group
        for group_name, control_keys in groups.items():
            ttk.Label(controls_frame, text=f"{group_name}:", font=("Arial", 10, "bold")).grid(
                row=row, column=0, sticky=tk.W, padx=5, pady=(10, 5))
            row += 1
            
            for key in control_keys:
                if key in self.output_controls:
                    # Create a more readable label from the key
                    label = " ".join(word.capitalize() for word in key.replace("generate_", "").split("_"))
                    ttk.Checkbutton(controls_frame, text=label, variable=self.output_controls[key]).grid(
                        row=row, column=0, sticky=tk.W, padx=20, pady=3)
                    row += 1
        
        # Add "Select All" buttons
        button_frame = ttk.Frame(controls_frame)
        button_frame.grid(row=row, column=0, sticky=tk.W, padx=5, pady=10, columnspan=2)
        ttk.Button(button_frame, text="Select All", command=self.select_all_output_controls).grid(
            row=0, column=0, sticky=tk.W, padx=5)
        ttk.Button(button_frame, text="Deselect All", command=self.deselect_all_output_controls).grid(
            row=0, column=1, sticky=tk.W, padx=5)
        

    def select_all_output_controls(self):
        """Select all output controls"""
        for var in self.output_controls.values():
            var.set(True)

    def deselect_all_output_controls(self):
        """Deselect all output controls"""
        for var in self.output_controls.values():
            var.set(False)

    def browse_data_directory(self):
        """Open file dialog to select data directory"""
        directory = filedialog.askdirectory()
        if directory:
            self.data_directory.set(directory)

    def browse_output_directory(self):
        """Open file dialog to select output directory"""
        directory = filedialog.askdirectory()
        if directory:
            self.output_directory.set(directory)
    
    def check_gpu_support(self):
        """Check if GPU support packages are available"""
        gpu_available = False
        missing_packages = []
        
        # Check for each GPU package
        for package in ["cudf", "cupy", "cuml"]:
            try:
                importlib.import_module(package)
            except ImportError:
                missing_packages.append(package)
        
        # Update the use_gpu checkbox state based on what's installed
        # This doesn't change the user's preference, just informs them of capability
        
        if not missing_packages:
            self.gpu_status_label.config(text="GPU status: Support available - acceleration enabled")
            if hasattr(self, 'install_gpu_button') and self.install_gpu_button.winfo_ismapped():
                self.install_gpu_button.pack_forget()
            gpu_available = True
        else:
            # Check if conda is available
            conda_available = self.is_conda_available()
            if conda_available:
                self.gpu_status_label.config(text=f"GPU status: Optional acceleration not available (Conda available)")
            else:
                self.gpu_status_label.config(text=f"GPU status: Optional acceleration not available (using pip)")
                
            # Show the install button if packages are missing
            if hasattr(self, 'install_gpu_button') and not self.install_gpu_button.winfo_ismapped():
                self.install_gpu_button.pack(anchor=tk.W, padx=15, pady=2)
                
            # Add note about GPU being optional
            if not hasattr(self, 'gpu_note_label') or not self.gpu_note_label.winfo_ismapped():
                self.gpu_note_label = ttk.Label(self.gpu_option_frame, 
                                              text="Note: GPU acceleration is optional. The application will run without it.")
                self.gpu_note_label.pack(anchor=tk.W, padx=15, pady=(0, 5))
        
        return gpu_available
        
    def is_conda_available(self):
        """Check if conda is available in PATH"""
        try:
            # Check if conda is in PATH
            result = subprocess.run(['conda', '--version'], 
                                  capture_output=True, text=True, check=False)
            return result.returncode == 0
        except:
            return False
    
    def install_gpu_packages(self):
        """Install GPU support packages"""
        try:
            # Create progress window
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Installing GPU Support")
            progress_window.geometry("400x200")
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            # Add status label
            status_label = ttk.Label(progress_window, text="Installing GPU support packages...")
            status_label.pack(pady=10)
            
            # Add progress bar
            progress = ttk.Progressbar(progress_window, mode="indeterminate")
            progress.pack(fill="x", padx=20, pady=10)
            progress.start()
            
            # Add log text area
            log_text = scrolledtext.ScrolledText(progress_window, height=5)
            log_text.pack(fill="both", expand=True, padx=20, pady=10)
            
            def update_log(message):
                log_text.insert(tk.END, message + "\n")
                log_text.see(tk.END)
                log_text.update()
            
            # Define installation function to run in thread
            def run_installation():
                installation_success = False
                conda_available = self.is_conda_available()
                
                # Try conda installation first if available
                if conda_available:
                    update_log("Conda detected - attempting to install RAPIDS using conda...")
                    try:
                        # Try to install RAPIDS using conda
                        cmd = ["conda", "install", "-y", "-c", "rapidsai", "-c", "conda-forge", "-c", "nvidia", 
                               "cudf", "cuml", "cupy"]
                        process = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if process.returncode == 0:
                            installation_success = True
                            update_log("Successfully installed RAPIDS using conda!")
                        else:
                            update_log(f"Failed to install with conda: {process.stderr}")
                            update_log("Falling back to pip installation...")
                    except Exception as e:
                        update_log(f"Error during conda installation: {str(e)}")
                        update_log("Falling back to pip installation...")
                else:
                    update_log("Conda not found - using pip for installation")
                
                # Fall back to pip with lower version requirements if conda failed or is not available
                if not installation_success:
                    update_log("Attempting to install RAPIDS using pip with lower version requirements...")
                    
                    # Packages to install with lower version requirements
                    gpu_packages = ["cudf<1.0", "cupy<8.0", "cuml<1.0"]
                    pip_success = True
                    
                    for package in gpu_packages:
                        update_log(f"Installing {package}...")
                        try:
                            # Use pip to install the package
                            process = subprocess.run(
                                [sys.executable, "-m", "pip", "install", package],
                                capture_output=True,
                                text=True
                            )
                            
                            if process.returncode != 0:
                                pip_success = False
                                update_log(f"Failed to install {package}: {process.stderr}")
                            else:
                                update_log(f"{package} installed successfully.")
                        except Exception as e:
                            pip_success = False
                            update_log(f"Error installing {package}: {str(e)}")
                    
                    installation_success = pip_success
                
                # Complete installation
                if installation_success:
                    update_log("\nAll GPU packages installed successfully!")
                else:
                    update_log("\nSome packages could not be installed. Check output for details.")
                
                # Update UI back on the main thread
                self.root.after(100, lambda: self._complete_installation(progress_window, installation_success))
            
            # Start installation in a separate thread
            threading.Thread(target=run_installation, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install GPU packages: {str(e)}")
    
    def _complete_installation(self, progress_window, success):
        """Complete the GPU package installation process"""
        # Close the progress window
        progress_window.destroy()
        
        # Show completion message
        if success:
            messagebox.showinfo("Success", "GPU support packages installed successfully! GPU acceleration is now enabled.")
        else:
            messagebox.showwarning("Warning", 
                "Some GPU packages could not be installed. The application will still run without GPU acceleration.\n\n"
                "You can continue using the application with CPU-only processing.")
        
        # Check GPU support status again
        self.check_gpu_support()
    
    def toggle_data_source(self):
        """Toggle between local data folder and AWS S3 data bucket"""
        if not aws_available and self.data_source.get() == "s3":
            messagebox.showerror("Error", "AWS boto3 library not installed. Install with: pip install boto3")
            self.data_source.set("local")
            return
            
        if self.data_source.get() == "local":
            # Using local data folder
            if hasattr(self, 'bucket_name_entry'):
                self.bucket_name_entry.configure(state="disabled")
                self.prefix_entry.configure(state="disabled")
                self.access_key_entry.configure(state="disabled")
                self.secret_key_entry.configure(state="disabled")
                self.token_entry.configure(state="disabled")
                self.test_s3_button.configure(state="disabled")
            self.use_s3.set(False)
        else:  # s3
            # Using AWS S3
            if hasattr(self, 'bucket_name_entry'):
                self.bucket_name_entry.configure(state="normal")
                self.prefix_entry.configure(state="normal")
                self.access_key_entry.configure(state="normal")
                self.secret_key_entry.configure(state="normal")
                self.token_entry.configure(state="normal")
                self.test_s3_button.configure(state="normal")
            self.use_s3.set(True)
            
    def toggle_s3_settings(self):
        """Enable/disable S3 settings based on use_s3 checkbox"""
        if not aws_available:
            # Disable all S3 settings if boto3 is not available
            if hasattr(self, 's3_uri_entry'):
                self.s3_uri_entry.configure(state="disabled")
            if hasattr(self, 'test_s3_button'):
                self.test_s3_button.configure(state="disabled")
            # Keys authentication is the only method supported
            return
            
        if self.use_s3.get():
            # Enable S3 settings
            if hasattr(self, 's3_uri_entry'):
                self.s3_uri_entry.configure(state="normal")
            if hasattr(self, 'test_s3_button'):
                self.test_s3_button.configure(state="normal")
            # Keys authentication is the only method supported
            # Update authentication settings based on selected method
            self.toggle_auth_method()
            # Toggle advanced authentication if needed
            self.toggle_advanced_auth()
            
            # Set data source to S3 if available
            if hasattr(self, 'data_source'):
                self.data_source.set("s3")
                
            # Configuration will be saved when 'Save Configuration' or 'Run Analysis' is clicked
                
        else:
            # Disable S3 settings
            if hasattr(self, 's3_uri_entry'):
                self.s3_uri_entry.configure(state="disabled")
            if hasattr(self, 'test_s3_button'):
                self.test_s3_button.configure(state="disabled")
            # Disable all authentication settings
            if hasattr(self, 'access_key_entry'):
                self.access_key_entry.configure(state="disabled")
                self.secret_key_entry.configure(state="disabled")
            if hasattr(self, 'token_entry'):
                self.token_entry.configure(state="disabled")
            if hasattr(self, 'bucket_name_entry'):
                self.bucket_name_entry.configure(state="disabled")
                self.prefix_entry.configure(state="disabled")
            if hasattr(self, 'region_entry'):
                self.region_entry.configure(state="disabled")
            # Only keys authentication is supported
                
            # Set data source to local
            if hasattr(self, 'data_source'):
                self.data_source.set("local")
                
            # Configuration will be saved when 'Save Configuration' or 'Run Analysis' is clicked
                
    def toggle_advanced_auth(self):
        """Show or hide advanced authentication options"""
        if not hasattr(self, 'show_advanced_auth') or not hasattr(self, 'advanced_auth_frame'):
            return
            
        if self.show_advanced_auth.get():
            # Show advanced authentication frame using pack instead of grid
            self.advanced_auth_frame.pack(fill=tk.X, padx=5, pady=5, after=self.show_advanced_auth.master)
            self.toggle_auth_method()
        else:
            # Hide advanced authentication frame
            self.advanced_auth_frame.pack_forget()
    
    def toggle_auth_method(self, *args):
        """Enable/disable authentication settings based on selected auth method - only keys supported"""
        if not aws_available or not self.use_s3.get() or not hasattr(self, 'show_advanced_auth'):
            return
            
        # If advanced auth is not shown, return
        if not self.show_advanced_auth.get():
            return
            
        # Only keys auth method is supported now
        # Just enable the region entry
        if hasattr(self, 'region_entry'):
            self.region_entry.configure(state="normal")
            
    def validate_session_token(self, session_token):
        """Validate the format of a session token"""
        # Basic checks for AWS session token format
        # This doesn't verify the token is valid with AWS, just that it looks like a valid format
        if not session_token:
            return True  # Empty token is technically valid (means don't use a token)
            
        # Most AWS session tokens follow this pattern
        if len(session_token) < 100:
            return False  # Too short for a session token
        
        # Check for invalid characters
        valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\n")
        return all(c in valid_chars for c in session_token)
    
    def test_s3_connection(self):
        """Test the connection to the S3 bucket"""
        if not aws_available:
            messagebox.showerror("Error", "AWS boto3 library not installed. Install with: pip install boto3")
            return
        
        s3_uri = self.s3_data_uri.get()
        if not s3_uri.startswith('s3://'):
            messagebox.showerror("Error", "Invalid S3 URI format. It should start with 's3://'") 
            return
        
        try:
            # Parse the S3 URI to extract bucket name and prefix
            parts = s3_uri.replace("s3://", "").split("/")
            bucket_name = parts[0]
            prefix = "/".join(parts[1:]) if len(parts) > 1 else ""
            
            # Only keys authentication is supported
            access_key = self.s3_access_key.get()
            secret_key = self.s3_secret_key.get()
            session_token = self.s3_session_token.get()
            region = self.s3_region.get()
            s3_client = None
            
            if not access_key or not secret_key:
                messagebox.showerror("Error", "Access key and secret key cannot be empty")
                return
                
            # Validate session token if provided
            if session_token and not self.validate_session_token(session_token):
                messagebox.showerror("Error", "Session token appears to be invalid. Please check the format.")
                return
                
            if session_token:
                messagebox.showinfo("Auth Method", f"Using AWS access keys with session token in region {region}")
                try:
                    s3_client = boto3.client('s3', 
                                           aws_access_key_id=access_key, 
                                           aws_secret_access_key=secret_key, 
                                           aws_session_token=session_token,
                                           region_name=region)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create S3 client with session token: {str(e)}\n\nYour session token may be invalid or expired.")
                    return
            else:
                messagebox.showinfo("Auth Method", f"Using AWS access keys in region {region}")
                try:
                    s3_client = boto3.client('s3', 
                                           aws_access_key_id=access_key, 
                                           aws_secret_access_key=secret_key, 
                                           region_name=region)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create S3 client: {str(e)}")
                    return
            
            # Check if we got a valid S3 client
            if s3_client is None:
                messagebox.showerror("Error", "Failed to create S3 client. Check your authentication details.")
                return
                
            # Test the connection by listing objects
            try:
                response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix, MaxKeys=1)
                if prefix:
                    messagebox.showinfo("Success", f"Successfully connected to S3 bucket '{bucket_name}' with prefix '{prefix}'")
                else:
                    messagebox.showinfo("Success", f"Successfully connected to S3 bucket '{bucket_name}'")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to list objects in bucket: {str(e)}")
                return
            
        except botocore.exceptions.NoCredentialsError:
            messagebox.showerror("Error", "AWS credentials not found. Please configure your AWS credentials.")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error while testing S3 connection: {str(e)}")
            logger.error(traceback.format_exc())
    
    def update_date_values(self):
        """Update date string variables from the date picker widgets"""
        if tkcalendar_available and hasattr(self, 'start_date_picker') and hasattr(self, 'end_date_picker'):
            # Using DateEntry widgets
            self.start_date.set(self.start_date_picker.get_date().strftime('%Y-%m-%d'))
            self.end_date.set(self.end_date_picker.get_date().strftime('%Y-%m-%d'))
        elif hasattr(self, 'start_date_entry') and hasattr(self, 'end_date_entry'):
            # Using basic Entry widgets
            self.start_date.set(self.start_date_entry.get())
            self.end_date.set(self.end_date_entry.get())
                    
    def create_bottom_buttons(self):
        """Create buttons only on the Startup tab below the time range selection"""
        # We'll create these buttons directly on the Startup tab instead of at the bottom of the window
        pass
    
    def load_config(self):
        """Load configuration from config.ini if it exists"""
        try:
            # Get the script directory for the config file path
            if getattr(sys, 'frozen', False):
                script_dir = os.path.dirname(sys.executable)
            else:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                
            config_path = os.path.join(script_dir, 'config.ini')
            
            if not os.path.exists(config_path):
                return
                
            config = configparser.ConfigParser()
            config.read(config_path)
            
            # Load general settings
            if 'DEFAULT' in config:
                if 'DATA_DIRECTORY' in config['DEFAULT']:
                    self.data_directory.set(config['DEFAULT']['DATA_DIRECTORY'])
                if 'OUTPUT_DIRECTORY' in config['DEFAULT']:
                    self.output_directory.set(config['DEFAULT']['OUTPUT_DIRECTORY'])
                
                # Load date range settings
                if 'START_DATE' in config['DEFAULT'] and config['DEFAULT']['START_DATE']:
                    self.start_date.set(config['DEFAULT']['START_DATE'])
                    try:
                        if tkcalendar_available and hasattr(self, 'start_date_picker'):
                            self.start_date_picker.set_date(datetime.strptime(config['DEFAULT']['START_DATE'], '%Y-%m-%d').date())
                    except (ValueError, AttributeError):
                        pass  # If date is invalid, keep the default
                if 'END_DATE' in config['DEFAULT'] and config['DEFAULT']['END_DATE']:
                    self.end_date.set(config['DEFAULT']['END_DATE'])
                    try:
                        if tkcalendar_available and hasattr(self, 'end_date_picker'):
                            self.end_date_picker.set_date(datetime.strptime(config['DEFAULT']['END_DATE'], '%Y-%m-%d').date())
                    except (ValueError, AttributeError):
                        pass  # If date is invalid, keep the default
            
            # Load ship filters
            if 'SHIP_FILTERS' in config:
                if 'SELECTED_SHIP_TYPES' in config['SHIP_FILTERS']:
                    selected_types = config['SHIP_FILTERS']['SELECTED_SHIP_TYPES'].split(',')
                    # Reset all to false first
                    for ship_type in self.ship_types:
                        self.ship_types[ship_type]['var'].set(False)
                    # Then set selected ones to true
                    for type_str in selected_types:
                        try:
                            ship_type = int(type_str.strip())
                            if ship_type in self.ship_types:
                                self.ship_types[ship_type]['var'].set(True)
                        except (ValueError, KeyError):
                            pass
            
            # Load anomaly thresholds
            if 'ANOMALY_THRESHOLDS' in config:
                if 'MIN_TRAVEL_NM' in config['ANOMALY_THRESHOLDS']:
                    self.min_travel_nm.set(float(config['ANOMALY_THRESHOLDS']['MIN_TRAVEL_NM']))
                if 'MAX_TRAVEL_NM' in config['ANOMALY_THRESHOLDS']:
                    self.max_travel_nm.set(float(config['ANOMALY_THRESHOLDS']['MAX_TRAVEL_NM']))
                if 'COG_HEADING_MAX_DIFF' in config['ANOMALY_THRESHOLDS']:
                    self.cog_heading_max_diff.set(float(config['ANOMALY_THRESHOLDS']['COG_HEADING_MAX_DIFF']))
                if 'MIN_SPEED_FOR_COG_CHECK' in config['ANOMALY_THRESHOLDS']:
                    self.min_speed_for_cog_check.set(float(config['ANOMALY_THRESHOLDS']['MIN_SPEED_FOR_COG_CHECK']))
            
            # Load anomaly types to detect
            if 'ANOMALY_TYPES' in config:
                for anomaly_type in self.anomaly_types:
                    # Handle special case for COG-Heading renamed to Course over Ground-Heading
                    if anomaly_type == "Course over Ground-Heading Inconsistency":
                        key = "COG-Heading_Inconsistency"
                    else:
                        key = anomaly_type.replace(' ', '_').replace('(', '').replace(')', '')
                    if key in config['ANOMALY_TYPES']:
                        self.anomaly_types[anomaly_type].set(config['ANOMALY_TYPES'].getboolean(key))
                        
            # Load output controls settings
            if 'OUTPUT_CONTROLS' in config:
                for control_key in self.output_controls:
                    if control_key in config['OUTPUT_CONTROLS']:
                        self.output_controls[control_key].set(config['OUTPUT_CONTROLS'].getboolean(control_key))
                        
            # Load analysis filters
            if 'ANALYSIS_FILTERS' in config:
                # Only try to load existing filter variables
                # Skip the removed anomaly filter toggles that might still be in the config file
                for filter_key, var in self.analysis_filters.items():
                    if filter_key in config['ANALYSIS_FILTERS']:
                        # Handle different variable types appropriately
                        if isinstance(var, tk.DoubleVar):
                            try:
                                var.set(float(config['ANALYSIS_FILTERS'][filter_key]))
                            except ValueError:
                                pass  # Use default if value cannot be converted
                        elif isinstance(var, tk.IntVar):
                            try:
                                var.set(int(config['ANALYSIS_FILTERS'][filter_key]))
                            except ValueError:
                                pass  # Use default if value cannot be converted
                        else:  # StringVar or other
                            var.set(config['ANALYSIS_FILTERS'][filter_key])
            
            # Load AWS settings
            if 'AWS' in config:
                # Use getboolean for boolean values
                if 'use_s3' in config['AWS']:
                    try:
                        self.use_s3.set(config['AWS'].getboolean('use_s3'))
                    except ValueError:
                        pass
                        
                # String values
                if 's3_data_uri' in config['AWS']:
                    self.s3_data_uri.set(config['AWS']['s3_data_uri'])
                if 's3_auth_method' in config['AWS']:
                    self.s3_auth_method.set(config['AWS']['s3_auth_method'])
                if 's3_profile_name' in config['AWS']:
                    self.s3_profile_name.set(config['AWS']['s3_profile_name'])
                if 's3_access_key' in config['AWS']:
                    self.s3_access_key.set(config['AWS']['s3_access_key'])
                if 's3_secret_key' in config['AWS']:
                    self.s3_secret_key.set(config['AWS']['s3_secret_key'])
                if 's3_session_token' in config['AWS']:
                    self.s3_session_token.set(config['AWS']['s3_session_token'])
                if 's3_region' in config['AWS']:
                    self.s3_region.set(config['AWS']['s3_region'])
                if 's3_role_arn' in config['AWS']:
                    self.s3_role_arn.set(config['AWS']['s3_role_arn'])
                if 's3_bucket_name' in config['AWS']:
                    self.s3_bucket_name.set(config['AWS']['s3_bucket_name'])
                if 's3_prefix' in config['AWS']:
                    self.s3_prefix.set(config['AWS']['s3_prefix'])
                if 's3_local_dir' in config['AWS']:
                    self.s3_local_dir.set(config['AWS']['s3_local_dir'])
        
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    
    def save_config(self):
        """Save configuration to config.ini"""
        try:
            # Get the script directory for the config file path
            if getattr(sys, 'frozen', False):
                script_dir = os.path.dirname(sys.executable)
            else:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                
            config_path = os.path.join(script_dir, 'config.ini')
            
            config = configparser.ConfigParser()
            
            # Read existing config to preserve other sections
            if os.path.exists(config_path):
                config.read(config_path)
            
            if 'DEFAULT' not in config:
                config['DEFAULT'] = {}
            
            # Update with current values
            config['DEFAULT']['DATA_DIRECTORY'] = self.data_directory.get()
            config['DEFAULT']['OUTPUT_DIRECTORY'] = self.output_directory.get()
            
            # Get date values based on available widgets
            if tkcalendar_available and hasattr(self, 'start_date_picker'):
                self.start_date.set(self.start_date_picker.get_date().strftime('%Y-%m-%d'))
                self.end_date.set(self.end_date_picker.get_date().strftime('%Y-%m-%d'))
                
            config['DEFAULT']['START_DATE'] = self.start_date.get()
            config['DEFAULT']['END_DATE'] = self.end_date.get()
            
            # Ship filters - get selected ship types
            selected_types = [str(ship_type) for ship_type in self.ship_types if self.ship_types[ship_type]['var'].get()]
            if 'SHIP_FILTERS' not in config:
                config['SHIP_FILTERS'] = {}
            config['SHIP_FILTERS']['SELECTED_SHIP_TYPES'] = ','.join(selected_types)
            
            # Anomaly thresholds
            if 'ANOMALY_THRESHOLDS' not in config:
                config['ANOMALY_THRESHOLDS'] = {}
            config['ANOMALY_THRESHOLDS']['MIN_TRAVEL_NM'] = str(self.min_travel_nm.get())
            config['ANOMALY_THRESHOLDS']['MAX_TRAVEL_NM'] = str(self.max_travel_nm.get())
            config['ANOMALY_THRESHOLDS']['COG_HEADING_MAX_DIFF'] = str(self.cog_heading_max_diff.get())
            config['ANOMALY_THRESHOLDS']['MIN_SPEED_FOR_COG_CHECK'] = str(self.min_speed_for_cog_check.get())
            
            # Anomaly types to detect
            if 'ANOMALY_TYPES' not in config:
                config['ANOMALY_TYPES'] = {}
            for anomaly_type, var in self.anomaly_types.items():
                # Handle special case for Course over Ground-Heading renamed from COG-Heading
                if anomaly_type == "Course over Ground-Heading Inconsistency":
                    key = "COG-Heading_Inconsistency"
                else:
                    key = anomaly_type.replace(' ', '_').replace('(', '').replace(')', '')
                config['ANOMALY_TYPES'][key] = str(var.get())
            
            # Output Controls settings
            if 'OUTPUT_CONTROLS' not in config:
                config['OUTPUT_CONTROLS'] = {}
            for control_key, var in self.output_controls.items():
                config['OUTPUT_CONTROLS'][control_key] = str(var.get())
                
            # Analysis Filters settings
            if 'ANALYSIS_FILTERS' not in config:
                config['ANALYSIS_FILTERS'] = {}
            
            # Save only the existing analysis filter variables
            # The filter toggles have been removed
            for filter_key, var in self.analysis_filters.items():
                # Only save to config if the variable still exists
                config['ANALYSIS_FILTERS'][filter_key] = str(var.get())
                
            # Processing Options
            if 'Processing' not in config:
                config['Processing'] = {}
                
            # Save processing options
            config['Processing']['USE_GPU'] = str(self.use_gpu.get())
            config['Processing']['USE_DASK'] = str(self.use_dask.get())
                
            # AWS S3 settings
            if 'AWS' not in config:
                config['AWS'] = {}
            
            # Save AWS credentials and settings
            config['AWS']['use_s3'] = str(self.use_s3.get())
            config['AWS']['s3_data_uri'] = self.s3_data_uri.get()
            # Keys authentication is the only supported method
            config['AWS']['s3_auth_method'] = "keys"
            config['AWS']['s3_access_key'] = self.s3_access_key.get()
            config['AWS']['s3_secret_key'] = self.s3_secret_key.get()
            
            # Handle session token - very long tokens may cause issues with the config file
            session_token = self.s3_session_token.get()
            if len(session_token) > 1000:
                logger.warning(f"Session token is very long ({len(session_token)} chars). Storing in config file.")
                # We'll store it but warn the user that it may be better to use AWS credentials file
            config['AWS']['s3_session_token'] = session_token
            config['AWS']['s3_region'] = self.s3_region.get()
            config['AWS']['s3_bucket_name'] = self.s3_bucket_name.get()
            config['AWS']['s3_prefix'] = self.s3_prefix.get()
            config['AWS']['s3_local_dir'] = self.s3_local_dir.get()

            # Write to file
            with open(config_path, 'w') as configfile:
                config.write(configfile)
                
            messagebox.showinfo("Configuration Saved", f"Configuration has been saved to {config_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
    
    def run_analysis(self):
        """Run the shipping fraud detection analysis using SFD.py"""
        # Add debug message box to show we're starting the run process
        messagebox.showinfo("Debug", "Starting SFD Analysis process...")
        
        # Validate data and output directories based on selected data source
        if self.data_source.get() == "local" and not self.data_directory.get():
            messagebox.showerror("Error", "Please specify a data directory in the Advanced tab")
            return
            
        if not self.output_directory.get():
            messagebox.showerror("Error", "Please specify an output directory in the Advanced tab")
            return
            
        # Validate S3 settings if using S3
        if self.data_source.get() == "s3":
            if not self.s3_bucket_name.get():
                messagebox.showerror("Error", "Please specify an S3 bucket name")
                return
                
            # Check for required access keys
            if not (self.s3_access_key.get() and self.s3_secret_key.get()):
                messagebox.showerror("Error", "Both AWS Access Key and Secret Key are required")
                return
        
        # Get the script directory for the config file path
        if getattr(sys, 'frozen', False):
            script_dir = os.path.dirname(sys.executable)
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
        # Get absolute paths with debug output
        # Look for both possible script filenames (SFD.py and SDF.py)
        script_path = None
        for script_name in ["SFD.py", "SDF.py"]:
            potential_path = os.path.abspath(os.path.join(script_dir, script_name))
            if os.path.exists(potential_path):
                script_path = potential_path
                logger.info(f"Found script file: {script_name}")
                break
                
        if script_path is None:
            # If no script found, default to SFD.py and let the error handling deal with it
            script_path = os.path.abspath(os.path.join(script_dir, "SFD.py"))
            
        config_path = os.path.abspath(os.path.join(script_dir, "config.ini"))
        
        # Log the paths for debugging
        script_filename = os.path.basename(script_path)
        logger.info(f"Script path: {script_path}")
        logger.info(f"Config path: {config_path}")
        
        if not os.path.exists(script_path):
            messagebox.showerror("Error", f"{script_filename} not found.")
            return
        
        # Get date values based on available widgets
        if tkcalendar_available and hasattr(self, 'start_date_picker'):
            start_date_str = self.start_date_picker.get_date().strftime('%Y-%m-%d')
            end_date_str = self.end_date_picker.get_date().strftime('%Y-%m-%d')
            # Update internal variables to match calendar widget values
            self.start_date.set(start_date_str)
            self.end_date.set(end_date_str)
        else:
            start_date_str = self.start_date.get()
            end_date_str = self.end_date.get()
            
        # Save all configuration settings to config.ini first
        self.save_config()
        
        # Build command to run SDF.py with NO command-line arguments
        cmd = [sys.executable, script_path]
        
        # Debug: Show the command that will be run
        debug_msg = f"Command: {' '.join(cmd)}\nWorking directory: {script_dir}"
        logger.info(debug_msg)
        messagebox.showinfo("Debug: Command", debug_msg)
            
        # Note: All other settings will be read from the config.ini file by SDF.py
        
        # Show message
        if tkcalendar_available and hasattr(self, 'start_date_picker'):
            start_date = self.start_date_picker.get_date().strftime('%Y-%m-%d')
            end_date = self.end_date_picker.get_date().strftime('%Y-%m-%d')
            message = f"Starting analysis for date range {start_date} to {end_date}.\n"
        else:
            message = f"Starting analysis for date range {self.start_date.get()} to {self.end_date.get()}.\n"
            
        messagebox.showinfo("Analysis Started", 
                          message + "This may take some time depending on the amount of data.")
        
        # Create and show progress window
        progress_window = ProgressWindow(self.root)
        progress_window.add_message("Starting analysis...")
        progress_window.add_message(f"Command: {' '.join(cmd)}")
        
        # Function to read output from process and update the window
        def read_output(process):
            # Show initial status
            progress_window.add_message(f"{script_filename} process started. Capturing output...")
            progress_window.add_message("You can monitor the progress in this window.")
            progress_window.add_message("-------------------------------------------")
            
            # For the dummy process, we just wait for it to finish
            if platform.system() == "Windows" and cmd[0] == sys.executable and os.path.basename(cmd[1]) == os.path.basename(script_path):
                # We're handling output with the monitoring thread now
                # Just wait for the dummy process to end
                process.wait()
                return
                
            # Normal process monitoring for non-Windows platforms
            try:
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if not line:
                        continue
                    if progress_window.canceled:
                        break
                    try:
                        # With text=True, we get strings directly
                        line_str = line.strip()
                        if line_str:
                            progress_window.add_message(line_str)
                    except Exception as e:
                        progress_window.add_message(f"Error reading output: {str(e)}")
                
                # Process has finished
                if not progress_window.canceled:
                    try:
                        return_code = process.poll()
                        if return_code is None:
                            return_code = process.wait(timeout=5)
                    except Exception:
                        return_code = process.poll() or -1
                        
                    if return_code == 0:
                        progress_window.add_message("Analysis completed successfully!")
                        progress_window.add_message(f"Results saved to {self.output_directory.get()}")
                        
                        # Show completion message and update the progress window
                        def show_completion():
                            if not progress_window.canceled:
                                # No need to show another message box, since SDF.py shows one
                                # with an option to continue or exit
                                
                                # Update the progress window with completion options
                                progress_window.analysis_complete(self.output_directory.get())
                                
                                # Remove focus from progress window - letting the SDF.py dialog
                                # be visible to the user
                                progress_window.withdraw()
                        
                        # Schedule the completion message to be shown after a delay
                        progress_window.after(500, show_completion)
                    elif return_code == 100:
                        # Special exit code 100 means user chose not to continue
                        # Close the entire application
                        progress_window.add_message("User chose not to continue. Closing application...")
                        # Create message box to make sure the user understands the application is closing
                        messagebox.showinfo("Closing Application", "The analysis is complete and you've chosen not to continue.\n\nThe application will now close.")
                        # Force destroy both windows to ensure complete exit
                        progress_window.destroy()
                        self.root.destroy()
                        # Additional exit call to guarantee termination
                        sys.exit(0)
                    else:
                        progress_window.add_message(f"Analysis failed with return code {return_code}")
                        
                        # If there's an error, show the error output
                        try:
                            error_lines = process.stderr.readlines()
                            for error_line in error_lines:
                                try:
                                    # With text=True, we get strings directly
                                    line_str = error_line.strip()
                                    if line_str:
                                        progress_window.add_message(f"ERROR: {line_str}")
                                except Exception:
                                    pass
                        except Exception as e:
                            progress_window.add_message(f"Error reading stderr: {str(e)}")
                        
                        # Show error message
                        def show_error():
                            if not progress_window.canceled:
                                messagebox.showerror("Error", f"Analysis failed. Check the log for details.")
                        
                        # Schedule the error message to be shown after a delay
                        progress_window.after(2000, show_error)
            except Exception as e:
                progress_window.add_message(f"Error in read_output: {str(e)}")
        
        try:
            # Check if the script file actually exists
            if not os.path.exists(script_path):
                error_msg = f"Error: {script_filename} not found at {script_path}"
                logger.error(error_msg)
                messagebox.showerror("Error", error_msg)
                return
                
            # Check permissions
            try:
                with open(script_path, 'r') as f:
                    pass  # Just testing if we can read the file
            except Exception as e:
                error_msg = f"Cannot read {script_filename}: {str(e)}"
                logger.error(error_msg)
                messagebox.showerror("Error", error_msg)
                return
            
            # Start the process
            if platform.system() == "Windows":
                try:
                    # Create a unique output log file for the process
                    import tempfile
                    log_file = os.path.join(tempfile.gettempdir(), f"sfd_output_{int(time.time())}.log")
                    logger.info(f"Will capture output to: {log_file}")
                    
                    # Extract parameters (everything after script path)
                    parameters = []
                    if len(cmd) > 2:
                        parameters = cmd[2:]
                    param_str = ' '.join(f'"{p}"' for p in parameters) if parameters else ''
                    
                    # Create a batch file that will run in a command window
                    batch_path = os.path.join(script_dir, BATCH_FILE_NAME)
                    with open(batch_path, "w") as batch_file:
                        # Write batch file header
                        batch_file.write(f"@echo off\n")
                        batch_file.write(f"cd \"{script_dir}\"\n")
                        batch_file.write(f"echo Starting {script_filename} at %time%\n")
                        batch_file.write(f"echo.\n")
                        
                        # Build the command to execute Python with the script file
                        # Use the script filename directly since we've already changed to the script directory
                        script_basename = os.path.basename(cmd[1])
                        full_cmd = f"\"{cmd[0]}\" \"{script_basename}\""
                        
                        # Add all additional parameters (skipping Python executable and script path)
                        if len(cmd) > 2:
                            for param in cmd[2:]:
                                if param.startswith("--"):  # This is a flag/option
                                    full_cmd += f" {param}"
                                else:  # This is a value, so it needs quotes
                                    full_cmd += f" \"{param}\""
                        
                        # Write the full command to the batch file to execute directly (no redirection)
                        batch_file.write(f"{full_cmd}\n")
                        batch_file.write(f"echo.\n")
                        batch_file.write(f"echo Process completed at %time%\n")
                        batch_file.write(f"echo Press any key to continue...\n")
                        batch_file.write(f"pause > nul\n")
                        
                        # Log the full command being executed
                        logger.info(f"Full command in batch file: {full_cmd}")
                    
                    logger.info(f"Created batch file: {batch_path}")
                    
                    # Just display a message about the command window
                    progress_window.add_message(f"{script_filename} will now run in a command window.")
                    progress_window.add_message("Please monitor the command window for progress updates.")
                    progress_window.add_message(f"After {script_filename} completes, press any key to close the command window.")
                    progress_window.add_message("\n--- Command Window Launched ---")
                    
                    # Set output directory for results access
                    output_dir = ""
                    if hasattr(self, 'output_directory') and hasattr(self.output_directory, 'get'):
                        output_dir = self.output_directory.get()
                    
                    # Mark analysis as complete in the progress window
                    progress_window.analysis_complete(output_dir)
                    
                    # Start the batch file in a visible command window
                    os.startfile(batch_path)
                    logger.info(f"Started {script_filename} in command window using batch file")
                    
                    messagebox.showinfo("Process Started", f"{script_filename} has been started in a command window.\
Please monitor the command window for progress information.")
                    
                except Exception as e:
                    error_msg = f"Failed to start {script_filename} process: {str(e)}"
                    logger.error(error_msg)
                    messagebox.showerror("Process Error", error_msg)
                    return
            else:
                try:
                    logger.info(f"Attempting to start process with cmd: {cmd}")
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=False,  # Keep as bytes for consistent handling
                        cwd=script_dir,  # Ensure correct working directory
                        creationflags=subprocess.CREATE_NEW_CONSOLE if platform.system() == "Windows" else 0  # Create a new console on Windows
                    )
                    logger.info(f"Process started with PID: {process.pid}")
                    messagebox.showinfo("Process Started", f"{script_filename} started with PID: {process.pid}")
                    
                    # Set the process on the progress window
                    progress_window.set_process(process)
                    
                    # Start a thread to read the output
                    threading.Thread(target=read_output, args=(process,), daemon=True).start()
                except Exception as e:
                    error_msg = f"Failed to start {script_filename} process: {str(e)}"
                    logger.error(error_msg)
                    messagebox.showerror("Process Error", error_msg)
                    return
                
        except Exception as e:
            error_msg = f"Failed to run analysis: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            messagebox.showerror("Error", error_msg)
            
            # Try an alternative method as a fallback
            if messagebox.askyesno("Attempt Alternative Launch", "Would you like to try an alternative method to launch SFD.py?"):
                try:
                    logger.info("Attempting alternative launch method")
                    # Construct a command string for direct execution with NO command line arguments
                    # We use a variable since this command is shown to the user in the dialog
                    alt_cmd = f"cd \"{script_dir}\" && \"{sys.executable}\" \"{script_path}\""
                    
                    # Log the alternative command
                    logger.info(f"Alternative command: {alt_cmd}")
                    messagebox.showinfo("Alternative Method", f"Trying to launch with command:\n{alt_cmd}")
                    
                    # Create a batch file to execute the command - use a different name than main batch file
                    temp_batch_name = f"run_sfd_alt_{int(time.time())}.bat"
                    batch_path = os.path.join(script_dir, temp_batch_name)
                    with open(batch_path, "w") as batch_file:
                        batch_file.write(f"@echo off\n")
                        batch_file.write(f"echo Running {script_filename}...\n")
                        batch_file.write(f"{alt_cmd}\n")
                        batch_file.write(f"pause\n")
                    
                    # Execute the batch file
                    os.startfile(batch_path)
                    messagebox.showinfo("Batch File Created", f"A batch file has been created at {batch_path}. Please check if {script_filename} is running.")
                    
                except Exception as alt_e:
                    logger.error(f"Alternative launch method failed: {str(alt_e)}")
                    messagebox.showerror("Error", f"Alternative launch method failed: {str(alt_e)}")
                    messagebox.showinfo("Manual Instructions", f"To run {script_filename} manually:\n1. Open a command prompt\n2. Navigate to: {script_dir}\n3. Run: {sys.executable} {script_path}")
                    return

def main():
    root = tk.Tk()
    app = SDFGUI(root)
    return root

if __name__ == "__main__":
    # Set up basic root window first for messagebox to work
    root = tk.Tk()
    root.withdraw()  # Hide window initially
    
    # Check dependencies first
    if check_dependencies():
        # Destroy initial hidden window
        root.destroy()
        # Start the application normally
        root = main()
        root.mainloop()
    else:
        # If dependencies are missing and user didn't install them, exit
        messagebox.showerror(
            "Dependencies Missing",
            "Cannot start application due to missing dependencies."
        )
        root.destroy()
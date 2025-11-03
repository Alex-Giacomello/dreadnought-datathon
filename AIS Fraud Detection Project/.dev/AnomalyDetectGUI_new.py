#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIS Shipping Fraud Detection System GUI

This module provides a graphical user interface for the AIS Shipping Fraud Detection System.
It allows users to configure settings, select which anomaly types to detect, and run the analysis.
"""

import os
import configparser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime, timedelta
import sys
import subprocess
import platform
import time
import re
import glob
import traceback
import logging

# Import AWS boto3 for S3 integration
try:
    import boto3
    import botocore.exceptions
    from urllib.parse import urlparse
    aws_available = True
except ImportError:
    aws_available = False

# Import Windows constants if on Windows
if platform.system() == "Windows":
    import win32con

# For markdown rendering
try:
    import markdown
    from tkhtmlview import HTMLScrolledText, HTMLText
    markdown_available = True
except ImportError:
    markdown_available = False

# Try to import tkcalendar, display an error if it's not available
try:
    from tkcalendar import DateEntry
    tkcalendar_available = True
except ImportError:
    tkcalendar_available = False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ais_fraud_detection_gui.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AnomalyDetectGUI")

# Import pandas conditionally to avoid startup delay
pandas_imported = False
def import_pandas():
    global pandas_imported, pd
    if not pandas_imported:
        try:
            import pandas as pd
            pandas_imported = True
            return True
        except ImportError:
            logger.error("Failed to import pandas")
            return False
    return True

class AnomalyDetectionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AIS Shipping Fraud Detection System")
        self.root.geometry("800x600")
        
        # Check for required files before proceeding
        self.check_required_files()
        
        # Initialize variables
        self.anomaly_types = {
            "AIS Beacon Off": tk.BooleanVar(value=True),
            "AIS Beacon On": tk.BooleanVar(value=True),
            "Excessive Travel Distance (Fast)": tk.BooleanVar(value=True),
            "Excessive Travel Distance (Slow)": tk.BooleanVar(value=True),
            "Course over Ground-Heading Inconsistency": tk.BooleanVar(value=True)
        }
        
        self.data_directory = tk.StringVar()
        self.output_directory = tk.StringVar()
        # Ship type variables - using dict with ship type number as key and BooleanVar as value
        self.ship_types = {
            70: {'name': 'Cargo, General', 'var': tk.BooleanVar(value=True)},
            71: {'name': 'Cargo, Hazardous category A', 'var': tk.BooleanVar(value=True)},
            72: {'name': 'Cargo, Hazardous category B', 'var': tk.BooleanVar(value=True)},
            73: {'name': 'Cargo, Hazardous category C', 'var': tk.BooleanVar(value=True)},
            74: {'name': 'Cargo, Hazardous category D', 'var': tk.BooleanVar(value=True)},
            75: {'name': 'Cargo, Reserved for future use', 'var': tk.BooleanVar(value=True)},
            76: {'name': 'Cargo, Reserved for future use', 'var': tk.BooleanVar(value=True)},
            77: {'name': 'Cargo, Reserved for future use', 'var': tk.BooleanVar(value=True)},
            78: {'name': 'Cargo, Reserved for future use', 'var': tk.BooleanVar(value=True)},
            79: {'name': 'Cargo, No additional information', 'var': tk.BooleanVar(value=True)},
            80: {'name': 'Tanker, General', 'var': tk.BooleanVar(value=True)},
            81: {'name': 'Tanker, Hazardous category A', 'var': tk.BooleanVar(value=True)},
            82: {'name': 'Tanker, Hazardous category B', 'var': tk.BooleanVar(value=True)},
            83: {'name': 'Tanker, Hazardous category C', 'var': tk.BooleanVar(value=True)},
            84: {'name': 'Tanker, Hazardous category D', 'var': tk.BooleanVar(value=True)},
            85: {'name': 'Tanker, Reserved for future use', 'var': tk.BooleanVar(value=True)},
            86: {'name': 'Tanker, Reserved for future use', 'var': tk.BooleanVar(value=True)},
            87: {'name': 'Tanker, Reserved for future use', 'var': tk.BooleanVar(value=True)},
            88: {'name': 'Tanker, Reserved for future use', 'var': tk.BooleanVar(value=True)},
            89: {'name': 'Tanker, No additional information', 'var': tk.BooleanVar(value=True)}
        }
        self.min_travel_nm = tk.DoubleVar(value=200)
        self.max_travel_nm = tk.DoubleVar(value=550)
        self.cog_heading_max_diff = tk.DoubleVar(value=45)
        self.min_speed_for_cog_check = tk.DoubleVar(value=10)
        
        # Date range variables (replacing num_days)
        self.use_date_range = tk.BooleanVar(value=True)  # Use date range by default
        self.num_days = tk.IntVar(value=5)  # Still keep this for backward compatibility
        # Set specific default dates for the AIS test data
        self.start_date = tk.StringVar(value="2024-10-01")  # Default to Oct 1, 2024
        self.end_date = tk.StringVar(value="2024-10-05")  # Default to Oct 5, 2024
        
        self.use_dask = tk.BooleanVar(value=True)
        
        # S3 variables
        self.use_s3 = tk.BooleanVar(value=False)
        self.s3_data_uri = tk.StringVar(value="s3://ai-dsde-txg-datathon2025/teams/dreadnought/parquet/")
        
        # Authentication method variables
        self.s3_auth_method = tk.StringVar(value="default") # values: default, profile, keys, role
        self.s3_profile_name = tk.StringVar(value="dreadnought")
        self.s3_access_key = tk.StringVar()
        self.s3_secret_key = tk.StringVar()
        self.s3_region = tk.StringVar(value="us-east-1")
        self.s3_role_arn = tk.StringVar()
        
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_date_selection_tab()
        self.create_ship_types_tab()
        self.create_anomaly_types_tab()
        self.create_advanced_tab()
        self.create_readme_tab()
        
        # Create bottom buttons
        self.create_bottom_buttons()
        
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
NOTE: In this test implementation only data from 1 OCT 2024 to 31 MAR 2025 is available for use.

Select the time period on this tab and press the Run Analysis button to execute your inquery.  You can select the specific types of ships and anomalies you want to search for in those tabs.  The Data and Results folders can be set on the Advanced Tab."""
        
        desc_label = ttk.Label(desc_frame, text=desc_text, wraplength=750, justify="left")
        desc_label.pack(fill=tk.X, padx=10, pady=10)
        
        # Time Range Selection Frame
        time_frame = ttk.LabelFrame(date_selection_frame, text="Time Range Selection")
        time_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=10)
        
        # Radio buttons for selection method
        ttk.Radiobutton(time_frame, text="Use days back from today", variable=self.use_date_range, 
                       value=False, command=self.toggle_date_selection).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Number of days to analyze - only enabled when use_date_range is False
        ttk.Label(time_frame, text="Number of days:").grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.days_spinbox = ttk.Spinbox(time_frame, from_=1, to=365, textvariable=self.num_days, width=5)
        self.days_spinbox.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Date range selection - only enabled when use_date_range is True
        date_range_radio = ttk.Radiobutton(time_frame, text="Use specific date range", variable=self.use_date_range, 
                       value=True, command=self.toggle_date_selection)
        date_range_radio.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
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
            
            # Set default dates to Oct 1-5, 2024
            self.start_date_picker.set_date(datetime(2024, 10, 1).date())
            self.end_date_picker.set_date(datetime(2024, 10, 5).date())
        else:
            # If tkcalendar is not available, use basic entry fields with validation
            self.date_warning = ttk.Label(date_range_frame, 
                                        text="Warning: tkcalendar not installed. Using basic date fields.",
                                        foreground='red')
            self.date_warning.pack(side=tk.TOP, pady=2)
            
            date_fields_frame = ttk.Frame(date_range_frame)
            date_fields_frame.pack(side=tk.TOP)
            
            ttk.Label(date_fields_frame, text="Start Date (YYYY-MM-DD):").pack(side=tk.LEFT, padx=2)
            self.start_date_entry = ttk.Entry(date_fields_frame, width=12)
            self.start_date_entry.pack(side=tk.LEFT, padx=2)
            
            ttk.Label(date_fields_frame, text="End Date (YYYY-MM-DD):").pack(side=tk.LEFT, padx=2)
            self.end_date_entry = ttk.Entry(date_fields_frame, width=12)
            self.end_date_entry.pack(side=tk.LEFT, padx=2)
            
            # Set default dates to Oct 1-5, 2024
            self.start_date_entry.insert(0, "2024-10-01")
            self.end_date_entry.insert(0, "2024-10-05")
            
            # Disable date range option if tkcalendar not available
            if not tkcalendar_available:
                # Show a message recommending to install tkcalendar
                ttk.Label(time_frame, text="For better date selection, install tkcalendar: pip install tkcalendar",
                         foreground='blue').grid(row=2, column=0, columnspan=3, sticky=tk.W, padx=5, pady=2)
        
        # Initialize the state of date inputs based on self.use_date_range
        self.toggle_date_selection()

    # General tab has been removed

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
        ttk.Label(scrollable_frame, text="Select ship types to include in analysis:", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=10, columnspan=2)
        
        # Create a frame for Cargo ships
        cargo_frame = ttk.LabelFrame(scrollable_frame, text="Cargo Ships")
        cargo_frame.grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        
        # Create a frame for Tanker ships
        tanker_frame = ttk.LabelFrame(scrollable_frame, text="Tanker Ships")
        tanker_frame.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Add checkboxes for each cargo ship type (70-79)
        cargo_row = 0
        for ship_type in range(70, 80):
            ttk.Checkbutton(
                cargo_frame, 
                text=f"{ship_type}: {self.ship_types[ship_type]['name']}",
                variable=self.ship_types[ship_type]['var']
            ).grid(row=cargo_row, column=0, sticky=tk.W, padx=5, pady=3)
            cargo_row += 1
        
        # Add checkboxes for each tanker ship type (80-89)
        tanker_row = 0
        for ship_type in range(80, 90):
            ttk.Checkbutton(
                tanker_frame, 
                text=f"{ship_type}: {self.ship_types[ship_type]['name']}",
                variable=self.ship_types[ship_type]['var']
            ).grid(row=tanker_row, column=0, sticky=tk.W, padx=5, pady=3)
            tanker_row += 1
        
        # Add select all/none buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Select All Cargo", command=self.select_all_cargo).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Deselect All Cargo", command=self.deselect_all_cargo).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Select All Tanker", command=self.select_all_tanker).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Deselect All Tanker", command=self.deselect_all_tanker).pack(side=tk.LEFT, padx=5)
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

    # Thresholds tab removed - content moved to Anomaly Types tab
    
    def create_readme_tab(self):
        """Create a README tab that shows the content of 1. README.md"""
        readme_frame = ttk.Frame(self.notebook)
        self.notebook.add(readme_frame, text="README")
        
        # Create a button frame at the top
        button_frame = ttk.Frame(readme_frame)
        button_frame.pack(fill=tk.X, side=tk.TOP, padx=10, pady=5)
        
        # Add a "View in Browser" button
        ttk.Button(button_frame, text="View README in Browser", command=self.open_readme_in_browser).pack(side=tk.RIGHT)
        
        if markdown_available:
            # Create an HTML viewer for rendered markdown
            self.readme_viewer = HTMLScrolledText(readme_frame, padx=10, pady=10)
            self.readme_viewer.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            # Set background color to match the application
            self.readme_viewer.set_html_content("<body style='background-color: #f0f0f0;'></body>")
        else:
            # Fallback to plain text if markdown rendering is not available
            self.readme_viewer = scrolledtext.ScrolledText(readme_frame, wrap=tk.WORD, font=("Consolas", 10), padx=10, pady=10)
            self.readme_viewer.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            self.readme_viewer.config(state=tk.DISABLED)  # Make it read-only
        
        # Load the README content
        self.load_readme_content()
        
        # Bind tab selection to refresh the README content
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def load_readme_content(self):
        """Load and render the content of 1. README.md"""
        try:
            # Get the path to the README file
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                script_dir = os.path.dirname(sys.executable)
            else:
                # Running as a script
                script_dir = os.path.dirname(os.path.abspath(__file__))
                
            readme_path = os.path.join(script_dir, "1. README.md")
            
            if os.path.exists(readme_path):
                with open(readme_path, 'r') as file:
                    readme_content = file.read()
                
                if markdown_available:
                    # Convert markdown to HTML
                    html_content = markdown.markdown(
                        readme_content,
                        extensions=['tables', 'fenced_code', 'nl2br', 'codehilite']
                    )
                    
                    # Add styling to make it look nice
                    styled_html = f"""
                    <html>
                    <head>
                        <style>
                            body {{ font-family: Arial, sans-serif; padding: 20px; }}
                            h1, h2, h3, h4, h5, h6 {{ color: #00008B; }}
                            h1 {{ border-bottom: 2px solid #00008B; padding-bottom: 5px; }}
                            h2 {{ border-bottom: 1px solid #CCCCCC; padding-bottom: 2px; }}
                            code {{ background-color: #f8f8f8; padding: 2px 4px; border-radius: 4px; }}
                            pre {{ background-color: #f8f8f8; padding: 10px; border-radius: 4px; overflow-x: auto; }}
                            a {{ color: #0066CC; text-decoration: none; }}
                            a:hover {{ text-decoration: underline; }}
                            blockquote {{ border-left: 4px solid #CCCCCC; padding-left: 10px; color: #555555; }}
                            table {{ border-collapse: collapse; width: 100%; }}
                            th, td {{ border: 1px solid #ddd; padding: 8px; }}
                            tr:nth-child(even) {{ background-color: #f2f2f2; }}
                        </style>
                    </head>
                    <body>
                        {html_content}
                    </body>
                    </html>
                    """
                    
                    # Display the HTML
                    self.readme_viewer.set_html_content(styled_html)
                else:
                    # Plain text fallback with basic formatting
                    self.readme_viewer.config(state=tk.NORMAL)
                    self.readme_viewer.delete(1.0, tk.END)
                    
                    # Format the content for better readability in plain text
                    lines = readme_content.split('\n')
                    for line in lines:
                        # Format headings
                        if line.startswith('# '):
                            self.readme_viewer.insert(tk.END, line[2:].upper() + '\n\n', 'heading1')
                        elif line.startswith('## '):
                            self.readme_viewer.insert(tk.END, line[3:].upper() + '\n\n', 'heading2')
                        elif line.startswith('### '):
                            self.readme_viewer.insert(tk.END, line[4:] + '\n\n', 'heading3')
                        # Code blocks
                        elif line.startswith('```'):
                            self.readme_viewer.insert(tk.END, '---CODE---\n', 'code')
                        # Regular text
                        else:
                            self.readme_viewer.insert(tk.END, line + '\n')
                    
                    # Configure text tags for styling
                    self.readme_viewer.tag_configure('heading1', font=('Consolas', 14, 'bold'))
                    self.readme_viewer.tag_configure('heading2', font=('Consolas', 12, 'bold'))
                    self.readme_viewer.tag_configure('heading3', font=('Consolas', 11, 'bold'))
                    self.readme_viewer.tag_configure('code', font=('Consolas', 9), background='#f0f0f0')
                    
                    self.readme_viewer.config(state=tk.DISABLED)
            else:
                # Handle missing file
                if markdown_available:
                    self.readme_viewer.set_html_content(f"<p>README file not found: {readme_path}</p>")
                else:
                    self.readme_viewer.config(state=tk.NORMAL)
                    self.readme_viewer.delete(1.0, tk.END)
                    self.readme_viewer.insert(tk.END, "README file not found: " + readme_path)
                    self.readme_viewer.config(state=tk.DISABLED)
        except Exception as e:
            # Handle errors
            error_message = f"Error loading README: {str(e)}"
            if markdown_available:
                self.readme_viewer.set_html_content(f"<p>{error_message}</p>")
            else:
                self.readme_viewer.config(state=tk.NORMAL)
                self.readme_viewer.delete(1.0, tk.END)
                self.readme_viewer.insert(tk.END, error_message)
                self.readme_viewer.config(state=tk.DISABLED)
    
    def on_tab_changed(self, event):
        """Called when a tab is selected"""
        current_tab = self.notebook.index(self.notebook.select())
        
        # Check if the README tab is selected
        if self.notebook.tab(current_tab, "text") == "README":
            # Reload the README content to ensure it's up to date
            self.load_readme_content()
            
    def open_readme_in_browser(self):
        """Open the README.md file in the default web browser"""
        try:
            if getattr(sys, 'frozen', False):
                script_dir = os.path.dirname(sys.executable)
            else:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                
            readme_path = os.path.join(script_dir, "1. README.md")
            
            if os.path.exists(readme_path):
                # Generate a temporary HTML file
                import tempfile
                temp_dir = tempfile.gettempdir()
                temp_html = os.path.join(temp_dir, "readme_preview.html")
                
                with open(readme_path, 'r') as md_file:
                    content = md_file.read()
                    
                # Create a simple HTML wrapper
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>README - AIS Shipping Fraud Detection</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                        pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                        code {{ background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
                        h1, h2, h3, h4 {{ color: #333; }}
                        a {{ color: #0066cc; }}
                    </style>
                </head>
                <body>
                    <pre>{content}</pre>
                </body>
                </html>
                """
                
                with open(temp_html, 'w') as html_file:
                    html_file.write(html_content)
                    
                # Open the HTML file in the default browser
                import webbrowser
                webbrowser.open('file://' + os.path.realpath(temp_html))
            else:
                messagebox.showinfo("File Not Found", f"README file not found: {readme_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open README in browser: {str(e)}")


    def create_advanced_tab(self):
        """Create the Advanced tab with additional settings"""
        advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(advanced_frame, text="Advanced")
        
        # Create sections with LabelFrame
        file_frame = ttk.LabelFrame(advanced_frame, text="File Locations")
        file_frame.grid(row=0, column=0, columnspan=3, sticky=tk.W+tk.E, padx=10, pady=5)
        
        # Data Directory
        ttk.Label(file_frame, text="Data Directory:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(file_frame, textvariable=self.data_directory, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="Browse...", command=self.browse_data_directory).grid(row=0, column=2, padx=5, pady=5)
        
        # Output Directory
        ttk.Label(file_frame, text="Output Directory:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(file_frame, textvariable=self.output_directory, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="Browse...", command=self.browse_output_directory).grid(row=1, column=2, padx=5, pady=5)
        
        # S3 Settings
        s3_frame = ttk.LabelFrame(advanced_frame, text="Amazon S3 Settings")
        s3_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W+tk.E, padx=10, pady=5)
        
        # Check if boto3 is available
        if not aws_available:
            ttk.Label(s3_frame, text="AWS boto3 library not installed. Install with: pip install boto3", foreground="red").grid(
                row=0, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
            s3_frame_row = 1
        else:
            s3_frame_row = 0
        
        # Use S3 checkbox
        ttk.Checkbutton(s3_frame, text="Use AWS S3 for data storage", variable=self.use_s3, 
                       command=self.toggle_s3_settings, state="normal" if aws_available else "disabled").grid(
            row=s3_frame_row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # S3 URI
        ttk.Label(s3_frame, text="S3 URI:").grid(row=s3_frame_row+1, column=0, sticky=tk.W, padx=5, pady=5)
        self.s3_uri_entry = ttk.Entry(s3_frame, textvariable=self.s3_data_uri, width=60)
        self.s3_uri_entry.grid(row=s3_frame_row+1, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Authentication Method Frame
        self.auth_method_frame = ttk.LabelFrame(s3_frame, text="Authentication Method")
        self.auth_method_frame.grid(row=s3_frame_row+2, column=0, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Authentication method selection
        ttk.Label(self.auth_method_frame, text="Auth Method:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.auth_method_combo = ttk.Combobox(self.auth_method_frame, textvariable=self.s3_auth_method, width=20, state="readonly")
        self.auth_method_combo['values'] = ("default", "profile", "keys", "role")
        self.auth_method_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.auth_method_combo.bind("<<ComboboxSelected>>", self.toggle_auth_method)
        
        # Default method description
        ttk.Label(self.auth_method_frame, text="(Uses AWS credentials from environment variables, EC2 IAM role, etc.)").grid(
            row=0, column=2, padx=5, pady=5, sticky=tk.W)
        
        # Profile settings
        ttk.Label(self.auth_method_frame, text="Profile Name:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.profile_entry = ttk.Entry(self.auth_method_frame, textvariable=self.s3_profile_name, width=20)
        self.profile_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Access key settings
        ttk.Label(self.auth_method_frame, text="Access Key:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.access_key_entry = ttk.Entry(self.auth_method_frame, textvariable=self.s3_access_key, width=40)
        self.access_key_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        # Secret key settings
        ttk.Label(self.auth_method_frame, text="Secret Key:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.secret_key_entry = ttk.Entry(self.auth_method_frame, textvariable=self.s3_secret_key, width=40, show="*")
        self.secret_key_entry.grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        # Region settings
        ttk.Label(self.auth_method_frame, text="AWS Region:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.region_entry = ttk.Entry(self.auth_method_frame, textvariable=self.s3_region, width=20)
        self.region_entry.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Role ARN settings
        ttk.Label(self.auth_method_frame, text="Role ARN:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.role_arn_entry = ttk.Entry(self.auth_method_frame, textvariable=self.s3_role_arn, width=60)
        self.role_arn_entry.grid(row=5, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        # Test S3 Connection button
        self.test_s3_button = ttk.Button(s3_frame, text="Test S3 Connection", command=self.test_s3_connection, 
                                        state="normal" if aws_available else "disabled")
        self.test_s3_button.grid(row=s3_frame_row+3, column=1, sticky=tk.E, padx=5, pady=5)
        
        # Initialize the auth method settings
        self.toggle_auth_method()
        
        # Processing Options
        process_frame = ttk.LabelFrame(advanced_frame, text="Processing Options")
        process_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W+tk.E, padx=10, pady=5)
        
        # Use Dask for processing
        ttk.Checkbutton(process_frame, text="Use Dask for parallel processing", variable=self.use_dask).grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Initialize S3 settings state
        self.toggle_s3_settings()

    def create_bottom_buttons(self):
        """Create buttons at the bottom of the window"""
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Save Configuration", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Run Analysis", command=self.run_analysis).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.root.destroy).pack(side=tk.RIGHT, padx=5)

    def browse_data_directory(self):
        """Open file dialog to select data directory"""
        directory = filedialog.askdirectory()
        if directory:
            self.data_directory.set(directory)
            # Check for AIS data files in the selected directory
            self.check_ais_data_files(directory)

    def browse_output_directory(self):
        """Open file dialog to select output directory"""
        directory = filedialog.askdirectory()
        if directory:
            self.output_directory.set(directory)
            
    def toggle_s3_settings(self):
        """Enable/disable S3 settings based on use_s3 checkbox"""
        if not aws_available:
            # Disable S3 settings if boto3 is not available
            self.s3_uri_entry.configure(state="disabled")
            if hasattr(self, 'test_s3_button'):
                self.test_s3_button.configure(state="disabled")
            if hasattr(self, 'auth_method_frame'):
                for widget in self.auth_method_frame.winfo_children():
                    widget.configure(state="disabled")
            return
            
        if self.use_s3.get():
            # Enable S3 settings
            self.s3_uri_entry.configure(state="normal")
            self.test_s3_button.configure(state="normal")
            # Enable authentication method selection
            if hasattr(self, 'auth_method_combo'):
                self.auth_method_combo.configure(state="readonly")
            # Update authentication settings based on selected method
            self.toggle_auth_method()
        else:
            # Disable S3 settings
            self.s3_uri_entry.configure(state="disabled")
            self.test_s3_button.configure(state="disabled")
            # Disable all authentication settings
            if hasattr(self, 'auth_method_combo'):
                self.auth_method_combo.configure(state="disabled")
            if hasattr(self, 'profile_entry'):
                self.profile_entry.configure(state="disabled")
            if hasattr(self, 'access_key_entry'):
                self.access_key_entry.configure(state="disabled")
                self.secret_key_entry.configure(state="disabled")
            if hasattr(self, 'region_entry'):
                self.region_entry.configure(state="disabled")
            if hasattr(self, 'role_arn_entry'):
                self.role_arn_entry.configure(state="disabled")
                
    def toggle_auth_method(self, *args):
        """Enable/disable authentication settings based on selected auth method"""
        if not aws_available or not self.use_s3.get():
            return
            
        auth_method = self.s3_auth_method.get()
        
        # Disable all first
        if hasattr(self, 'profile_entry'):
            self.profile_entry.configure(state="disabled")
        if hasattr(self, 'access_key_entry'):
            self.access_key_entry.configure(state="disabled")
            self.secret_key_entry.configure(state="disabled")
        if hasattr(self, 'region_entry'):
            self.region_entry.configure(state="disabled")
        if hasattr(self, 'role_arn_entry'):
            self.role_arn_entry.configure(state="disabled")
        
        # Enable based on selected method
        if auth_method == "profile" and hasattr(self, 'profile_entry'):
            self.profile_entry.configure(state="normal")
        elif auth_method == "keys" and hasattr(self, 'access_key_entry'):
            self.access_key_entry.configure(state="normal")
            self.secret_key_entry.configure(state="normal")
            self.region_entry.configure(state="normal")
        elif auth_method == "role" and hasattr(self, 'role_arn_entry'):
            self.role_arn_entry.configure(state="normal")
            self.region_entry.configure(state="normal")
    
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
            # Import enhanced S3 auth module
            import sys
            import os
            script_dir = os.path.dirname(os.path.abspath(__file__))
            if script_dir not in sys.path:
                sys.path.append(script_dir)
                
            try:
                import enhanced_s3_auth
            except ImportError:
                messagebox.showerror("Error", "Could not import enhanced_s3_auth.py. Make sure it exists in the same directory as this script.")
                return
                
            # Parse the S3 URI to extract bucket name and prefix
            parts = s3_uri.replace("s3://", "").split("/")
            bucket_name = parts[0]
            prefix = "/".join(parts[1:]) if len(parts) > 1 else ""
            
            # Choose authentication method based on selection
            auth_method = self.s3_auth_method.get()
            s3_client = None
            
            if auth_method == "default":
                messagebox.showinfo("Auth Method", "Using default AWS credential provider chain")
                s3_client = enhanced_s3_auth.get_s3_client_default()
                
            elif auth_method == "profile":
                profile_name = self.s3_profile_name.get()
                if not profile_name:
                    messagebox.showerror("Error", "Profile name cannot be empty")
                    return
                    
                messagebox.showinfo("Auth Method", f"Using AWS profile: {profile_name}")
                s3_client = enhanced_s3_auth.get_s3_client_with_profile(profile_name)
                
            elif auth_method == "keys":
                access_key = self.s3_access_key.get()
                secret_key = self.s3_secret_key.get()
                region = self.s3_region.get()
                
                if not access_key or not secret_key:
                    messagebox.showerror("Error", "Access key and secret key cannot be empty")
                    return
                    
                messagebox.showinfo("Auth Method", f"Using AWS access keys in region {region}")
                s3_client = enhanced_s3_auth.get_s3_client_with_keys(access_key, secret_key, region)
                
            elif auth_method == "role":
                role_arn = self.s3_role_arn.get()
                region = self.s3_region.get()
                
                if not role_arn:
                    messagebox.showerror("Error", "Role ARN cannot be empty")
                    return
                    
                messagebox.showinfo("Auth Method", f"Using IAM role: {role_arn}")
                s3_client = enhanced_s3_auth.get_s3_client_with_role_arn(role_arn, region)
            
            # Check if we got a valid S3 client
            if s3_client is None:
                messagebox.showerror("Error", "Failed to create S3 client. Check your authentication details.")
                return
                
            # Test the connection
            success = enhanced_s3_auth.test_s3_connection(s3_client, bucket_name, prefix)
            
            if success:
                if prefix:
                    messagebox.showinfo("Success", f"Successfully connected to S3 bucket '{bucket_name}' with prefix '{prefix}'")
                else:
                    messagebox.showinfo("Success", f"Successfully connected to S3 bucket '{bucket_name}'")
            
        except botocore.exceptions.NoCredentialsError:
            messagebox.showerror("Error", "AWS credentials not found. Please configure your AWS credentials.")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error while testing S3 connection: {str(e)}")
            import traceback
            traceback.print_exc()

    
    def toggle_date_selection(self):
        """Enable/disable date controls based on date range selection"""
        if self.use_date_range.get():
            # Using date range
            self.days_spinbox.config(state='disabled')
            
            if tkcalendar_available:
                # Using DateEntry widgets
                self.start_date_picker.config(state='readonly')
                self.end_date_picker.config(state='readonly')
                # Update the string variables with selected dates
                self.start_date.set(self.start_date_picker.get_date().strftime('%Y-%m-%d'))
                self.end_date.set(self.end_date_picker.get_date().strftime('%Y-%m-%d'))
            else:
                # Using basic Entry widgets
                if hasattr(self, 'start_date_entry') and hasattr(self, 'end_date_entry'):
                    self.start_date_entry.config(state='normal')
                    self.end_date_entry.config(state='normal')
                    # Update the string variables with entered dates
                    self.start_date.set(self.start_date_entry.get())
                    self.end_date.set(self.end_date_entry.get())
        else:
            # Using days back
            self.days_spinbox.config(state='normal')
            
            if tkcalendar_available:
                # Using DateEntry widgets
                self.start_date_picker.config(state='disabled')
                self.end_date_picker.config(state='disabled')
            else:
                # Using basic Entry widgets
                if hasattr(self, 'start_date_entry') and hasattr(self, 'end_date_entry'):
                    self.start_date_entry.config(state='disabled')
                    self.end_date_entry.config(state='disabled')

    def select_all_anomalies(self):
        """Select all anomaly types"""
        for var in self.anomaly_types.values():
            var.set(True)

    def deselect_all_anomalies(self):
        """Deselect all anomaly types"""
        for var in self.anomaly_types.values():
            var.set(False)

    def load_config(self):
        """Load configuration from config.ini if it exists"""
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
            if 'USE_DATE_RANGE' in config['DEFAULT']:
                self.use_date_range.set(config['DEFAULT'].getboolean('USE_DATE_RANGE'))
            if 'NUM_DAYS' in config['DEFAULT']:
                self.num_days.set(int(config['DEFAULT']['NUM_DAYS']))
            if 'START_DATE' in config['DEFAULT'] and config['DEFAULT']['START_DATE']:
                self.start_date.set(config['DEFAULT']['START_DATE'])
                try:
                    self.start_date_picker.set_date(datetime.strptime(config['DEFAULT']['START_DATE'], '%Y-%m-%d').date())
                except (ValueError, AttributeError):
                    pass  # If date is invalid, keep the default
            if 'END_DATE' in config['DEFAULT'] and config['DEFAULT']['END_DATE']:
                self.end_date.set(config['DEFAULT']['END_DATE'])
                try:
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
                    
        # Load S3 settings if available
        if 'S3_SETTINGS' in config:
            if 'USE_S3' in config['S3_SETTINGS']:
                self.use_s3.set(config['S3_SETTINGS'].getboolean('USE_S3'))
            if 'S3_DATA_URI' in config['S3_SETTINGS']:
                self.s3_data_uri.set(config['S3_SETTINGS']['S3_DATA_URI'])
            
            # Load authentication method and related settings
            if 'AUTH_METHOD' in config['S3_SETTINGS']:
                self.s3_auth_method.set(config['S3_SETTINGS']['AUTH_METHOD'])
            if 'PROFILE_NAME' in config['S3_SETTINGS']:
                self.s3_profile_name.set(config['S3_SETTINGS']['PROFILE_NAME'])
            if 'ACCESS_KEY' in config['S3_SETTINGS']:
                self.s3_access_key.set(config['S3_SETTINGS']['ACCESS_KEY'])
            if 'SECRET_KEY' in config['S3_SETTINGS']:
                self.s3_secret_key.set(config['S3_SETTINGS']['SECRET_KEY'])
            if 'REGION' in config['S3_SETTINGS']:
                self.s3_region.set(config['S3_SETTINGS']['REGION'])
            if 'ROLE_ARN' in config['S3_SETTINGS']:
                self.s3_role_arn.set(config['S3_SETTINGS']['ROLE_ARN'])
                
            # Update S3 UI elements if they exist
            if hasattr(self, 's3_uri_entry') and hasattr(self, 'toggle_s3_settings'):
                self.toggle_s3_settings()
                if hasattr(self, 'auth_method_combo'):
                    self.toggle_auth_method()

    def save_config(self):
        """Save configuration to config.ini"""
        config = configparser.ConfigParser()
        
        # General settings
        config['DEFAULT'] = {
            'DATA_DIRECTORY': self.data_directory.get(),
            'OUTPUT_DIRECTORY': self.output_directory.get(),
            'USE_DATE_RANGE': str(self.use_date_range.get()),
            'NUM_DAYS': str(self.num_days.get())
        }
        
        # Update date values if using date range
        if self.use_date_range.get():
            # Get the current selected dates from pickers
            self.start_date.set(self.start_date_picker.get_date().strftime('%Y-%m-%d'))
            self.end_date.set(self.end_date_picker.get_date().strftime('%Y-%m-%d'))
            
        # Always save date values even if not currently using date range
        config['DEFAULT']['START_DATE'] = self.start_date.get()
        config['DEFAULT']['END_DATE'] = self.end_date.get()
        
        # Ship filters - get selected ship types
        selected_types = [str(ship_type) for ship_type in self.ship_types if self.ship_types[ship_type]['var'].get()]
        config['SHIP_FILTERS'] = {
            'SELECTED_SHIP_TYPES': ','.join(selected_types)
        }
        
        # Anomaly thresholds
        config['ANOMALY_THRESHOLDS'] = {
            'MIN_TRAVEL_NM': str(self.min_travel_nm.get()),
            'MAX_TRAVEL_NM': str(self.max_travel_nm.get()),
            'COG_HEADING_MAX_DIFF': str(self.cog_heading_max_diff.get()),
            'MIN_SPEED_FOR_COG_CHECK': str(self.min_speed_for_cog_check.get())
        }
        
        # Anomaly types to detect
        config['ANOMALY_TYPES'] = {}
        for anomaly_type, var in self.anomaly_types.items():
            # Handle special case for Course over Ground-Heading renamed from COG-Heading
            if anomaly_type == "Course over Ground-Heading Inconsistency":
                key = "COG-Heading_Inconsistency"
            else:
                key = anomaly_type.replace(' ', '_').replace('(', '').replace(')', '')
            config['ANOMALY_TYPES'][key] = str(var.get())
            
        # S3 settings
        config['S3_SETTINGS'] = {
            'USE_S3': str(self.use_s3.get()),
            'S3_DATA_URI': self.s3_data_uri.get(),
            'AUTH_METHOD': self.s3_auth_method.get(),
            'PROFILE_NAME': self.s3_profile_name.get(),
            'ACCESS_KEY': self.s3_access_key.get(),
            'SECRET_KEY': self.s3_secret_key.get(),
            'REGION': self.s3_region.get(),
            'ROLE_ARN': self.s3_role_arn.get()
        }
        
        # Get the script directory for the config file path
        if getattr(sys, 'frozen', False):
            script_dir = os.path.dirname(sys.executable)
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
        config_path = os.path.join(script_dir, 'config.ini')
        
        # Try to write to file
        try:
            with open(config_path, 'w') as configfile:
                config.write(configfile)
                
            messagebox.showinfo("Configuration Saved", f"Configuration has been saved to {config_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}\n\nMake sure you have write permissions to the application directory.")

    def run_analysis(self):
        """Run the shipping fraud detection analysis"""
        # Validate inputs
        if self.use_s3.get() and aws_available:
            # Using S3 for data
            s3_uri = self.s3_data_uri.get()
            if not s3_uri.startswith('s3://'):
                messagebox.showerror("Error", "Invalid S3 URI format. It should start with 's3://'")
                return
                
            # Check if S3 bucket is accessible
            try:
                # Parse the S3 URI to extract bucket name and prefix
                parts = s3_uri.replace("s3://", "").split("/")
                bucket_name = parts[0]
                prefix = "/".join(parts[1:]) if len(parts) > 1 else ""
                
                # Create an S3 client
                s3 = boto3.client('s3')
                s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix, MaxKeys=1)
            except Exception as e:
                messagebox.showerror("Error", f"Cannot access S3 bucket: {str(e)}")
                return
                
        elif not self.data_directory.get():
            messagebox.showerror("Error", "Please specify a data directory")
            return
            
        if not self.output_directory.get():
            messagebox.showerror("Error", "Please specify an output directory")
            return
        
        # Check if data directory exists
        if not os.path.exists(self.data_directory.get()):
            messagebox.showerror("Error", f"Data directory does not exist:\n{self.data_directory.get()}")
            return
            
        # Check for AIS data files in the data directory
        self.check_ais_data_files(self.data_directory.get())
        
        # Check if output directory exists, create it if not
        if not os.path.exists(self.output_directory.get()):
            try:
                os.makedirs(self.output_directory.get())
                messagebox.showinfo("Directory Created", f"Output directory created:\n{self.output_directory.get()}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not create output directory:\n{str(e)}")
                return
        
        # Check write permissions on output directory
        test_file_path = os.path.join(self.output_directory.get(), "test_write_permission.tmp")
        try:
            with open(test_file_path, 'w') as f:
                f.write("test")
            os.remove(test_file_path)  # Clean up the test file
        except Exception as e:
            messagebox.showerror("Error", f"Cannot write to output directory:\n{str(e)}\n\nPlease choose a directory with write permissions.")
            return
            
        # Save configuration first
        self.save_config()
        
        # Verify required files still exist
        if getattr(sys, 'frozen', False):
            script_dir = os.path.dirname(sys.executable)
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
        script_path = os.path.join(script_dir, "shipping_fraud_detection.py")
        config_path = os.path.join(script_dir, "config.ini")
        
        if not os.path.exists(script_path):
            messagebox.showerror("Error", "Required file 'shipping_fraud_detection.py' not found.")
            return
            
        if not os.path.exists(config_path):
            messagebox.showerror("Error", "Required file 'config.ini' not found.")
            return
        
        # Get the script path - handle both running as script and as frozen executable
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            script_dir = os.path.dirname(sys.executable)
        else:
            # Running as a script
            script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Build command to run shipping_fraud_detection.py
        script_path = os.path.join(script_dir, "shipping_fraud_detection.py")
        cmd = [
            sys.executable,
            script_path,
            "--config", os.path.join(script_dir, "config.ini")
        ]
        
        # Add S3 URI if enabled
        if self.use_s3.get() and aws_available:
            cmd.extend(["--s3-uri", self.s3_data_uri.get()])
            
            # Add authentication options based on selected method
            auth_method = self.s3_auth_method.get()
            
            if auth_method == "profile" and self.s3_profile_name.get():
                cmd.extend(["--profile", self.s3_profile_name.get()])
            elif auth_method == "keys" and self.s3_access_key.get() and self.s3_secret_key.get():
                cmd.extend(["--access-key", self.s3_access_key.get()])
                cmd.extend(["--secret-key", self.s3_secret_key.get()])
                cmd.extend(["--region", self.s3_region.get()])
            elif auth_method == "role" and self.s3_role_arn.get():
                cmd.extend(["--role-arn", self.s3_role_arn.get()])
                cmd.extend(["--region", self.s3_region.get()])
        
        # Add date parameters based on selection method
        if self.use_date_range.get():
            # Get date values based on available widgets
            if tkcalendar_available:
                # Get values from DateEntry widgets
                start_date_str = self.start_date_picker.get_date().strftime('%Y-%m-%d')
                end_date_str = self.end_date_picker.get_date().strftime('%Y-%m-%d')
            else:
                # Get values from Entry widgets
                start_date_str = self.start_date_entry.get()
                end_date_str = self.end_date_entry.get()
                
                # Validate the date formats
                try:
                    # Try to parse the dates to ensure they are valid
                    datetime.strptime(start_date_str, '%Y-%m-%d')
                    datetime.strptime(end_date_str, '%Y-%m-%d')
                except ValueError:
                    messagebox.showerror("Invalid Date Format", 
                                      "Please enter dates in the format YYYY-MM-DD.")
                    return
            
            cmd.extend(["--start-date", start_date_str, "--end-date", end_date_str])
        else:
            cmd.extend(["--days", str(self.num_days.get())])
        
        # Add selected ship types as a command line argument
        selected_types = [str(ship_type) for ship_type in self.ship_types if self.ship_types[ship_type]['var'].get()]
        if selected_types:
            cmd.extend(["--ship-types", ",".join(selected_types)])
        
        if not self.use_dask.get():
            cmd.append("--no-dask")
            
        # Run the command
        try:
            # Prepare message based on date range selection
            if self.use_date_range.get():
                start_date = self.start_date_picker.get_date().strftime('%Y-%m-%d')
                end_date = self.end_date_picker.get_date().strftime('%Y-%m-%d')
                message = f"Starting analysis for date range {start_date} to {end_date}.\n"
            else:
                message = f"Starting analysis for {self.num_days.get()} days of data.\n"
                
            messagebox.showinfo("Analysis Started", 
                               message + "This may take some time depending on the amount of data.")
            
            # Create a console window for output on Windows
            if platform.system() == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = win32con.SW_SHOW  # Use win32con.SW_SHOW instead of subprocess.SW_SHOW
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                         text=True, startupinfo=startupinfo)
            else:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                # Prepare completion message based on date selection mode
                if self.use_date_range.get():
                    if tkcalendar_available:
                        start_date_str = self.start_date_picker.get_date().strftime('%Y-%m-%d')
                        end_date_str = self.end_date_picker.get_date().strftime('%Y-%m-%d')
                    else:
                        start_date_str = self.start_date_entry.get()
                        end_date_str = self.end_date_entry.get()
                        
                    completion_message = f"Analysis for date range {start_date_str} to {end_date_str} completed successfully.\n"
                else:
                    completion_message = f"Analysis for the last {self.num_days.get()} days completed successfully.\n"
                    
                messagebox.showinfo("Analysis Complete", 
                                   completion_message + 
                                   f"Results saved to {self.output_directory.get()}")
                
            else:
                messagebox.showerror("Error", f"Analysis failed with error:\n{stderr}")
                
        except Exception as e:
            error_msg = f"Failed to run analysis: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            messagebox.showerror("Error", error_msg)
            
        # Open output directory after successful analysis
        try:
            if process.returncode == 0:
                try:
                    if platform.system() == "Windows":
                        os.startfile(self.output_directory.get())
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.call(["open", self.output_directory.get()])
                    else:  # Linux
                        subprocess.call(["xdg-open", self.output_directory.get()])
                except Exception as e:
                    pass  # Silently ignore if we can't open the directory
        except UnboundLocalError:
            # process variable might not be defined if an exception occurred earlier
            pass


    def check_ais_data_files(self, directory):
        """Check for AIS data files in the selected directory"""
        # Get all CSV and Parquet files in the directory
        csv_files = glob.glob(os.path.join(directory, "*.csv"))
        parquet_files = glob.glob(os.path.join(directory, "*.parquet"))
        
        # Check if any files match the expected date format (with or without ais- prefix)
        csv_pattern = re.compile(r'(?:ais-)?\d{4}-\d{2}-\d{2}\.csv$')
        parquet_pattern = re.compile(r'(?:ais-)?\d{4}-\d{2}-\d{2}\.parquet$')
        
        csv_ais_files = [f for f in csv_files if csv_pattern.search(os.path.basename(f))]
        parquet_ais_files = [f for f in parquet_files if parquet_pattern.search(os.path.basename(f))]
        
        ais_data_files = csv_ais_files + parquet_ais_files
        
        if not ais_data_files:
            messagebox.showwarning(
                "No AIS Data Files Found", 
                f"No AIS data files with the format 'ais-YYYY-MM-DD.csv', 'ais-YYYY-MM-DD.parquet', 'YYYY-MM-DD.csv', or 'YYYY-MM-DD.parquet' were found in:\n{directory}\n\n"
                "Please make sure your AIS data files are named with the correct date format."
            )
        else:
            # Check if the files have the required columns
            if not import_pandas():
                messagebox.showwarning(
                    "Missing Dependency", 
                    "Pandas is required to check the file format. Please install it using pip install pandas."
                )
                return
                
            try:
                # Try to read the first few lines of the first file
                sample_file = ais_data_files[0]
                
                # Determine file type and read accordingly
                if sample_file.lower().endswith('.csv'):
                    sample_df = pd.read_csv(sample_file, nrows=100)  # Read more rows to better check for null values
                elif sample_file.lower().endswith('.parquet'):
                    sample_df = pd.read_parquet(sample_file)
                    # For Parquet, we can't limit rows easily, so just use the whole file
                    # If it's too large, consider using a subset: sample_df = sample_df.head(100)
                else:
                    raise ValueError(f"Unsupported file format: {sample_file}")
                
                # Check for required columns
                required_columns = [
                    'MMSI', 'VesselName', 'VesselType', 'LAT', 'LON',
                    'BaseDateTime', 'SOG', 'Heading', 'COG'
                ]
                
                missing_columns = [col for col in required_columns if col not in sample_df.columns]
                
                if missing_columns:
                    messagebox.showwarning(
                        "Missing Columns", 
                        f"The AIS data files are missing the following required columns:\n\n"
                        f"{', '.join(missing_columns)}\n\n"
                        "The analysis may not work correctly without these columns."
                    )
                else:
                    # Check for null values in required columns
                    null_columns = {}
                    for col in required_columns:
                        null_count = sample_df[col].isnull().sum()
                        if null_count > 0:
                            null_columns[col] = null_count
                    
                    if null_columns:
                        null_info = "\n".join([f"{col}: {count} null values" for col, count in null_columns.items()])
                        messagebox.showinfo(
                            "Null Values Detected", 
                            f"The following columns contain null values in the sample data:\n\n"
                            f"{null_info}\n\n"
                            "These null values will be included in the analysis and ships with null values "
                            "will be reported as part of the anomaly detection."
                        )
            except Exception as e:
                # If there's an error reading the file, just show a warning
                messagebox.showwarning(
                    "File Format Warning", 
                    f"Could not verify the format of the AIS data files:\n{str(e)}\n\n"
                    "Please make sure your files are properly formatted CSV or Parquet files."
                )
    
    def check_required_files(self):
        """Check that all required files exist before running the application"""
        # Get the script directory
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            script_dir = os.path.dirname(sys.executable)
        else:
            # Running as a script
            script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # List of required files
        required_files = [
            ("shipping_fraud_detection.py", "Main detection script"),
            ("config.ini", "Configuration file")
        ]
        
        missing_files = []
        
        # Check each required file
        for file_name, description in required_files:
            file_path = os.path.join(script_dir, file_name)
            if not os.path.exists(file_path):
                missing_files.append(f"{file_name} ({description})")
        
        # If any files are missing, show an error and exit
        if missing_files:
            error_message = "The following required files are missing:\n\n"
            error_message += "\n".join(missing_files)
            error_message += "\n\nPlease ensure all required files are in the same directory as this application."
            messagebox.showerror("Missing Files", error_message)
            self.root.after(100, self.root.destroy)  # Give time for the message to be shown
            return
        
        # Check if shipping_fraud_detection.py is valid Python file
        try:
            with open(os.path.join(script_dir, "shipping_fraud_detection.py"), "r") as f:
                # Just try to read the first few lines to verify it's a valid file
                for _ in range(10):
                    if not f.readline():
                        break
        except Exception as e:
            error_message = f"Error reading shipping_fraud_detection.py: {str(e)}\n\n"
            error_message += "The file may be corrupted or inaccessible."
            messagebox.showerror("File Error", error_message)
            self.root.after(100, self.root.destroy())
            return
        
        # Check if config.ini is a valid configuration file
        try:
            config = configparser.ConfigParser()
            config.read(os.path.join(script_dir, "config.ini"))
            
            # Check for required sections
            required_sections = ["DEFAULT", "SHIP_FILTERS", "ANOMALY_THRESHOLDS"]
            missing_sections = [section for section in required_sections if section not in config]
            
            if missing_sections:
                error_message = "The config.ini file is missing the following required sections:\n\n"
                error_message += "\n".join(missing_sections)
                messagebox.showwarning("Configuration Warning", error_message)
                # Don't exit, just warn the user
        except Exception as e:
            error_message = f"Error reading config.ini: {str(e)}\n\n"
            error_message += "The file may be corrupted or not a valid configuration file."
            messagebox.showwarning("Configuration Warning", error_message)
            # Don't exit, just warn the user

def main():
    """Main entry point for the application"""
    try:
        logger.info("Starting AIS Shipping Fraud Detection GUI")
        root = tk.Tk()
        app = AnomalyDetectionGUI(root)
        return root
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}")
        logger.critical(traceback.format_exc())
        # Try to show error message even if GUI fails
        try:
            import tkinter.messagebox
            tkinter.messagebox.showerror("Critical Error", 
                                      f"An unhandled error occurred: {str(e)}\n\n"
                                      f"Please check the log file: gui_error.log")
        except:
            print(f"CRITICAL ERROR: {str(e)}")
            print("See gui_error.log for details.")
        sys.exit(1)

if __name__ == "__main__":
    root = main()
    root.mainloop()

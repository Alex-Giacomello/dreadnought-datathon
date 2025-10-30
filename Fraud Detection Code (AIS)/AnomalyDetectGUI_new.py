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
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timedelta
import sys
import subprocess
import platform
import time
import re
import glob
import traceback
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gui_error.log"),
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
            70: {'name': 'Cargo, all ships of this type', 'var': tk.BooleanVar(value=True)},
            71: {'name': 'Cargo, Hazardous category A', 'var': tk.BooleanVar(value=False)},
            72: {'name': 'Cargo, Hazardous category B', 'var': tk.BooleanVar(value=False)},
            73: {'name': 'Cargo, Hazardous category C', 'var': tk.BooleanVar(value=False)},
            74: {'name': 'Cargo, Hazardous category D', 'var': tk.BooleanVar(value=False)},
            75: {'name': 'Cargo, Reserved for future use', 'var': tk.BooleanVar(value=False)},
            76: {'name': 'Cargo, Reserved for future use', 'var': tk.BooleanVar(value=False)},
            77: {'name': 'Cargo, Reserved for future use', 'var': tk.BooleanVar(value=False)},
            78: {'name': 'Cargo, Reserved for future use', 'var': tk.BooleanVar(value=False)},
            79: {'name': 'Cargo, No additional information', 'var': tk.BooleanVar(value=False)},
            80: {'name': 'Tanker, all ships of this type', 'var': tk.BooleanVar(value=True)},
            81: {'name': 'Tanker, Hazardous category A', 'var': tk.BooleanVar(value=False)},
            82: {'name': 'Tanker, Hazardous category B', 'var': tk.BooleanVar(value=False)},
            83: {'name': 'Tanker, Hazardous category C', 'var': tk.BooleanVar(value=False)},
            84: {'name': 'Tanker, Hazardous category D', 'var': tk.BooleanVar(value=False)},
            85: {'name': 'Tanker, Reserved for future use', 'var': tk.BooleanVar(value=False)},
            86: {'name': 'Tanker, Reserved for future use', 'var': tk.BooleanVar(value=False)},
            87: {'name': 'Tanker, Reserved for future use', 'var': tk.BooleanVar(value=False)},
            88: {'name': 'Tanker, Reserved for future use', 'var': tk.BooleanVar(value=False)},
            89: {'name': 'Tanker, No additional information', 'var': tk.BooleanVar(value=False)}
        }
        self.min_travel_nm = tk.DoubleVar(value=200)
        self.max_travel_nm = tk.DoubleVar(value=550)
        self.cog_heading_max_diff = tk.DoubleVar(value=45)
        self.min_speed_for_cog_check = tk.DoubleVar(value=10)
        self.num_days = tk.IntVar(value=5)
        self.use_dask = tk.BooleanVar(value=True)
        
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_general_tab()
        self.create_ship_types_tab()
        self.create_anomaly_types_tab()
        self.create_thresholds_tab()
        self.create_advanced_tab()
        
        # Create bottom buttons
        self.create_bottom_buttons()
        
        # Load config if exists
        self.load_config()

    def create_general_tab(self):
        """Create the General tab with basic settings"""
        general_frame = ttk.Frame(self.notebook)
        self.notebook.add(general_frame, text="General")
        
        # Data Directory
        ttk.Label(general_frame, text="Data Directory:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(general_frame, textvariable=self.data_directory, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(general_frame, text="Browse...", command=self.browse_data_directory).grid(row=0, column=2, padx=5, pady=5)
        
        # Output Directory
        ttk.Label(general_frame, text="Output Directory:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(general_frame, textvariable=self.output_directory, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(general_frame, text="Browse...", command=self.browse_output_directory).grid(row=1, column=2, padx=5, pady=5)
        
        # Number of days to analyze
        ttk.Label(general_frame, text="Number of days to analyze:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Spinbox(general_frame, from_=1, to=365, textvariable=self.num_days, width=10).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Ship Type Selection note
        ttk.Label(general_frame, text="Ship Types:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(general_frame, text="Use the 'Ship Types' tab to select specific ship types").grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

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
        """Create the Anomaly Types tab with checkboxes for each type"""
        anomaly_frame = ttk.Frame(self.notebook)
        self.notebook.add(anomaly_frame, text="Anomaly Types")
        
        ttk.Label(anomaly_frame, text="Select anomaly types to detect:", font=("", 12)).grid(row=0, column=0, sticky=tk.W, padx=5, pady=10)
        
        # Create checkboxes for each anomaly type
        for i, (anomaly_type, var) in enumerate(self.anomaly_types.items()):
            ttk.Checkbutton(anomaly_frame, text=anomaly_type, variable=var).grid(row=i+1, column=0, sticky=tk.W, padx=20, pady=5)
            
        # Add a "Select All" button
        ttk.Button(anomaly_frame, text="Select All", command=self.select_all_anomalies).grid(row=len(self.anomaly_types)+1, column=0, sticky=tk.W, padx=5, pady=10)
        ttk.Button(anomaly_frame, text="Deselect All", command=self.deselect_all_anomalies).grid(row=len(self.anomaly_types)+1, column=1, sticky=tk.W, padx=5, pady=10)

    def create_thresholds_tab(self):
        """Create the Thresholds tab with settings for anomaly detection thresholds"""
        thresholds_frame = ttk.Frame(self.notebook)
        self.notebook.add(thresholds_frame, text="Thresholds")
        
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

    def create_advanced_tab(self):
        """Create the Advanced tab with additional settings"""
        advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(advanced_frame, text="Advanced")
        
        # Use Dask for processing
        ttk.Checkbutton(advanced_frame, text="Use Dask for parallel processing", variable=self.use_dask).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Add more advanced options as needed

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

    def save_config(self):
        """Save configuration to config.ini"""
        config = configparser.ConfigParser()
        
        # General settings
        config['DEFAULT'] = {
            'DATA_DIRECTORY': self.data_directory.get(),
            'OUTPUT_DIRECTORY': self.output_directory.get()
        }
        
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
        if not self.data_directory.get():
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
            "--days", str(self.num_days.get()),
            "--config", os.path.join(script_dir, "config.ini")
        ]
        
        # Add selected ship types as a command line argument
        selected_types = [str(ship_type) for ship_type in self.ship_types if self.ship_types[ship_type]['var'].get()]
        if selected_types:
            cmd.extend(["--ship-types", ",".join(selected_types)])
        
        if not self.use_dask.get():
            cmd.append("--no-dask")
            
        # Run the command
        try:
            messagebox.showinfo("Analysis Started", 
                               f"Starting analysis for {self.num_days.get()} days of data.\n"
                               f"This may take some time depending on the amount of data.")
            
            # Create a console window for output on Windows
            if platform.system() == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_SHOW
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                         text=True, startupinfo=startupinfo)
            else:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                messagebox.showinfo("Analysis Complete", 
                                   f"Analysis completed successfully.\n"
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
                    'MMSI', 'ShipName', 'ShipType', 'Latitude', 'Longitude',
                    'Timestamp', 'Speed', 'Heading', 'COG'
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
            required_sections = ["DEFAULT", "SHIP_FILTERS", "ANOMALY_THRESHOLDS", "TIMESTAMPS"]
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

if __name__ == "__main__":
    try:
        logger.info("Starting AIS Shipping Fraud Detection GUI")
        root = tk.Tk()
        app = AnomalyDetectionGUI(root)
        root.mainloop()
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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIS Shipping Fraud Detection System Installer

This script installs the AIS Shipping Fraud Detection System.
It checks for required dependencies, creates necessary files,
and sets up the environment for running the application.
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import shutil
import time
import platform

class InstallerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AIS Shipping Fraud Detection System Installer")
        self.root.geometry("700x500")
        self.root.resizable(False, False)
        
        # Set up the main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="AIS Shipping Fraud Detection System Installer", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Description
        desc_text = ("This installer will set up the AIS Shipping Fraud Detection System on your computer. "
                    "It will perform the following actions:")
        desc_label = ttk.Label(main_frame, text=desc_text, wraplength=650)
        desc_label.pack(pady=10, anchor="w")
        
        # Actions list
        actions_frame = ttk.Frame(main_frame)
        actions_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        actions = [
            "Verify Python and pip are properly installed",
            "Check for required Python dependencies and install them if missing",
            "Create a desktop shortcut for easy access",
            "Set up the configuration file with default settings",
            "Create necessary directories for data and reports"
        ]
        
        for i, action in enumerate(actions):
            action_label = ttk.Label(actions_frame, text=f"{i+1}. {action}", wraplength=650)
            action_label.pack(anchor="w", pady=3)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(main_frame, orient="horizontal", 
                                       length=650, mode="determinate", 
                                       variable=self.progress_var)
        self.progress.pack(pady=20)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to install")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(pady=5)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        # Install button
        self.install_button = ttk.Button(buttons_frame, text="Install", 
                                        command=self.start_installation, width=15)
        self.install_button.pack(side=tk.LEFT, padx=5)
        
        # Cancel button
        self.cancel_button = ttk.Button(buttons_frame, text="Cancel", 
                                       command=self.root.destroy, width=15)
        self.cancel_button.pack(side=tk.RIGHT, padx=5)
    
    def start_installation(self):
        """Start the installation process"""
        result = messagebox.askokcancel(
            "Confirm Installation",
            "This will install the AIS Shipping Fraud Detection System. Do you want to continue?"
        )
        
        if result:
            self.install_button.config(state="disabled")
            self.cancel_button.config(state="disabled")
            self.progress_var.set(0)
            self.perform_installation()
    
    def update_progress(self, value, status):
        """Update the progress bar and status label"""
        self.progress_var.set(value)
        self.status_var.set(status)
        self.root.update()
    
    def perform_installation(self):
        """Perform the actual installation steps"""
        try:
            # Step 1: Check Python and pip installation
            self.update_progress(5, "Checking Python and pip installation...")
            python_ok, pip_ok = self.check_python_pip()
            
            if not python_ok or not pip_ok:
                return
            
            # Step 2: Check Python dependencies
            self.update_progress(20, "Checking Python dependencies...")
            self.check_dependencies()
            
            # Step 3: Create directories
            self.update_progress(40, "Creating directories...")
            self.create_directories()
            
            # Step 4: Set up configuration
            self.update_progress(60, "Setting up configuration...")
            self.setup_configuration()
            
            # Step 5: Create desktop shortcut
            self.update_progress(80, "Creating desktop shortcut...")
            self.create_shortcut()
            
            # Step 6: Finalize installation
            self.update_progress(90, "Finalizing installation...")
            time.sleep(1)  # Just for visual effect
            
            # Installation complete
            self.update_progress(100, "Installation complete!")
            messagebox.showinfo(
                "Installation Complete",
                "The AIS Shipping Fraud Detection System has been successfully installed."
            )
            
            # Re-enable buttons
            self.install_button.config(state="normal")
            self.cancel_button.config(state="normal")
            self.cancel_button.config(text="Close")
            
        except Exception as e:
            messagebox.showerror("Installation Error", f"An error occurred during installation: {str(e)}")
            self.install_button.config(state="normal")
            self.cancel_button.config(state="normal")
    
    def check_python_pip(self):
        """Check if Python and pip are installed"""
        python_ok = True
        pip_ok = True
        
        # Check Python
        try:
            python_version = platform.python_version()
            self.update_progress(8, f"Python {python_version} detected")
        except:
            python_ok = False
            if messagebox.askokcancel("Python Required",
                                    "Python is required but not detected. Would you like to use "
                                    "the Python Install Manager to install the correct version?"):
                self.update_progress(10, "Installing Python Install Manager...")
                try:
                    subprocess.run(["winget", "install", "9NQ7512CXL7T"], check=True, shell=True)
                    messagebox.showinfo("Installation", 
                                      "Python Install Manager has been installed. Please use it to "
                                      "install Python 3.9 or higher, then run this installer again.")
                    self.root.destroy()
                    return False, False
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to install Python Install Manager: {str(e)}")
                    self.root.destroy()
                    return False, False
            else:
                messagebox.showinfo("Installation Canceled", 
                                  "Python is required to install AIS Shipping Fraud Detection System. "
                                  "Please install Python and try again.")
                self.root.destroy()
                return False, False
        
        # Check pip
        if python_ok:
            try:
                result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                     text=True, check=False)
                if result.returncode == 0:
                    pip_version = result.stdout.split()[1]
                    self.update_progress(12, f"pip {pip_version} detected")
                else:
                    pip_ok = False
                    messagebox.showerror("pip Required", 
                                      "pip is required but not installed properly. "
                                      "Please ensure pip is installed with your Python installation.")
                    self.root.destroy()
                    return False, False
            except:
                pip_ok = False
                messagebox.showerror("pip Required", 
                                  "pip is required but not installed properly. "
                                  "Please ensure pip is installed with your Python installation.")
                self.root.destroy()
                return False, False
        
        return python_ok, pip_ok
        
    def check_dependencies(self):
        """Check and install required Python dependencies"""
        required_packages = [
            "pandas", "numpy", "dask", "folium", "matplotlib", 
            "seaborn", "geopy", "configparser", "tkinter", "pyinstaller",
            "tkcalendar", "pyarrow"
        ]
        
        for package in required_packages:
            try:
                # Try to import the package
                if package == "tkinter":
                    import tkinter
                else:
                    __import__(package)
            except ImportError:
                # If import fails, try to install the package
                self.status_var.set(f"Installing {package}...")
                self.root.update()
                
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                except subprocess.CalledProcessError:
                    raise Exception(f"Failed to install {package}. Please install it manually.")
    
    def create_directories(self):
        """Create necessary directories for the application"""
        # Get user's home directory
        home_dir = os.path.expanduser("~")
        
        # Create directories
        dirs = [
            os.path.join(home_dir, "AIS_Data"),
            os.path.join(home_dir, "AIS_Data", "Reports")
        ]
        
        for directory in dirs:
            if not os.path.exists(directory):
                os.makedirs(directory)
    
    def setup_configuration(self):
        """Set up the configuration file"""
        # Get the script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Create config parser
        config = configparser.ConfigParser()
        
        # Default section
        config['DEFAULT'] = {
            'DATA_DIRECTORY': os.path.join(os.path.expanduser("~"), "AIS_Data"),
            'OUTPUT_DIRECTORY': os.path.join(os.path.expanduser("~"), "AIS_Data", "Reports")
        }
        
        # Ship filters section
        config['SHIP_FILTERS'] = {
            'SELECTED_SHIP_TYPES': '70,80'
        }
        
        # Anomaly thresholds section
        config['ANOMALY_THRESHOLDS'] = {
            'MIN_TRAVEL_NM': '200',
            'MAX_TRAVEL_NM': '550',
            'COG_HEADING_MAX_DIFF': '45',
            'MIN_SPEED_FOR_COG_CHECK': '10'
        }
        
        # Timestamps section
        config['TIMESTAMPS'] = {
            'FORMAT': '%%Y-%%m-%%d %%H:%%M:%%S'
        }
        
        # Anomaly types section
        config['ANOMALY_TYPES'] = {
            'AIS_Beacon_Off': 'True',
            'AIS_Beacon_On': 'True',
            'Excessive_Travel_Distance_Fast': 'True',
            'Excessive_Travel_Distance_Slow': 'True',
            'COG-Heading_Inconsistency': 'True'
        }
        
        # Write the configuration file
        with open(os.path.join(script_dir, 'config.ini'), 'w') as configfile:
            config.write(configfile)
    
    def create_shortcut(self):
        """Create a desktop shortcut for the application"""
        # Get the script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Get the desktop directory
        desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        
        # Create a batch file to run the application
        batch_path = os.path.join(script_dir, "Shipping Fraud Detection.bat")
        with open(batch_path, 'w') as f:
            f.write('@echo off\n')
            f.write('echo Starting AIS Shipping Fraud Detection System...\n')
            f.write(f'cd /d "{script_dir}"\n')
            f.write('start pythonw AnomalyDetectGUI_new.py\n')
            
        # Create a batch file to run the uninstaller
        uninstall_batch_path = os.path.join(script_dir, "Uninstall Anomaly Detection.bat")
        with open(uninstall_batch_path, 'w') as f:
            f.write('@echo off\n')
            f.write('echo Starting AIS Shipping Fraud Detection System Uninstaller...\n')
            f.write(f'cd /d "{script_dir}"\n')
            f.write('start pythonw uninstaller.py\n')
        
        # Create a shortcut on the desktop using PowerShell
        shortcut_path = os.path.join(desktop_dir, "AIS Shipping Fraud Detection.lnk")
        uninstall_shortcut_path = os.path.join(desktop_dir, "Uninstall Anomaly Detection.lnk")
        
        # PowerShell command to create shortcuts
        ps_command = f"""
        $WshShell = New-Object -ComObject WScript.Shell
        
        # Create application shortcut
        $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
        $Shortcut.TargetPath = "{batch_path}"
        $Shortcut.WorkingDirectory = "{script_dir}"
        $Shortcut.Description = "AIS Shipping Fraud Detection System"
        $Shortcut.Save()
        
        # Create uninstaller shortcut
        $UninstallShortcut = $WshShell.CreateShortcut("{uninstall_shortcut_path}")
        $UninstallShortcut.TargetPath = "{uninstall_batch_path}"
        $UninstallShortcut.WorkingDirectory = "{script_dir}"
        $UninstallShortcut.Description = "Uninstall AIS Shipping Fraud Detection System"
        $UninstallShortcut.Save()
        """
        
        # Run PowerShell command
        try:
            result = subprocess.run(["powershell", "-Command", ps_command], 
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=True, text=True)
            if result.returncode != 0:
                raise Exception(f"PowerShell error: {result.stderr}")
        except Exception as e:
            # If PowerShell fails, try alternative method or just log the error
            print(f"Warning: Could not create shortcut: {str(e)}")
            # Create a simple batch file as fallback
            with open(shortcut_path.replace(".lnk", ".bat"), 'w') as f:
                f.write(f'@echo off\ncd /d "{script_dir}"\npythonw AnomalyDetectGUI_new.py\n')


if __name__ == "__main__":
    root = tk.Tk()
    app = InstallerGUI(root)
    root.mainloop()

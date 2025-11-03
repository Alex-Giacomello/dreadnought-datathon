#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIS Shipping Fraud Detection System Uninstaller

This script uninstalls the AIS Shipping Fraud Detection System.
It removes created files, shortcuts, and configuration settings.
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import shutil
import time
import logging
import traceback

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("uninstall.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Uninstaller")

class UninstallerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AIS Shipping Fraud Detection System Uninstaller")
        self.root.geometry("700x500")
        self.root.resizable(False, False)
        
        # Set up the main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="AIS Shipping Fraud Detection System Uninstaller", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Description
        desc_text = ("This uninstaller will remove the AIS Shipping Fraud Detection System from your computer. "
                    "It will perform the following actions:")
        desc_label = ttk.Label(main_frame, text=desc_text, wraplength=650)
        desc_label.pack(pady=10, anchor="w")
        
        # Actions list
        actions_frame = ttk.Frame(main_frame)
        actions_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        actions = [
            "Remove desktop shortcuts",
            "Remove configuration files",
            "Remove batch files created during installation",
            "Optionally remove data and report files"
        ]
        
        for i, action in enumerate(actions):
            action_label = ttk.Label(actions_frame, text=f"{i+1}. {action}", wraplength=650)
            action_label.pack(anchor="w", pady=3)
        
        # Options
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=tk.X, pady=10)
        
        # Option to remove data files
        self.remove_data_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Remove all data and report files", 
                       variable=self.remove_data_var).pack(anchor="w", pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(main_frame, orient="horizontal", 
                                       length=650, mode="determinate", 
                                       variable=self.progress_var)
        self.progress.pack(pady=20)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to uninstall")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(pady=5)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        # Uninstall button
        self.uninstall_button = ttk.Button(buttons_frame, text="Uninstall", 
                                        command=self.start_uninstallation, width=15)
        self.uninstall_button.pack(side=tk.LEFT, padx=5)
        
        # Cancel button
        self.cancel_button = ttk.Button(buttons_frame, text="Cancel", 
                                       command=self.root.destroy, width=15)
        self.cancel_button.pack(side=tk.RIGHT, padx=5)
    
    def start_uninstallation(self):
        """Start the uninstallation process"""
        result = messagebox.askokcancel(
            "Confirm Uninstallation",
            "This will uninstall the AIS Shipping Fraud Detection System. Do you want to continue?"
        )
        
        if result:
            self.uninstall_button.config(state="disabled")
            self.cancel_button.config(state="disabled")
            self.progress_var.set(0)
            self.perform_uninstallation()
    
    def update_progress(self, value, status):
        """Update the progress bar and status label"""
        self.progress_var.set(value)
        self.status_var.set(status)
        self.root.update()
    
    def perform_uninstallation(self):
        """Perform the actual uninstallation steps"""
        try:
            # Step 1: Remove desktop shortcuts
            self.update_progress(20, "Removing desktop shortcuts...")
            self.remove_shortcuts()
            
            # Step 2: Remove batch files
            self.update_progress(40, "Removing batch files...")
            self.remove_batch_files()
            
            # Step 3: Remove configuration files
            self.update_progress(60, "Removing configuration files...")
            self.remove_config_files()
            
            # Step 4: Optionally remove data files
            if self.remove_data_var.get():
                self.update_progress(80, "Removing data and report files...")
                self.remove_data_files()
            
            # Step 5: Finalize uninstallation
            self.update_progress(100, "Uninstallation complete!")
            messagebox.showinfo(
                "Uninstallation Complete",
                "The AIS Shipping Fraud Detection System has been successfully uninstalled."
            )
            
            # Re-enable buttons
            self.uninstall_button.config(state="normal")
            self.cancel_button.config(state="normal")
            self.cancel_button.config(text="Close")
            
        except Exception as e:
            logger.error(f"Error during uninstallation: {str(e)}")
            logger.error(traceback.format_exc())
            messagebox.showerror("Uninstallation Error", f"An error occurred during uninstallation: {str(e)}")
            self.uninstall_button.config(state="normal")
            self.cancel_button.config(state="normal")
    
    def remove_shortcuts(self):
        """Remove desktop shortcuts"""
        try:
            # Get the desktop directory
            desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
            
            # Remove .lnk shortcut
            shortcut_path = os.path.join(desktop_dir, "AIS Shipping Fraud Detection.lnk")
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
                logger.info(f"Removed shortcut: {shortcut_path}")
            
            # Remove .bat shortcut (fallback)
            bat_shortcut = os.path.join(desktop_dir, "AIS Shipping Fraud Detection.bat")
            if os.path.exists(bat_shortcut):
                os.remove(bat_shortcut)
                logger.info(f"Removed batch shortcut: {bat_shortcut}")
        except Exception as e:
            logger.warning(f"Error removing shortcuts: {str(e)}")
    
    def remove_batch_files(self):
        """Remove batch files created during installation"""
        try:
            # Get the script directory, handling PyInstaller frozen state
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                # Running as compiled executable
                script_dir = os.path.dirname(sys.executable)
            else:
                # Running as a script
                script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Remove the batch file
            batch_path = os.path.join(script_dir, "Shipping Fraud Detection.bat")
            if os.path.exists(batch_path):
                os.remove(batch_path)
                logger.info(f"Removed batch file: {batch_path}")
        except Exception as e:
            logger.warning(f"Error removing batch files: {str(e)}")
    
    def remove_config_files(self):
        """Remove configuration files"""
        try:
            # Get the script directory, handling PyInstaller frozen state
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                # Running as compiled executable
                script_dir = os.path.dirname(sys.executable)
            else:
                # Running as a script
                script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Remove config.ini
            config_path = os.path.join(script_dir, "config.ini")
            if os.path.exists(config_path):
                os.remove(config_path)
                logger.info(f"Removed config file: {config_path}")
        except Exception as e:
            logger.warning(f"Error removing configuration files: {str(e)}")
    
    def remove_data_files(self):
        """Remove data and report files"""
        try:
            # Get user's home directory
            home_dir = os.path.expanduser("~")
            
            # Remove AIS_Data directory and all its contents
            ais_data_dir = os.path.join(home_dir, "AIS_Data")
            if os.path.exists(ais_data_dir):
                shutil.rmtree(ais_data_dir)
                logger.info(f"Removed data directory: {ais_data_dir}")
        except Exception as e:
            logger.warning(f"Error removing data files: {str(e)}")


if __name__ == "__main__":
    try:
        # Log execution environment
        logger.info("Starting AIS Shipping Fraud Detection System Uninstaller")
        logger.info(f"Python executable: {sys.executable}")
        logger.info(f"Running in frozen state: {getattr(sys, 'frozen', False)}")
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            logger.info(f"MEIPASS: {sys._MEIPASS}")
            logger.info(f"Executable directory: {os.path.dirname(sys.executable)}")
        
        root = tk.Tk()
        app = UninstallerGUI(root)
        root.mainloop()
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}")
        logger.critical(traceback.format_exc())
        # Try to show error message even if GUI fails
        try:
            import tkinter.messagebox
            tkinter.messagebox.showerror("Critical Error", 
                                      f"An unhandled error occurred: {str(e)}\n\n"
                                      f"Please check the log file: uninstall.log")
        except:
            print(f"CRITICAL ERROR: {str(e)}")
            print("See uninstall.log for details.")

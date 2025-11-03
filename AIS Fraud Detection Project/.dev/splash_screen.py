#!/usr/bin/env python3
"""
Splash screen module for AIS Fraud Detection Project
Shows a loading image with progress bar during application startup
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import os
import sys
from PIL import Image, ImageTk

class SplashScreen(tk.Tk):
    """Loading splash screen with progress bar"""
    
    def __init__(self, image_path=None, main_app=None):
        """
        Initialize splash screen
        
        Args:
            image_path (str): Path to the image file to display
            main_app (callable): Function to call to initialize the main application
        """
        super().__init__()
        
        # Remove window decorations and keep on top
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        
        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Set splash window dimensions
        self.width = 600
        self.height = 400
        
        # Center on screen
        x = (screen_width - self.width) // 2
        y = (screen_height - self.height) // 2
        self.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
        # Main frame
        self.main_frame = tk.Frame(self, bg="white")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Load and display the image
        if image_path and os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                # Resize to fit the window while maintaining aspect ratio
                img_width, img_height = img.size
                ratio = min(self.width / img_width, (self.height - 30) / img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)
                img = img.resize((new_width, new_height), Image.ANTIALIAS)
                
                self.photo = ImageTk.PhotoImage(img)
                self.image_label = tk.Label(self.main_frame, image=self.photo, bg="white")
                self.image_label.pack(pady=(20, 0))
            except Exception as e:
                print(f"Error loading image: {e}")
                self.image_label = tk.Label(self.main_frame, text="Loading...", font=("Arial", 24), bg="white")
                self.image_label.pack(pady=(100, 0))
        else:
            self.image_label = tk.Label(self.main_frame, text="Loading...", font=("Arial", 24), bg="white")
            self.image_label.pack(pady=(100, 0))
        
        # Progress bar at the bottom
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.main_frame, 
            orient="horizontal",
            length=self.width - 40,
            mode="determinate",
            variable=self.progress_var
        )
        self.progress_bar.pack(side=tk.BOTTOM, pady=20)
        
        # Status label
        self.status_var = tk.StringVar(value="Starting application...")
        self.status_label = tk.Label(
            self.main_frame,
            textvariable=self.status_var,
            font=("Arial", 10),
            bg="white"
        )
        self.status_label.pack(side=tk.BOTTOM)
        
        self.main_app = main_app
        self.app_loaded = False
        
    def start_progress(self):
        """Start the progress simulation and loading of main application"""
        # Start the main application in a separate thread
        if self.main_app:
            threading.Thread(target=self._load_main_app, daemon=True).start()
        
        # Simulate progress
        threading.Thread(target=self._simulate_progress, daemon=True).start()
    
    def _simulate_progress(self):
        """Simulate progress from 0-90% (the remaining 10% will be when app is actually ready)"""
        for i in range(91):
            if self.app_loaded:  # If app is loaded early, jump to 100%
                break
                
            time.sleep(0.4)  # Adjust timing to match actual loading time (about 40 seconds total)
            self.progress_var.set(i)
            
            # Update status messages at certain points
            if i == 10:
                self.status_var.set("Loading libraries...")
            elif i == 30:
                self.status_var.set("Initializing application...")
            elif i == 50:
                self.status_var.set("Setting up user interface...")
            elif i == 70:
                self.status_var.set("Preparing data structures...")
            
            # Process events to update the UI
            self.update()
            
        # Wait for app to finish loading if it hasn't yet
        while not self.app_loaded:
            time.sleep(0.1)
            self.update()
            
        # Finish progress to 100%
        self.progress_var.set(100)
        self.status_var.set("Ready!")
        self.update()
        
        # Close splash after a short delay
        self.after(500, self.destroy)
            
    def _load_main_app(self):
        """Load the main application"""
        if callable(self.main_app):
            # Import and prepare the main app
            self.main_app()
            
            # Mark app as loaded
            self.app_loaded = True

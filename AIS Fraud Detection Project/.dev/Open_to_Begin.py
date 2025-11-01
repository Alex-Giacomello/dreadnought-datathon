#!/usr/bin/env python3
"""
AIS Shipping Fraud Detection System - Setup and Installer
--------------------------------------------------------

This script provides a unified interface for setting up the AIS Shipping Fraud Detection System.
It checks for required dependencies and offers to install them if missing.

Main functions:
- Verify Python and pip installation
- Install Python via Python Install Manager if needed
- Build the application executable
- Build installer and uninstaller
- Provide comprehensive setup guidance
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import platform
from pathlib import Path
import webbrowser
import threading

class SetupGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AIS Shipping Fraud Detection System - Setup")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # Set style
        style = ttk.Style()
        style.configure('TButton', font=('Arial', 11))
        style.configure('TLabel', font=('Arial', 11))
        style.configure('Header.TLabel', font=('Arial', 16, 'bold'))
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = ttk.Label(main_frame, text="AIS Shipping Fraud Detection System Setup", 
                          style='Header.TLabel')
        header.pack(pady=10)
        
        # Version info
        version_info = ttk.Label(main_frame, text="Version 1.0.0")
        version_info.pack()
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="System Status", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=False, pady=10)
        
        # Status grid
        status_grid = ttk.Frame(status_frame)
        status_grid.pack(fill=tk.BOTH, expand=True)
        
        # Python status
        ttk.Label(status_grid, text="Python:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.python_status = ttk.Label(status_grid, text="Checking Python installation...")
        self.python_status.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # Pip status
        ttk.Label(status_grid, text="pip:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.pip_status = ttk.Label(status_grid, text="Checking pip installation...")
        self.pip_status.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        # Dependencies status
        ttk.Label(status_grid, text="Packages:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.deps_status = ttk.Label(status_grid, text="Required packages: Not checked")
        self.deps_status.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        # System info
        if platform.system() == "Windows":
            ttk.Label(status_grid, text="Windows:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
            windows_ver = platform.win32_ver()[0]
            self.windows_status = ttk.Label(status_grid, text=f"Windows {windows_ver}")
            self.windows_status.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        
        # Actions frame
        actions_frame = ttk.LabelFrame(main_frame, text="Available Actions", padding="10")
        actions_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Instruction text
        instruction_label = ttk.Label(actions_frame, text="Choose an action to begin setup:", 
                                    font=('Arial', 11))
        instruction_label.pack(anchor="w", pady=5)
        
        # Actions grid for better layout
        actions_grid = ttk.Frame(actions_frame)
        actions_grid.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Build application button
        self.build_app_btn = ttk.Button(actions_grid, text="1. Build Application", 
                                      command=self.build_application, width=30)
        self.build_app_btn.grid(row=0, column=0, sticky="w", pady=8, padx=10)
        
        build_app_desc = ttk.Label(actions_grid, text="Creates a standalone executable for the program")
        build_app_desc.grid(row=0, column=1, sticky="w", pady=8, padx=10)
        
        # Build installer button
        self.build_installer_btn = ttk.Button(actions_grid, text="2. Build Installer", 
                                            command=self.build_installer, width=30)
        self.build_installer_btn.grid(row=1, column=0, sticky="w", pady=8, padx=10)
        
        build_installer_desc = ttk.Label(actions_grid, text="Creates an installer executable")
        build_installer_desc.grid(row=1, column=1, sticky="w", pady=8, padx=10)
        
        # Build uninstaller button
        self.build_uninstaller_btn = ttk.Button(actions_grid, text="3. Build Uninstaller", 
                                              command=self.build_uninstaller, width=30)
        self.build_uninstaller_btn.grid(row=2, column=0, sticky="w", pady=8, padx=10)
        
        build_uninstaller_desc = ttk.Label(actions_grid, text="Creates an uninstaller executable")
        build_uninstaller_desc.grid(row=2, column=1, sticky="w", pady=8, padx=10)
        
        # Build all button
        self.build_all_btn = ttk.Button(actions_grid, text="4. Build All Components", 
                                      command=self.build_all, width=30)
        self.build_all_btn.grid(row=3, column=0, sticky="w", pady=8, padx=10)
        
        build_all_desc = ttk.Label(actions_grid, text="Builds all components at once")
        build_all_desc.grid(row=3, column=1, sticky="w", pady=8, padx=10)
        
        # Open README button
        self.open_readme_btn = ttk.Button(actions_grid, text="5. Open Documentation", 
                                        command=self.open_readme, width=30)
        self.open_readme_btn.grid(row=4, column=0, sticky="w", pady=8, padx=10)
        
        open_readme_desc = ttk.Label(actions_grid, text="Opens the comprehensive documentation")
        open_readme_desc.grid(row=4, column=1, sticky="w", pady=8, padx=10)
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.pack(fill=tk.X, expand=False, pady=10)
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(progress_frame, orient="horizontal", 
                                      length=660, mode="determinate", 
                                      variable=self.progress_var)
        self.progress.pack(pady=5, fill=tk.X)
        
        # Status message
        status_frame = ttk.Frame(progress_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, font=('Arial', 10, 'bold'))
        status_label.pack(side=tk.LEFT, padx=5)
        
        # Footer with help button
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill=tk.X, pady=10)
        
        help_button = ttk.Button(footer_frame, text="Help", 
                               command=lambda: messagebox.showinfo("Help", "For assistance, refer to the documentation or contact system administrator."))
        help_button.pack(side=tk.RIGHT, padx=5)
        
        # Check Python installation on startup
        self.root.after(100, self.check_system_dependencies)
    
    def check_system_dependencies(self):
        """Check if Python and pip are installed"""
        self.update_status("Checking system dependencies...", 10)
        
        # Check Python
        try:
            python_version = platform.python_version()
            self.python_status.config(text=f"Python {python_version} installed ✓")
            python_installed = True
        except:
            self.python_status.config(text="Python not detected ✗")
            python_installed = False
        
        # Check pip
        if python_installed:
            try:
                pip_result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                          text=True, check=False)
                if pip_result.returncode == 0:
                    pip_version = pip_result.stdout.split()[1]
                    self.pip_status.config(text=f"pip {pip_version} installed ✓")
                    pip_installed = True
                else:
                    self.pip_status.config(text="pip not installed ✗")
                    pip_installed = False
            except:
                self.pip_status.config(text="pip not installed ✗")
                pip_installed = False
        else:
            self.pip_status.config(text="pip check skipped (Python not found) ✗")
            pip_installed = False
        
        # Check if Python Install Manager is needed
        if not python_installed or not pip_installed:
            self.deps_status.config(text="Python environment incomplete. Installation required.")
            
            # Ask user if they want to install Python
            if messagebox.askyesno("Python Installation Required", 
                                  "Python or pip is not installed correctly. Would you like to use "
                                  "the Python Install Manager to install the correct version?"):
                self.install_python()
            else:
                messagebox.showwarning("Manual Installation Required", 
                                      "You will need to install Python and pip manually before proceeding.")
        else:
            self.update_status("Checking required packages...", 20)
            self.deps_status.config(text="Python environment is ready")
            self.update_status("Ready", 0)
    
    def install_python(self):
        """Install Python using the Python Install Manager"""
        self.update_status("Installing Python Install Manager...", 30)
        
        try:
            # Show message to user
            messagebox.showinfo("Python Install Manager", 
                              "Python Install Manager will be installed. After installation, "
                              "please use it to install Python, then restart this setup tool.")
                              
            # Use threading to prevent UI freeze during installation
            install_thread = threading.Thread(target=self._run_python_install_manager)
            install_thread.daemon = True
            install_thread.start()
        except Exception as e:
            self.update_status("Failed to install Python Install Manager.", 0)
            messagebox.showerror("Installation Error", 
                               f"Failed to install Python Install Manager. Check that 'winget install 9NQ7512CXL7T' version is correct.\nError: {str(e)}")
    
    def _run_python_install_manager(self):
        """Run the Python Install Manager installation in a separate thread"""
        try:
            # Run winget to install Python Install Manager
            self.update_status("Running winget to install Python Install Manager...", 40)
            
            # Accept source and package agreements  If the version ("9NQ7512CXL7T") is not correct go to the official python webpage to update it.
            cmd = ["winget", "install", "9NQ7512CXL7T", "--accept-source-agreements", "--accept-package-agreements"]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
            stdout, stderr = process.communicate()
            
            # Update UI on the main thread
            self.root.after(0, self._handle_install_result, process.returncode, stdout, stderr)
        except Exception as e:
            # Update UI on the main thread
            self.root.after(0, self._handle_install_exception, str(e))
    
    def _handle_install_result(self, returncode, stdout, stderr):
        """Handle the result of the Python Install Manager installation"""
        if returncode == 0:
            self.update_status("Python Install Manager installed successfully.", 50)
            messagebox.showinfo("Installation Complete", 
                              "Python Install Manager has been installed. Please use it to install "
                              "Python 3.9 or higher, then restart this setup tool.")
        else:
            self.update_status("Failed to install Python Install Manager.", 0)
            messagebox.showerror("Installation Error", 
                               f"Failed to install Python Install Manager. Check that 'winget install 9NQ7512CXL7' version is correct.\nError: {stderr}")
    
    def _handle_install_exception(self, error_msg):
        """Handle exceptions during installation"""
        self.update_status("Failed to install Python Install Manager.", 0)
        messagebox.showerror("Installation Error", 
                           f"Failed to install Python Install Manager. Check that 'winget install 9NQ7512CXL7' version is correct.\nError: {error_msg}")
    
    def update_status(self, message, progress):
        """Update the status message and progress bar"""
        self.status_var.set(message)
        self.progress_var.set(progress)
        self.root.update()
    
    def build_application(self):
        """Build the standalone application executable"""
        self.update_status("Building application...", 10)
        self._run_build_script("build_exe.bat", "application")
    
    def build_installer(self):
        """Build the installer executable"""
        self.update_status("Building installer...", 10)
        self._run_build_script("build_installer.bat", "installer")
    
    def build_uninstaller(self):
        """Build the uninstaller executable"""
        self.update_status("Building uninstaller...", 10)
        self._run_build_script("build_uninstaller.bat", "uninstaller")
    
    def build_all(self):
        """Build all components"""
        self.update_status("Building all components...", 10)
        self._run_build_script("build_all.bat", "all components")
    
    def _run_build_script(self, script_name, component_name):
        """Run a build script"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, script_name)
        
        if os.path.exists(script_path):
            try:
                self.update_status(f"Preparing to build {component_name}...", 20)
                
                # Disable buttons while building
                self.build_app_btn.config(state='disabled')
                self.build_installer_btn.config(state='disabled')
                self.build_uninstaller_btn.config(state='disabled')
                self.build_all_btn.config(state='disabled')
                
                # Start the build process in a separate thread
                build_thread = threading.Thread(
                    target=self._execute_build_script,
                    args=(script_path, script_dir, component_name)
                )
                build_thread.daemon = True
                build_thread.start()
                
                # Show information to user
                messagebox.showinfo(f"Building {component_name.capitalize()}", 
                                  f"The build process for {component_name} has been started.\n\n"
                                  f"A command window will open to show the progress.")
            except Exception as e:
                self.update_status(f"Failed to run {script_name}", 0)
                messagebox.showerror("Build Error", f"Failed to run build script.\nError: {str(e)}")
                self._enable_buttons()
        else:
            self.update_status(f"Build script {script_name} not found", 0)
            messagebox.showerror("Build Error", f"Build script {script_name} not found.")
            self._enable_buttons()
    
    def _execute_build_script(self, script_path, script_dir, component_name):
        """Execute the build script in a separate thread"""
        try:
            self.update_status(f"Building {component_name}...", 50)
            process = subprocess.Popen(script_path, shell=True, cwd=script_dir)
            process.communicate()  # Wait for process to complete
            
            # Update UI on the main thread
            self.root.after(0, self._handle_build_completion, process.returncode, component_name)
        except Exception as e:
            # Update UI on the main thread
            self.root.after(0, self._handle_build_exception, str(e), component_name)
    
    def _handle_build_completion(self, returncode, component_name):
        """Handle build process completion"""
        if returncode == 0:
            self.update_status(f"{component_name.capitalize()} built successfully", 100)
            messagebox.showinfo("Build Complete", 
                              f"{component_name.capitalize()} has been built successfully.\n\n"
                              f"You can find the output in the 'dist' folder.")
        else:
            self.update_status(f"Error building {component_name}", 0)
            messagebox.showerror("Build Error", 
                               f"Failed to build {component_name}. Check the command window for details.")
        
        # Re-enable buttons
        self._enable_buttons()
    
    def _handle_build_exception(self, error_msg, component_name):
        """Handle exceptions during build process"""
        self.update_status(f"Error building {component_name}", 0)
        messagebox.showerror("Build Error", 
                           f"Failed to build {component_name}.\nError: {error_msg}")
        
        # Re-enable buttons
        self._enable_buttons()
    
    def _enable_buttons(self):
        """Re-enable all build buttons"""
        self.build_app_btn.config(state='normal')
        self.build_installer_btn.config(state='normal')
        self.build_uninstaller_btn.config(state='normal')
        self.build_all_btn.config(state='normal')
    
    def open_readme(self):
        """Open the README file"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        readme_path = os.path.join(script_dir, "READ_ME_FIRST.md")
        
        if os.path.exists(readme_path):
            os.startfile(readme_path)
        else:
            messagebox.showerror("Error", "README file not found.")


if __name__ == "__main__":
    root = tk.Tk()
    app = SetupGUI(root)
    root.mainloop()

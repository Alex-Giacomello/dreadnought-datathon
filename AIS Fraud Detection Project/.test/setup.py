#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script to create a Windows executable for the Shipping Fraud Detection GUI
"""

import sys
import os
from setuptools import setup

APP_NAME = "Shipping Fraud Detection"
APP_SCRIPT = "AnomalyDetectGUI_new.py"

# Additional files to include
data_files = [
    ('', ['shipping_fraud_detection.py', 'config.ini']),
]

setup(
    name=APP_NAME,
    version="1.0.0",
    description="AIS Shipping Fraud Detection System",
    author="Team Dreadnaught-Datathon 2025",
    options={
        'build_exe': {
            'includes': ['tkinter'],
            'include_files': ['shipping_fraud_detection.py', 'config.ini'],
            'packages': ['numpy', 'pandas', 'dask', 'folium', 'matplotlib', 'seaborn', 'geopy'],
        },
    },
    executables=[
        {
            'script': APP_SCRIPT,
            'base': 'Win32GUI',
            'target_name': APP_NAME,
            'icon': None,  # Add an icon file path here if you have one
        }
    ],
)

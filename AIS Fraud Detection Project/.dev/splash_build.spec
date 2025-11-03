# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for AIS Fraud Detection System with splash screen
"""

import os
import sys
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Get the directory of this spec file
spec_dir = os.path.dirname(os.path.abspath(SPECPATH))

# Define data files to include
datas = [
    (os.path.join(spec_dir, 'SFDLoad.png'), '.'),
    (os.path.join(spec_dir, '1. README.md'), '.'),
    (os.path.join(spec_dir, 'config.ini'), '.'),
]

# Create a list of hidden imports that might be needed
hidden_imports = [
    'PIL.Image', 
    'PIL.ImageTk',
    'tkcalendar',
    'boto3',
    'botocore',
    'markdown',
    'tkhtmlview',
    'pandas',
]

# Main executable that shows splash screen then loads the app
a = Analysis(
    [os.path.join(spec_dir, 'launch_with_splash.py')],
    pathex=[spec_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AIS_Fraud_Detection',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(spec_dir, 'app_icon.ico') if os.path.exists(os.path.join(spec_dir, 'app_icon.ico')) else None,
)

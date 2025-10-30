@echo off
echo Building Shipping Fraud Detection executable...

REM Install required packages if not already installed
pip install pyinstaller pandas numpy dask folium matplotlib seaborn geopy

REM Create the executable
pyinstaller --name="Shipping Fraud Detection" --windowed --onefile --icon=SFD.ico ^
  --add-data="shipping_fraud_detection.py;." ^
  --add-data="config.ini;." ^
  --hidden-import=pandas ^
  --hidden-import=numpy ^
  --hidden-import=dask ^
  --hidden-import=folium ^
  --hidden-import=matplotlib ^
  --hidden-import=seaborn ^
  --hidden-import=geopy ^
  AnomalyDetectGUI_new.py

echo.
echo Build complete. The executable is located in the dist folder.
echo.
pause
# S3 Integration Quick Start Guide

## Setting Up S3 Integration (5 minutes)

1. **Install required package:**
   ```
   python -m pip install boto3
   ```

2. **Configure AWS credentials:**
   ```
   python aws_config_helper.py
   ```
   Select option 1 and enter your AWS Access Key ID and Secret Key when prompted.

3. **Test your connection:**
   ```
   python test_s3_connectivity_enhanced.py
   ```

4. **Update configuration:**
   - Either use the GUI application (Advanced tab → AWS S3 Settings)
   - Or run: `python aws_config_helper.py` and select option 3

## Using S3 in the AIS Fraud Detection System

### Option 1: Using the GUI

1. Launch the AnomalyDetectGUI_new.py application
2. Go to the "Advanced" tab
3. Check "Use AWS S3 for data storage" 
4. Enter S3 URI: `s3://ai-dsde-txg-datathon2025/teams/dreadnought/parquet/`
5. Click "Test S3 Connection" to verify
6. Click "Run Analysis" to analyze data from S3

### Option 2: Command Line

Run the analysis directly from the command line:
```
python shipping_fraud_detection.py --config config.ini --s3-uri s3://ai-dsde-txg-datathon2025/teams/dreadnought/parquet/
```

## Expected Data Format in S3

Files in S3 should follow one of these formats:
- `2024-10-01.csv` or `ais-2024-10-01.csv`
- `2024-10-01.parquet` or `ais-2024-10-01.parquet`

## Verifying Data in S3

To verify what data is available in the S3 bucket:
```
python test_s3_connectivity_enhanced.py --s3-uri s3://ai-dsde-txg-datathon2025/teams/dreadnought/parquet/
```

This will list the first 10 files in the bucket and show how many CSV and Parquet files were found.

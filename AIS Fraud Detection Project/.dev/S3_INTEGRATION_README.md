# AWS S3 Integration for AIS Fraud Detection

This document explains how to use the Amazon S3 integration with the AIS Shipping Fraud Detection System.

## Overview

The AIS Fraud Detection System now supports retrieving AIS shipping data directly from Amazon S3 storage buckets. This integration allows you to:

- Store and access large AIS datasets in the cloud
- Use the same analysis tools on both local and cloud-stored data
- Share datasets more easily with team members

## Requirements

- AWS account with access to the S3 bucket containing AIS data
- AWS credentials (Access Key ID and Secret Access Key) with permissions to read from the S3 bucket
- Python 3.7+ with boto3 library installed

## Installation

1. Install the required AWS SDK for Python:
   ```
   pip install boto3
   ```

2. Configure your AWS credentials using one of these methods:

   a) Use the AWS CLI:
   ```
   aws configure
   ```
   
   b) Set environment variables:
   ```
   set AWS_ACCESS_KEY_ID=your_access_key
   set AWS_SECRET_ACCESS_KEY=your_secret_key
   set AWS_DEFAULT_REGION=your_region
   ```
   
   c) Use the `aws_config_helper.py` tool included in this package:
   ```
   python aws_config_helper.py
   ```

## Configuration

You can enable S3 integration by:

1. Using the GUI application:
   - Go to the "Advanced" tab
   - Check "Use AWS S3 for data storage"
   - Enter the S3 URI in the format: `s3://bucket-name/path/to/data/`
   - Click "Test S3 Connection" to verify access
   - Click "Save Configuration" to save these settings

2. Editing the config.ini file:
   - Add or modify the S3_SETTINGS section:
   ```ini
   [S3_SETTINGS]
   use_s3 = True
   s3_data_uri = s3://ai-dsde-txg-datathon2025/teams/dreadnought/parquet/
   ```

3. Using command line options:
   ```
   python shipping_fraud_detection.py --s3-uri s3://ai-dsde-txg-datathon2025/teams/dreadnought/parquet/
   ```

## Data Format

The S3 bucket should contain AIS data files in one of these formats:

1. CSV files with filenames in the format:
   - `YYYY-MM-DD.csv` (e.g., `2024-10-01.csv`)
   - `ais-YYYY-MM-DD.csv` (e.g., `ais-2024-10-01.csv`)

2. Parquet files with filenames in the format:
   - `YYYY-MM-DD.parquet` (e.g., `2024-10-01.parquet`)
   - `ais-YYYY-MM-DD.parquet` (e.g., `ais-2024-10-01.parquet`)

## Testing S3 Connectivity

You can test your S3 connectivity using the included test scripts:

1. Basic connectivity test:
   ```
   python test_s3_connectivity.py
   ```

2. Enhanced connectivity test with detailed reporting:
   ```
   python test_s3_connectivity_enhanced.py
   ```

## Troubleshooting

### Common Issues:

1. **No credentials found**
   - Configure AWS credentials using one of the methods described above
   - Verify your credentials with: `aws s3 ls`

2. **Access denied**
   - Check that your AWS user has the necessary S3 permissions
   - Verify the bucket name and path are correct
   - Ensure the bucket policy allows your user to list objects

3. **No files found**
   - Verify the S3 URI path is correct
   - Check that files follow the expected naming conventions
   - Ensure files have the correct extensions (.csv or .parquet)

### Getting Help

For further assistance:
1. Check AWS documentation: https://docs.aws.amazon.com/s3/
2. Contact your AWS administrator
3. Refer to the boto3 documentation: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html

## Security Considerations

- Never hardcode AWS credentials in your code
- Use IAM roles with least privilege when possible
- Consider using temporary credentials for enhanced security
- Regularly rotate your AWS access keys

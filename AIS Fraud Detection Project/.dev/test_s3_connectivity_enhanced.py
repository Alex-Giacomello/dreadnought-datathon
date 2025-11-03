#!/usr/bin/env python3
"""
Enhanced S3 Connectivity Test Script for AIS Shipping Fraud Detection

This script tests connectivity to an AWS S3 bucket and lists available AIS data files.
It will also check AWS credentials and region configuration.
"""

import boto3
import botocore.exceptions
import os
import sys
import logging
import argparse
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("s3_connectivity_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_aws_credentials():
    """Check if AWS credentials are configured properly"""
    try:
        # Get current AWS session
        session = boto3.session.Session()
        credentials = session.get_credentials()
        
        if credentials is None:
            logger.warning("No AWS credentials found. Please configure your credentials with AWS CLI or set environment variables.")
            return False
            
        # Check if credentials are set
        access_key = credentials.access_key
        secret_key = credentials.secret_key
        
        if not access_key or not secret_key:
            logger.warning("AWS credentials are incomplete. Please check your configuration.")
            return False
            
        # Get region
        region = session.region_name
        if not region:
            logger.warning("AWS region not set. Using default 'us-east-1'.")
            region = "us-east-1"
            
        logger.info(f"AWS credentials found with region: {region}")
        logger.info(f"Access key ID: {access_key[:4]}...{access_key[-4:] if len(access_key) > 8 else ''}")
        return True
        
    except botocore.exceptions.BotoCoreError as e:
        logger.error(f"Error checking AWS credentials: {e}")
        return False

def test_s3_connectivity(s3_uri):
    """
    Test connectivity to an S3 bucket using the provided URI
    
    Args:
        s3_uri (str): S3 URI in the format 's3://bucket-name/prefix/'
        
    Returns:
        bool: True if connection is successful
    """
    try:
        if not s3_uri.startswith('s3://'):
            logger.error(f"Invalid S3 URI format. Expected 's3://bucket/path/', got '{s3_uri}'")
            return False
            
        # Parse the URI
        parts = s3_uri[5:].split('/', 1)  # Skip 's3://' and split on first '/'
        bucket_name = parts[0]
        prefix = parts[1] if len(parts) > 1 else ""
        
        logger.info(f"Testing connection to bucket: {bucket_name}, prefix: {prefix}")
        
        # Create S3 client
        s3 = boto3.client('s3')
        
        # Test bucket existence
        try:
            s3.head_bucket(Bucket=bucket_name)
            logger.info(f"Successfully connected to bucket: {bucket_name}")
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == '404':
                logger.error(f"Bucket {bucket_name} does not exist")
            elif error_code == '403':
                logger.error(f"Access denied to bucket {bucket_name}. Check permissions.")
            else:
                logger.error(f"Error accessing bucket {bucket_name}: {e}")
            return False
            
        # List objects with the given prefix
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        
        # Check if any objects were found
        if 'Contents' in response:
            object_count = len(response['Contents'])
            logger.info(f"Found {object_count} objects in {s3_uri}")
            
            # List some of the objects
            max_display = 10
            logger.info(f"First {min(max_display, object_count)} objects:")
            for i, obj in enumerate(response['Contents'][:max_display]):
                key = obj['Key']
                size = obj['Size']
                logger.info(f"{i+1}. {key} ({size} bytes)")
                
            # Check for AIS data files
            csv_count = len([obj for obj in response['Contents'] if obj['Key'].endswith('.csv')])
            parquet_count = len([obj for obj in response['Contents'] if obj['Key'].endswith('.parquet')])
            
            logger.info(f"Found {csv_count} CSV files and {parquet_count} Parquet files in the bucket")
            
            if csv_count == 0 and parquet_count == 0:
                logger.warning("No AIS data files (CSV or Parquet) found in the specified location")
            
            return True
        else:
            logger.warning(f"No objects found in {s3_uri}")
            return True  # Still return True as connection was successful
            
    except botocore.exceptions.NoCredentialsError:
        logger.error("AWS credentials not found. Use AWS CLI to configure your credentials.")
        return False
    except botocore.exceptions.EndpointConnectionError:
        logger.error("Could not connect to AWS. Check your internet connection.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False

def test_s3_connectivity_with_profile(s3_uri, profile_name):
    """
    Test connectivity to an S3 bucket using the provided URI and AWS profile
    
    Args:
        s3_uri (str): S3 URI in the format 's3://bucket-name/prefix/'
        profile_name (str): AWS profile name to use
        
    Returns:
        bool: True if connection is successful
    """
    try:
        if not s3_uri.startswith('s3://'):
            logger.error(f"Invalid S3 URI format. Expected 's3://bucket/path/', got '{s3_uri}'")
            return False
            
        # Parse the URI
        parts = s3_uri[5:].split('/', 1)  # Skip 's3://' and split on first '/'
        bucket_name = parts[0]
        prefix = parts[1] if len(parts) > 1 else ""
        
        logger.info(f"Testing connection to bucket: {bucket_name}, prefix: {prefix} using profile: {profile_name}")
        
        # Create a session with the specified profile
        session = boto3.Session(profile_name=profile_name)
        s3 = session.client('s3')
        
        # Test bucket existence
        try:
            s3.head_bucket(Bucket=bucket_name)
            logger.info(f"Successfully connected to bucket: {bucket_name}")
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == '404':
                logger.error(f"Bucket {bucket_name} does not exist")
            elif error_code == '403':
                logger.error(f"Access denied to bucket {bucket_name}. Check permissions.")
            else:
                logger.error(f"Error accessing bucket {bucket_name}: {e}")
            return False
            
        # List objects with the given prefix
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        
        # Check if any objects were found
        if 'Contents' in response:
            object_count = len(response['Contents'])
            logger.info(f"Found {object_count} objects in {s3_uri}")
            
            # List some of the objects
            max_display = 10
            logger.info(f"First {min(max_display, object_count)} objects:")
            for i, obj in enumerate(response['Contents'][:max_display]):
                key = obj['Key']
                size = obj['Size']
                logger.info(f"{i+1}. {key} ({size} bytes)")
                
            # Check for AIS data files
            csv_count = len([obj for obj in response['Contents'] if obj['Key'].endswith('.csv')])
            parquet_count = len([obj for obj in response['Contents'] if obj['Key'].endswith('.parquet')])
            
            logger.info(f"Found {csv_count} CSV files and {parquet_count} Parquet files in the bucket")
            
            if csv_count == 0 and parquet_count == 0:
                logger.warning("No AIS data files (CSV or Parquet) found in the specified location")
            
            return True
        else:
            logger.warning(f"No objects found in {s3_uri}")
            return True  # Still return True as connection was successful
            
    except botocore.exceptions.NoCredentialsError:
        logger.error("AWS credentials not found for profile. Use AWS CLI to configure your credentials.")
        return False
    except botocore.exceptions.ProfileNotFound:
        logger.error(f"AWS profile '{profile_name}' not found. Please check your AWS configuration.")
        return False
    except botocore.exceptions.EndpointConnectionError:
        logger.error("Could not connect to AWS. Check your internet connection.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False

def check_aws_profiles():
    """Check available AWS profiles"""
    try:
        session = boto3.Session()
        profiles = session.available_profiles
        
        if not profiles:
            logger.warning("No AWS profiles found")
            return []
            
        logger.info(f"Found {len(profiles)} AWS profiles: {', '.join(profiles)}")
        return profiles
    except Exception as e:
        logger.error(f"Error checking AWS profiles: {e}")
        return []

def main():
    """Main function to test S3 connectivity"""
    parser = argparse.ArgumentParser(description='Test AWS S3 connectivity for AIS Shipping Fraud Detection')
    parser.add_argument('--s3-uri', type=str, default='s3://ai-dsde-txg-datathon2025/teams/dreadnought/parquet/',
                        help='S3 URI to test (default: s3://ai-dsde-txg-datathon2025/teams/dreadnought/parquet/)')
    parser.add_argument('--profile', type=str, help='AWS profile to use')
    args = parser.parse_args()
    
    logger.info("Starting S3 connectivity test")
    
    # Check for available profiles if using a profile
    if args.profile:
        logger.info(f"Using AWS profile: {args.profile}")
    else:
        # Check available profiles
        profiles = check_aws_profiles()
        if "dreadnought" in profiles:
            logger.info("Found 'dreadnought' profile, recommending its use")
            print("\nFound AWS profile 'dreadnought'. You can use this profile with --profile dreadnought")
    
    # Check AWS credentials first if not using a profile
    if not args.profile and check_aws_credentials():
        logger.info("AWS credentials check passed")
    elif not args.profile:
        logger.warning("AWS credentials check failed. You may need to configure your AWS credentials.")
        print("\nTo configure AWS credentials, use one of the following methods:")
        print("1. Run the SSO setup script: python setup_aws_sso.py")
        print("2. Run 'aws configure' in your terminal")
        print("3. Set environment variables AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        print("4. Run 'python set_temp_credentials.py' to use temporary credentials")
    
    # Test S3 connectivity
    success = False
    if args.profile:
        # Test with the specified profile
        success = test_s3_connectivity_with_profile(args.s3_uri, args.profile)
    else:
        # Test with default credentials
        success = test_s3_connectivity(args.s3_uri)
        
    if success:
        logger.info("S3 connectivity test successful!")
        print("\nS3 connectivity test successful! You can use the S3 integration in the AIS Shipping Fraud Detection system.")
    else:
        logger.error("S3 connectivity test failed!")
        print("\nS3 connectivity test failed. Please check your AWS credentials and permissions.")
        
        # Suggest using the profile if failed with default credentials
        if not args.profile:
            print("\nIf you've set up AWS SSO, try running this command with your profile:")
            print(f"python test_s3_connectivity_enhanced.py --profile dreadnought")
            print("\nOr run 'python setup_aws_sso.py' to set up AWS SSO access.")
            print("\nFor immediate access with temporary credentials, run:")
            print("python set_temp_credentials.py")

if __name__ == "__main__":
    main()

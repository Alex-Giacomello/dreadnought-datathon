#!/usr/bin/env python3
"""
AWS S3 Authentication Utilities for AIS Fraud Detection project

This module provides various authentication methods for AWS S3 access.
"""

import os
import boto3
import botocore.exceptions
import configparser
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_s3_client_with_profile(profile_name):
    """
    Create an S3 client using the specified AWS profile.
    
    Args:
        profile_name (str): Name of the AWS profile to use
        
    Returns:
        boto3.client: An S3 client or None if an error occurs
    """
    try:
        # Create a session with the specified profile
        session = boto3.Session(profile_name=profile_name)
        
        # Create an S3 client from the session
        s3_client = session.client('s3')
        return s3_client
    except botocore.exceptions.ProfileNotFound:
        logger.error(f"AWS profile '{profile_name}' not found. Please check your AWS configuration.")
        return None
    except botocore.exceptions.NoCredentialsError:
        logger.error(f"No credentials found for profile '{profile_name}'")
        return None
    except Exception as e:
        logger.error(f"Error creating S3 client with profile '{profile_name}': {e}")
        return None

def get_s3_client_with_keys(access_key, secret_key, region='us-east-1'):
    """
    Create an S3 client using the provided access and secret keys.
    
    Args:
        access_key (str): AWS access key ID
        secret_key (str): AWS secret access key
        region (str): AWS region name
        
    Returns:
        boto3.client: An S3 client or None if an error occurs
    """
    try:
        # Create a client with the provided keys
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        return s3_client
    except botocore.exceptions.NoCredentialsError:
        logger.error("Invalid access or secret keys provided")
        return None
    except Exception as e:
        logger.error(f"Error creating S3 client with access keys: {e}")
        return None

def get_s3_client_with_role_arn(role_arn, region='us-east-1'):
    """
    Create an S3 client by assuming a specified IAM role.
    
    Args:
        role_arn (str): ARN of the IAM role to assume
        region (str): AWS region name
        
    Returns:
        boto3.client: An S3 client or None if an error occurs
    """
    try:
        # Create an STS client to assume the role
        sts_client = boto3.client('sts', region_name=region)
        
        # Assume the specified role
        assumed_role = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName="S3AccessSession"
        )
        
        # Extract temporary credentials
        credentials = assumed_role['Credentials']
        
        # Create an S3 client with the temporary credentials
        s3_client = boto3.client(
            's3',
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
            region_name=region
        )
        return s3_client
    except botocore.exceptions.ClientError as e:
        logger.error(f"Error assuming role '{role_arn}': {e}")
        return None
    except Exception as e:
        logger.error(f"Error creating S3 client with role ARN: {e}")
        return None

def get_s3_client_default():
    """
    Create an S3 client using the default credential provider chain.
    
    Returns:
        boto3.client: An S3 client or None if an error occurs
    """
    try:
        # Create an S3 client with the default credential provider chain
        s3_client = boto3.client('s3')
        return s3_client
    except botocore.exceptions.NoCredentialsError:
        logger.error("No AWS credentials found in the default credential provider chain")
        return None
    except Exception as e:
        logger.error(f"Error creating S3 client with default credentials: {e}")
        return None

def test_s3_connection(s3_client, bucket_name, prefix=""):
    """
    Test the connection to an S3 bucket.
    
    Args:
        s3_client (boto3.client): S3 client to use
        bucket_name (str): Name of the S3 bucket
        prefix (str): Prefix to list objects under
        
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        if prefix:
            # List objects with the prefix to verify we can access them
            response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix, MaxKeys=1)
            return 'Contents' in response
        else:
            # Just test if we can access the bucket
            s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
            return True
    except s3_client.exceptions.NoSuchBucket:
        logger.error(f"The bucket '{bucket_name}' does not exist or you don't have access to it")
        return False
    except botocore.exceptions.ClientError as e:
        logger.error(f"Failed to access S3: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while testing S3 connection: {e}")
        return False

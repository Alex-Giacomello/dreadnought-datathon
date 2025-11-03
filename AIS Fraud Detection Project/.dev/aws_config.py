import boto3
import configparser
import os
import logging

logger = logging.getLogger(__name__)

def configure_aws_credentials(access_key, secret_key, region='us-east-1'):
    """
    Configure AWS credentials for boto3.
    
    Args:
        access_key (str): AWS Access Key ID
        secret_key (str): AWS Secret Access Key
        region (str): AWS Region (default: us-east-1)
    
    Returns:
        bool: True if credentials were successfully configured
    """
    try:
        # Create a session with the provided credentials
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        # Test the credentials by listing S3 buckets
        s3 = session.client('s3')
        s3.list_buckets()
        
        # Save the credentials to the AWS credentials file
        aws_dir = os.path.expanduser("~/.aws")
        os.makedirs(aws_dir, exist_ok=True)
        
        config_path = os.path.join(aws_dir, "credentials")
        config = configparser.ConfigParser()
        
        # Read existing config if it exists
        if os.path.exists(config_path):
            config.read(config_path)
        
        # Add or update the 'default' profile
        if 'default' not in config:
            config['default'] = {}
        
        config['default']['aws_access_key_id'] = access_key
        config['default']['aws_secret_access_key'] = secret_key
        config['default']['region'] = region
        
        # Write the updated config back to the file
        with open(config_path, 'w') as f:
            config.write(f)
        
        logger.info("AWS credentials successfully configured")
        return True
    
    except Exception as e:
        logger.error(f"Failed to configure AWS credentials: {str(e)}")
        return False

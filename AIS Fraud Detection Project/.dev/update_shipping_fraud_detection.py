#!/usr/bin/env python3
"""
Update script for shipping_fraud_detection.py to add flexible authentication options
"""

import os
import sys
import re

def update_main_function():
    """Add command-line arguments for the new authentication options"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, "shipping_fraud_detection.py")
    
    if not os.path.exists(script_path):
        print(f"Error: Could not find shipping_fraud_detection.py in {script_dir}")
        return False
    
    # Read the file content
    with open(script_path, 'r') as file:
        content = file.read()
    
    # Pattern to match the argument parser section
    pattern = r"(def main\(\):.+?parser\.add_argument\('--profile', type=str, help='AWS profile name to use for S3 access'\))"
    
    # New command-line arguments to add
    new_args = """
    parser.add_argument('--profile', type=str, help='AWS profile name to use for S3 access')
    parser.add_argument('--access-key', type=str, help='AWS access key ID for S3 access')
    parser.add_argument('--secret-key', type=str, help='AWS secret access key for S3 access')
    parser.add_argument('--region', type=str, help='AWS region name', default='us-east-1')
    parser.add_argument('--role-arn', type=str, help='AWS IAM role ARN to assume for S3 access')"""
    
    # Replace the matched pattern with itself plus the new arguments
    updated_content = re.sub(pattern, r"\1" + new_args, content, flags=re.DOTALL)
    
    # Pattern to match the AWS profile setup
    profile_pattern = r"(if args\.profile:.*?)(\s+# Run anomaly detection)"
    
    # New authentication code to add
    auth_code = """
    # Set AWS credentials if provided
    if args.access_key and args.secret_key:
        logger.info(f"Using provided AWS access keys")
        os.environ['AWS_ACCESS_KEY_ID'] = args.access_key
        os.environ['AWS_SECRET_ACCESS_KEY'] = args.secret_key
        if args.region:
            os.environ['AWS_DEFAULT_REGION'] = args.region
            
    # Set up role assumption if specified
    if args.role_arn:
        try:
            logger.info(f"Assuming IAM role: {args.role_arn}")
            import boto3
            sts_client = boto3.client('sts', region_name=args.region)
            assumed_role = sts_client.assume_role(
                RoleArn=args.role_arn,
                RoleSessionName="FraudDetectionSession"
            )
            credentials = assumed_role['Credentials']
            
            os.environ['AWS_ACCESS_KEY_ID'] = credentials['AccessKeyId']
            os.environ['AWS_SECRET_ACCESS_KEY'] = credentials['SecretAccessKey']
            os.environ['AWS_SESSION_TOKEN'] = credentials['SessionToken']
            if args.region:
                os.environ['AWS_DEFAULT_REGION'] = args.region
        except Exception as e:
            logger.error(f"Error assuming role: {e}")
    
    # Run anomaly detection"""
    
    # Replace the matched pattern
    updated_content = re.sub(profile_pattern, r"\1" + auth_code, updated_content, flags=re.DOTALL)
    
    # Save the updated file
    with open(script_path, 'w') as file:
        file.write(updated_content)
    
    print(f"Successfully updated {script_path} with new authentication options")
    return True

if __name__ == "__main__":
    update_main_function()

#!/usr/bin/env python3
"""
Set up temporary AWS credentials for AIS Fraud Detection project

This script sets environment variables for temporary AWS credentials and
tests connectivity to the S3 bucket.
"""

import os
import subprocess
import sys
import platform
import boto3
import botocore.exceptions

def set_env_variables():
    """Set AWS environment variables for temporary credentials"""
    print("Setting AWS temporary credentials as environment variables...")
    
    # Credentials provided
    os.environ["AWS_ACCESS_KEY_ID"] = "ASIAVNJ7MHGLBDXB3RHB"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "cbtSohqXAMag/FCSNlUAut0WEVZ6lVwELk5VrgUO"
    os.environ["AWS_SESSION_TOKEN"] = "IQoJb3JpZ2luX2VjEIz//////////wEaCXVzLWVhc3QtMSJHMEUCIBUfR2M5f00bdg018qiBVFPY00DDvCPYns9C4PM7uEduAiEAw4F1KTyBuWEm0/RbDIR9hfYHkFddDyXXCQluKNiD1dwq+wIIVBACGgwzNzIxODQ0NjM3NjYiDP26KeLH7FYuK5Zn5irYAvynuaNjIuQYvppqAktZchxf/BoN4iu6LExRNhlU1/WgDs/SG+WI6TcJzeCaxSn4oqF7CKBpFY1gClCkcl4680G+mfXHC31fPc00cRRz+G6Rq7V4UpMQV3iTzTMMOGKFxNxDLCrDfnP3n6FQtb5OQKPhezUIANJIBmlVPq5HqIGqOLIWaqQpdZ3tdem+xlX0kl2BACyzly0cnwVGF1kPn9+YmrHEX7tFE7sQjqWvUex3/58W/kKDyq6aq2Vv3esUpGmb55x7CwPEHtDwx0pcQEJPtYtRu4b6hTCzXCaxJoPmzaOJ/Q4xxWmlhY6ieQRmO4XloswamN5TvYSgmUP8H5PqW8zQtZvkfae5fT8mfTjC1auyeqeAr4XrsiwIFxqtVCsxv3hRrXXbkUDcoGzdNr8QgG2HiQJTvH4acWf2v9b63S1BR+GjvfAnNi+X1V1ysJU6U/FsEMzZMNe4oMgGOqUBWcIJs0jg5NNkf7ztcrHiw+3UVvsEJ+eMlx7MF9o7Ei2dnM7k9uCC+KgY3MBWj3Ip6D3vTXeQe3qCYVWZbCfQwMb6rPogZdngf0zkt+hAk3DjZhosL66mDv02dN+Y0UBs1MtuXZuy3pIJobU/bejxMx0//txgBM8VdQpIivX/NxGbemYuQ3LayNGz81vnQq88i5TjieCUTu1TWDE41pgumuov63Q4"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    
    print("AWS temporary credentials set successfully")
    print("Warning: These credentials will expire after a few hours")

def test_connection():
    """Test connection to S3 using the temporary credentials"""
    print("\nTesting connection to S3...")
    try:
        # Create a session with the environment variables
        session = boto3.session.Session()
        s3 = session.client('s3')
        
        # Test the bucket access
        bucket = "ai-dsde-txg-datathon2025"
        prefix = "teams/dreadnought/parquet/"
        
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=5)
        
        if 'Contents' in response:
            print("✅ Successfully connected to S3 bucket!")
            print(f"Found {len(response['Contents'])} objects in the bucket")
            
            # List a few files
            print("\nSample files:")
            for item in response['Contents'][:5]:
                print(f"- {item['Key']} ({item['Size']} bytes)")
        else:
            print("✅ Successfully connected to S3 bucket, but no objects found in the specified prefix")
        
        return True
    except botocore.exceptions.ClientError as e:
        print(f"❌ Error accessing S3: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def print_command_prompt_instructions():
    """Print instructions for setting environment variables in command prompt"""
    print("\n=== Command Prompt Instructions ===")
    print("To set these environment variables in Command Prompt, run:")
    print("SET AWS_ACCESS_KEY_ID=ASIAVNJ7MHGLBDXB3RHB")
    print("SET AWS_SECRET_ACCESS_KEY=cbtSohqXAMag/FCSNlUAut0WEVZ6lVwELk5VrgUO")
    print("SET AWS_SESSION_TOKEN=IQoJb3JpZ2luX2VjEIz//////////wEaCXVzLWVhc3QtMSJHMEUCIBUfR2M5f00bdg018qiBVFPY00DDvCPYns9C4PM7uEduAiEAw4F1KTyBuWEm0/RbDIR9hfYHkFddDyXXCQluKNiD1dwq+wIIVBACGgwzNzIxODQ0NjM3NjYiDP26KeLH7FYuK5Zn5irYAvynuaNjIuQYvppqAktZchxf/BoN4iu6LExRNhlU1/WgDs/SG+WI6TcJzeCaxSn4oqF7CKBpFY1gClCkcl4680G+mfXHC31fPc00cRRz+G6Rq7V4UpMQV3iTzTMMOGKFxNxDLCrDfnP3n6FQtb5OQKPhezUIANJIBmlVPq5HqIGqOLIWaqQpdZ3tdem+xlX0kl2BACyzly0cnwVGF1kPn9+YmrHEX7tFE7sQjqWvUex3/58W/kKDyq6aq2Vv3esUpGmb55x7CwPEHtDwx0pcQEJPtYtRu4b6hTCzXCaxJoPmzaOJ/Q4xxWmlhY6ieQRmO4XloswamN5TvYSgmUP8H5PqW8zQtZvkfae5fT8mfTjC1auyeqeAr4XrsiwIFxqtVCsxv3hRrXXbkUDcoGzdNr8QgG2HiQJTvH4acWf2v9b63S1BR+GjvfAnNi+X1V1ysJU6U/FsEMzZMNe4oMgGOqUBWcIJs0jg5NNkf7ztcrHiw+3UVvsEJ+eMlx7MF9o7Ei2dnM7k9uCC+KgY3MBWj3Ip6D3vTXeQe3qCYVWZbCfQwMb6rPogZdngf0zkt+hAk3DjZhosL66mDv02dN+Y0UBs1MtuXZuy3pIJobU/bejxMx0//txgBM8VdQpIivX/NxGbemYuQ3LayNGz81vnQq88i5TjieCUTu1TWDE41pgumuov63Q4")
    print("SET AWS_DEFAULT_REGION=us-east-1")

def main():
    """Main function to set up temporary credentials and test connection"""
    print("=== AWS Temporary Credentials Setup ===\n")
    
    # Set environment variables
    set_env_variables()
    
    # Test connection
    success = test_connection()
    
    # Print instructions for command prompt
    print_command_prompt_instructions()
    
    # Print instructions for running the application
    print("\n=== Next Steps ===")
    print("1. Run the AIS Fraud Detection application:")
    print("   python AnomalyDetectGUI_new.py")
    print("2. Go to the Advanced tab")
    print("3. Check 'Use AWS S3 for data storage'")
    print("4. Enter S3 URI: s3://ai-dsde-txg-datathon2025/teams/dreadnought/parquet/")
    print("5. Click 'Test S3 Connection'")
    
    if not success:
        print("\nNote: If the test failed, the credentials may have expired.")
        print("      Please get new temporary credentials or set up SSO.")

if __name__ == "__main__":
    main()

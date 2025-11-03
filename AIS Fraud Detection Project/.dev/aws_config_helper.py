#!/usr/bin/env python3
"""
AWS Configuration Helper for AIS Shipping Fraud Detection

This script helps users set up their AWS credentials for accessing S3 data.
It guides users through the process of setting up credentials and testing the connection.
"""

import os
import sys
import configparser
import boto3
import botocore.exceptions
import getpass
from test_s3_connectivity_enhanced import test_s3_connectivity

def clear_screen():
    """Clear the terminal screen based on OS"""
    if os.name == 'nt':  # Windows
        os.system('cls')
    else:  # Unix/Linux/Mac
        os.system('clear')

def create_aws_config(access_key=None, secret_key=None, region=None):
    """
    Create or update AWS config files
    
    Args:
        access_key (str): AWS Access Key ID
        secret_key (str): AWS Secret Access Key
        region (str): AWS Region
        
    Returns:
        bool: True if configuration was successful
    """
    try:
        # Create ~/.aws directory if it doesn't exist
        aws_dir = os.path.expanduser("~/.aws")
        os.makedirs(aws_dir, exist_ok=True)
        
        # Create credentials file
        credentials_path = os.path.join(aws_dir, "credentials")
        config = configparser.ConfigParser()
        
        # Read existing config if it exists
        if os.path.exists(credentials_path):
            config.read(credentials_path)
            
        # Make sure default profile exists
        if 'default' not in config:
            config['default'] = {}
            
        # Prompt for credentials if not provided
        if not access_key:
            access_key = input("Enter your AWS Access Key ID: ")
        if not secret_key:
            secret_key = getpass.getpass("Enter your AWS Secret Access Key: ")
        if not region:
            region = input("Enter your preferred AWS Region (default: us-east-1): ") or "us-east-1"
            
        # Set credentials
        config['default']['aws_access_key_id'] = access_key
        config['default']['aws_secret_access_key'] = secret_key
        
        # Write to credentials file
        with open(credentials_path, 'w') as f:
            config.write(f)
            
        # Create config file for region
        config_path = os.path.join(aws_dir, "config")
        config = configparser.ConfigParser()
        
        # Read existing config if it exists
        if os.path.exists(config_path):
            config.read(config_path)
            
        # Make sure default profile exists
        if 'default' not in config:
            config['default'] = {}
            
        # Set region
        config['default']['region'] = region
        
        # Write to config file
        with open(config_path, 'w') as f:
            config.write(f)
            
        print(f"\nAWS credentials successfully configured in {aws_dir}")
        return True
        
    except Exception as e:
        print(f"Error configuring AWS credentials: {str(e)}")
        return False

def test_credentials(s3_uri='s3://ai-dsde-txg-datathon2025/teams/dreadnought/parquet/'):
    """
    Test AWS credentials by trying to access an S3 bucket
    
    Args:
        s3_uri (str): S3 URI to test
        
    Returns:
        bool: True if test is successful
    """
    try:
        print("\nTesting AWS credentials...")
        
        # Create a session with the credentials
        session = boto3.session.Session()
        
        # Check if credentials are set
        credentials = session.get_credentials()
        if credentials is None:
            print("Error: No AWS credentials found!")
            return False
            
        # Get region
        region = session.region_name or "us-east-1"
        print(f"Using AWS region: {region}")
        
        # Test S3 connection
        return test_s3_connectivity(s3_uri)
        
    except Exception as e:
        print(f"Error testing AWS credentials: {str(e)}")
        return False

def show_menu():
    """Display the main menu"""
    clear_screen()
    print("=" * 80)
    print("                   AWS CONFIGURATION HELPER                   ")
    print("=" * 80)
    print("\nThis tool helps you set up your AWS credentials for accessing S3 data.")
    print("\nMenu Options:")
    print("1. Configure AWS Credentials")
    print("2. Test AWS Connectivity")
    print("3. Update AIS Fraud Detection Configuration")
    print("4. Show AWS CLI Installation Instructions")
    print("5. Exit")
    
    choice = input("\nEnter your choice (1-5): ")
    return choice

def show_aws_cli_instructions():
    """Display instructions for installing AWS CLI"""
    clear_screen()
    print("=" * 80)
    print("                   AWS CLI INSTALLATION INSTRUCTIONS                   ")
    print("=" * 80)
    
    print("\nWindows Installation:")
    print("1. Download the AWS CLI MSI installer for Windows from:")
    print("   https://aws.amazon.com/cli/")
    print("2. Run the downloaded MSI installer and follow the instructions")
    print("3. Restart your command prompt and verify installation with:")
    print("   aws --version")
    
    print("\nMac Installation:")
    print("1. Install AWS CLI using Homebrew:")
    print("   brew install awscli")
    print("2. Verify installation:")
    print("   aws --version")
    
    print("\nLinux Installation:")
    print("1. Install using pip:")
    print("   pip install awscli --upgrade --user")
    print("2. Verify installation:")
    print("   aws --version")
    
    print("\nAfter Installation:")
    print("Configure your credentials by running:")
    print("   aws configure")
    print("You'll be prompted to enter your AWS Access Key, Secret Key, and region.")
    
    input("\nPress Enter to return to the main menu...")

def update_ais_fraud_config(s3_uri='s3://ai-dsde-txg-datathon2025/teams/dreadnought/parquet/'):
    """
    Update the AIS Fraud Detection config.ini file with S3 settings
    
    Args:
        s3_uri (str): S3 URI to use
        
    Returns:
        bool: True if update is successful
    """
    try:
        # Find config.ini file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'config.ini')
        
        if not os.path.exists(config_path):
            print(f"Error: Config file not found at {config_path}")
            return False
            
        # Read the config
        config = configparser.ConfigParser()
        config.read(config_path)
        
        # Update S3 settings
        if 'S3_SETTINGS' not in config:
            config['S3_SETTINGS'] = {}
        
        config['S3_SETTINGS']['USE_S3'] = 'True'
        config['S3_SETTINGS']['S3_DATA_URI'] = s3_uri
        
        # Write to file
        with open(config_path, 'w') as f:
            config.write(f)
            
        print(f"\nUpdated config.ini with S3 settings:")
        print(f"USE_S3 = True")
        print(f"S3_DATA_URI = {s3_uri}")
        return True
        
    except Exception as e:
        print(f"Error updating AIS Fraud Detection configuration: {str(e)}")
        return False

def main():
    """Main function to run the AWS Configuration Helper"""
    while True:
        choice = show_menu()
        
        if choice == '1':
            # Configure AWS Credentials
            clear_screen()
            print("=" * 80)
            print("                   CONFIGURE AWS CREDENTIALS                   ")
            print("=" * 80)
            print("\nYou'll need your AWS Access Key ID and Secret Access Key.")
            print("These can be obtained from your AWS administrator or IAM console.")
            
            if create_aws_config():
                input("\nConfiguration successful! Press Enter to continue...")
            else:
                input("\nConfiguration failed. Press Enter to continue...")
                
        elif choice == '2':
            # Test AWS Connectivity
            clear_screen()
            print("=" * 80)
            print("                   TEST AWS CONNECTIVITY                   ")
            print("=" * 80)
            
            s3_uri = input("\nEnter S3 URI to test (press Enter for default): ") or 's3://ai-dsde-txg-datathon2025/teams/dreadnought/parquet/'
            
            if test_credentials(s3_uri):
                print("\nAWS credentials test successful!")
                input("Press Enter to continue...")
            else:
                input("\nAWS credentials test failed. Press Enter to continue...")
                
        elif choice == '3':
            # Update AIS Fraud Detection Configuration
            clear_screen()
            print("=" * 80)
            print("                   UPDATE AIS FRAUD DETECTION CONFIGURATION                   ")
            print("=" * 80)
            
            s3_uri = input("\nEnter S3 URI to use (press Enter for default): ") or 's3://ai-dsde-txg-datathon2025/teams/dreadnought/parquet/'
            
            if update_ais_fraud_config(s3_uri):
                input("\nConfiguration update successful! Press Enter to continue...")
            else:
                input("\nConfiguration update failed. Press Enter to continue...")
                
        elif choice == '4':
            # Show AWS CLI Installation Instructions
            show_aws_cli_instructions()
            
        elif choice == '5':
            # Exit
            print("\nExiting AWS Configuration Helper. Goodbye!")
            break
            
        else:
            input("\nInvalid choice. Press Enter to try again...")

if __name__ == "__main__":
    main()

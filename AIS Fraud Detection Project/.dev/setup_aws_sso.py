#!/usr/bin/env python3
"""
AWS SSO Setup Guide for AIS Fraud Detection project

This script guides users through setting up AWS SSO for accessing
the S3 bucket for the AIS Fraud Detection project.
"""

import os
import sys
import subprocess
import platform
import time
import webbrowser

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print the script header"""
    clear_screen()
    print("=" * 80)
    print("                  AWS SSO SETUP FOR AIS FRAUD DETECTION                  ")
    print("=" * 80)
    print("\nThis guide will help you set up AWS SSO for accessing S3 data")
    print("Account: Cakes and Tensors (372184463766)")
    print("Role: BAHSSO_372184463766_Dreadnought\n")

def check_aws_cli():
    """Check if AWS CLI is installed and its version"""
    try:
        result = subprocess.run(["aws", "--version"], 
                              capture_output=True, 
                              text=True)
        if result.returncode == 0:
            print(f"✅ AWS CLI is installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ AWS CLI is installed but returned an error.")
            return False
    except FileNotFoundError:
        print("❌ AWS CLI is not installed or not in PATH.")
        return False

def open_sso_portal():
    """Open the AWS SSO portal in a web browser"""
    sso_url = "https://bahextendedenterprise.awsapps.com/start/#"
    print(f"\nOpening AWS SSO portal in your browser: {sso_url}")
    print("Please log in with your Booz Allen Hamilton credentials.")
    
    try:
        webbrowser.open(sso_url)
        input("\nPress Enter once you've logged in to continue...")
    except Exception as e:
        print(f"Could not open browser automatically. Please visit: {sso_url}")
        input("\nPress Enter once you've logged in to continue...")

def configure_sso_session():
    """Guide the user through AWS SSO session configuration"""
    print("\n=== STEP 1: Configure AWS SSO Session ===")
    print("Running 'aws configure sso-session'")
    print("Use the following values when prompted:")
    print("  SSO session name: bahsso")
    print("  SSO start URL: https://bahextendedenterprise.awsapps.com/start/#")
    print("  SSO region: us-east-1")
    print("  SSO registration scopes: sso:account:access")
    
    print("\nExecuting command now...\n")
    
    try:
        subprocess.run(["aws", "configure", "sso-session", 
                       "--session-name", "bahsso",
                       "--sso-start-url", "https://bahextendedenterprise.awsapps.com/start/#",
                       "--sso-region", "us-east-1",
                       "--registration-scopes", "sso:account:access"])
    except Exception as e:
        print(f"Error running command: {e}")
        print("\nYou can manually run:")
        print("aws configure sso-session --session-name bahsso --sso-start-url https://bahextendedenterprise.awsapps.com/start/# --sso-region us-east-1 --registration-scopes sso:account:access")

def login_to_sso():
    """Guide the user through AWS SSO login"""
    print("\n=== STEP 2: Log in to AWS SSO ===")
    print("Running 'aws sso login --sso-session bahsso'")
    print("This will open a browser window for authentication")
    
    try:
        subprocess.run(["aws", "sso", "login", "--sso-session", "bahsso"])
        print("\n✅ Successfully logged in to AWS SSO")
    except Exception as e:
        print(f"Error during SSO login: {e}")
        print("\nYou can manually run:")
        print("aws sso login --sso-session bahsso")

def configure_profile():
    """Guide the user through AWS profile configuration"""
    print("\n=== STEP 3: Configure AWS CLI Profile ===")
    print("Running 'aws configure sso'")
    print("Use the following values when prompted:")
    print("  SSO session: bahsso")
    print("  Account ID: 372184463766")
    print("  Role name: BAHSSO_372184463766_Dreadnought")
    print("  Region: us-east-1")
    print("  Output format: json")
    
    try:
        subprocess.run(["aws", "configure", "sso", 
                       "--profile", "dreadnought"])
    except Exception as e:
        print(f"Error configuring profile: {e}")
        print("\nYou can manually run:")
        print("aws configure sso --profile dreadnought")

def test_connection():
    """Test the AWS SSO connection"""
    print("\n=== STEP 4: Test AWS SSO Connection ===")
    print("Testing connection to S3 with the configured profile...")
    
    try:
        result = subprocess.run(
            ["aws", "s3", "ls", "s3://ai-dsde-txg-datathon2025/teams/dreadnought/", 
             "--profile", "dreadnought"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("\n✅ Successfully connected to S3 bucket!")
            print("\nFiles in the bucket:")
            print(result.stdout)
            return True
        else:
            print(f"\n❌ Error accessing S3: {result.stderr}")
            return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

def update_config_for_sso():
    """Update the AIS Fraud Detection configuration for SSO"""
    print("\n=== STEP 5: Update AIS Fraud Detection Configuration ===")
    
    # Path to the configuration file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.ini")
    
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found at: {config_path}")
        return
    
    # Read the current content
    with open(config_path, "r") as file:
        content = file.readlines()
    
    # Check if S3_SETTINGS section exists
    s3_section_exists = False
    for line in content:
        if line.strip() == "[S3_SETTINGS]":
            s3_section_exists = True
            break
    
    # Prepare the new content
    if not s3_section_exists:
        # Add the S3_SETTINGS section
        content.append("\n[S3_SETTINGS]\n")
        content.append("use_s3 = True\n")
        content.append("s3_data_uri = s3://ai-dsde-txg-datathon2025/teams/dreadnought/parquet/\n")
        content.append("aws_profile = dreadnought\n")
    else:
        # Update existing S3_SETTINGS section
        new_content = []
        in_s3_section = False
        added_profile = False
        
        for line in content:
            if line.strip() == "[S3_SETTINGS]":
                in_s3_section = True
            elif line.strip().startswith("[") and in_s3_section:
                in_s3_section = False
                if not added_profile:
                    new_content.append("aws_profile = dreadnought\n")
                    added_profile = True
            elif in_s3_section and line.strip().startswith("use_s3"):
                new_content.append("use_s3 = True\n")
            elif in_s3_section and line.strip().startswith("s3_data_uri"):
                new_content.append("s3_data_uri = s3://ai-dsde-txg-datathon2025/teams/dreadnought/parquet/\n")
            elif in_s3_section and line.strip().startswith("aws_profile"):
                new_content.append("aws_profile = dreadnought\n")
                added_profile = True
            else:
                new_content.append(line)
        
        if in_s3_section and not added_profile:
            new_content.append("aws_profile = dreadnought\n")
        
        content = new_content
    
    # Write the updated content
    with open(config_path, "w") as file:
        file.writelines(content)
    
    print(f"✅ Updated configuration file with AWS SSO settings at: {config_path}")
    print("   Added 'aws_profile = dreadnought' to use the SSO profile")

def print_instructions_for_manual_setup():
    """Print instructions for manual AWS SSO setup"""
    print("\n=== Manual AWS SSO Setup Instructions ===")
    print("If the automatic setup didn't work, follow these steps:")
    print("\n1. Configure an SSO session:")
    print("   aws configure sso-session --session-name bahsso --sso-start-url https://bahextendedenterprise.awsapps.com/start/# --sso-region us-east-1 --registration-scopes sso:account:access")
    
    print("\n2. Log in to AWS SSO:")
    print("   aws sso login --sso-session bahsso")
    
    print("\n3. Configure a profile for Dreadnought:")
    print("   aws configure sso --profile dreadnought")
    print("   - When prompted for SSO session, enter: bahsso")
    print("   - When prompted for Account ID, enter: 372184463766")
    print("   - When prompted for Role name, enter: BAHSSO_372184463766_Dreadnought")
    print("   - When prompted for Region, enter: us-east-1")
    print("   - When prompted for Output format, enter: json")
    
    print("\n4. Test the connection:")
    print("   aws s3 ls s3://ai-dsde-txg-datathon2025/teams/dreadnought/ --profile dreadnought")
    
    print("\n5. Add the following to config.ini in the [S3_SETTINGS] section:")
    print("   aws_profile = dreadnought")

def main():
    """Main function to guide through AWS SSO setup"""
    print_header()
    
    print("This script will guide you through setting up AWS SSO access")
    print("for the AIS Fraud Detection project.")
    input("\nPress Enter to continue...")
    
    # Check if AWS CLI is installed
    if not check_aws_cli():
        print("\n❌ Please install AWS CLI v2 and try again.")
        print("Download from: https://aws.amazon.com/cli/")
        return
    
    # Open SSO portal
    open_sso_portal()
    
    # Configure SSO session
    configure_sso_session()
    
    # Login to SSO
    login_to_sso()
    
    # Configure profile
    configure_profile()
    
    # Test connection
    success = test_connection()
    
    # Update configuration
    if success:
        update_config_for_sso()
    
    # Print instructions for manual setup
    print_instructions_for_manual_setup()
    
    print("\n=== Next Steps ===")
    print("1. Run the AIS Fraud Detection application:")
    print("   python AnomalyDetectGUI_new.py")
    print("2. Go to the Advanced tab")
    print("3. Ensure 'Use AWS S3 for data storage' is checked")
    print("4. Enter S3 URI: s3://ai-dsde-txg-datathon2025/teams/dreadnought/parquet/")
    print("5. Click 'Test S3 Connection'")

if __name__ == "__main__":
    main()

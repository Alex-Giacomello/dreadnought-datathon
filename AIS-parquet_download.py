import boto3
import os

# Initialize client
s3 = boto3.client("s3")

# Bucket and prefix (your "folder")
bucket_name = "ai-dsde-txg-datathon2025"
prefix = "teams/dreadnought/parquet/"
local_dir = "./eda/data/march_2025_files"

# Create local folder if it doesn't exist
os.makedirs(local_dir, exist_ok=True)

# List all files in that prefix
response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

# Filter and download only March 2025 files
if "Contents" in response:
    for obj in response["Contents"]:
        key = obj["Key"]
        filename = os.path.basename(key)
        # Filter: only files containing "2025-03"
        if "2025-03" in filename and filename.endswith(".parquet"):
            local_path = os.path.join(local_dir, filename)
            print(f"⬇️ Downloading {filename}...")
            s3.download_file(bucket_name, key, local_path)
    print("✅ All March 2025 files downloaded successfully!")
else:
    print("No files found under that prefix.")

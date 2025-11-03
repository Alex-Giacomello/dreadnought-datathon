import boto3
import botocore.exceptions

def test_s3_connectivity(bucket_name, prefix):
    try:
        # Create an S3 client
        s3 = boto3.client('s3')
        
        # Test if we can list objects in the bucket
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix, MaxKeys=1)
        
        # Check if we could access the bucket
        if 'Contents' in response:
            return True, f"Successfully accessed S3 bucket. Found objects with prefix '{prefix}'."
        else:
            return True, f"Successfully accessed S3 bucket. No objects found with prefix '{prefix}'."
    
    except botocore.exceptions.ClientError as e:
        return False, f"Error accessing S3 bucket: {str(e)}"
    except botocore.exceptions.NoCredentialsError:
        return False, "AWS credentials not found. Please configure AWS credentials."
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

if __name__ == "__main__":
    # Parse the S3 URI to extract bucket name and prefix
    uri = "s3://ai-dsde-txg-datathon2025/teams/dreadnought/parquet/"
    parts = uri.replace("s3://", "").split("/")
    bucket_name = parts[0]
    prefix = "/".join(parts[1:])
    
    print(f"Testing connection to bucket: {bucket_name}")
    print(f"Prefix: {prefix}")
    
    success, message = test_s3_connectivity(bucket_name, prefix)
    print(message)

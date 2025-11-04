
import pandas as pd
bucket_name = "ai-dsde-txg-datathon2025"
prefix = "teams/dreadnought/parquet/"

bucket_path = f"s3://{bucket_name}/{prefix}"
df = pd.read_parquet(bucket_path + "ais-2025-03-31.parquet")

print(df.head())

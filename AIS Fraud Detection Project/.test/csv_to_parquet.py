#!/usr/bin/env python3
"""
AIS Shipping Fraud Detection - CSV to Parquet Converter
Converts daily AIS CSV files to Parquet format
"""
import os
import pandas as pd
import argparse
from pathlib import Path
import glob

def convert_csv_to_parquet(input_dir=None, output_dir=None):
    """
    Convert all CSV files in input_dir to Parquet format in output_dir
    
    Args:
        input_dir: Directory containing CSV files (default: Test_data in user's home)
        output_dir: Directory to save Parquet files (default: Parquet subdirectory in input_dir)
    
    Returns:
        List of created Parquet files
    """
    # Use default directories if not specified
    if not input_dir:
        input_dir = os.path.join(str(Path.home()), "Test_data")
    
    if not output_dir:
        output_dir = os.path.join(input_dir, "Parquet")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    print(f"Created output directory: {output_dir}")
    
    # Find all CSV files in the input directory
    csv_pattern = os.path.join(input_dir, "ais-*.csv")
    csv_files = glob.glob(csv_pattern)
    
    if not csv_files:
        print(f"No CSV files matching pattern {csv_pattern} found")
        return []
    
    print(f"Found {len(csv_files)} CSV files to convert")
    
    # Convert each CSV file to Parquet
    parquet_files = []
    for csv_file in csv_files:
        try:
            # Read CSV
            df = pd.read_csv(csv_file)
            
            # Create Parquet filename with same basename but .parquet extension
            basename = os.path.basename(csv_file)
            parquet_basename = os.path.splitext(basename)[0] + ".parquet"
            parquet_file = os.path.join(output_dir, parquet_basename)
            
            # Write to Parquet format
            df.to_parquet(parquet_file, engine='pyarrow', index=False)
            
            parquet_files.append(parquet_file)
            print(f"  - Converted {basename} to {parquet_basename}")
        except Exception as e:
            print(f"  - Error converting {os.path.basename(csv_file)}: {str(e)}")
    
    print(f"Created {len(parquet_files)} Parquet files")
    return parquet_files

def main():
    parser = argparse.ArgumentParser(description='Convert AIS CSV files to Parquet format')
    parser.add_argument('--input-dir', help='Directory containing CSV files (default: Test_data in user\'s home)')
    parser.add_argument('--output-dir', help='Directory to save Parquet files (default: Parquet subdirectory in input-dir)')
    
    args = parser.parse_args()
    
    convert_csv_to_parquet(args.input_dir, args.output_dir)

if __name__ == "__main__":
    main()

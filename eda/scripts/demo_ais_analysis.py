"""
Demonstration script for AIS Data Analysis Toolkit
This script shows how to use the toolkit for efficient AIS data exploration
"""

import pandas as pd
import numpy as np
from ais_data_utils import AISDataLoader, AISDataAnalyzer, MemoryMonitor, optimize_dataframe_memory
from ..utils.ais_visualization_utils import AISVisualizer, create_summary_report

def demo_analysis():
    """Demonstrate the AIS analysis workflow"""
    
    print("🚢 AIS Data Analysis Toolkit Demo")
    print("=" * 50)
    
    # Configuration (you would normally import this from config.py)
    S3_BUCKET = "your-datathon-bucket"  # Replace with actual bucket
    S3_PREFIX = "ais-parquet/"
    MEMORY_LIMIT_GB = 6.0
    SAMPLE_SIZE = 10000  # Smaller for demo
    
    print(f"Initial memory usage: {MemoryMonitor.get_memory_usage():.2f} GB")
    
    # Initialize components
    print("\n1. Initializing data loader...")
    data_loader = AISDataLoader(
        s3_bucket=S3_BUCKET,
        s3_prefix=S3_PREFIX,
        memory_limit_gb=MEMORY_LIMIT_GB
    )
    
    analyzer = AISDataAnalyzer(data_loader)
    visualizer = AISVisualizer()
    
    # Discover data
    print("\n2. Discovering available data...")
    try:
        parquet_files = data_loader.list_parquet_files()
        print(f"   Found {len(parquet_files)} parquet files")
        
        if not parquet_files:
            print("   ⚠️  No parquet files found. This is expected in demo mode.")
            print("   ✅ In real usage, update S3_BUCKET and S3_PREFIX in your config")
            return demonstrate_with_sample_data()
        
        # Get metadata for first few files
        print("\n3. Examining file metadata...")
        for i, file_path in enumerate(parquet_files[:3]):
            metadata = data_loader.get_file_metadata(file_path)
            if metadata:
                print(f"   File {i+1}: {metadata['num_rows']:,} rows, "
                      f"{metadata['num_columns']} columns, "
                      f"{metadata['file_size_mb']:.1f} MB")
        
        # Create sample
        print(f"\n4. Creating sample dataset ({SAMPLE_SIZE:,} rows)...")
        sample_df = data_loader.sample_data(
            file_paths=parquet_files[:5],
            sample_size=SAMPLE_SIZE
        )
        
        if sample_df.empty:
            print("   ⚠️  Could not create sample. Using demo data instead.")
            return demonstrate_with_sample_data()
        
        return demonstrate_analysis(sample_df, analyzer, visualizer)
        
    except Exception as e:
        print(f"   ⚠️  Error accessing S3 data: {e}")
        print("   ✅ This is expected in demo mode. Using sample data instead.")
        return demonstrate_with_sample_data()

def demonstrate_with_sample_data():
    """Demonstrate analysis with synthetic sample data"""
    
    print("\n📊 Creating synthetic AIS data for demonstration...")
    
    # Create realistic synthetic AIS data
    np.random.seed(42)
    n_records = 5000
    n_vessels = 50
    
    # Generate vessel IDs
    vessel_ids = np.random.choice(range(100000000, 999999999), n_vessels, replace=False)
    
    # Generate data
    data = {
        'MMSI': np.random.choice(vessel_ids, n_records),
        'BaseDateTime': pd.date_range('2023-01-01', periods=n_records, freq='5min'),
        'LAT': np.random.uniform(25.0, 45.0, n_records),  # US East Coast
        'LON': np.random.uniform(-85.0, -65.0, n_records),
        'SOG': np.random.exponential(8, n_records),  # Speed over ground
        'COG': np.random.uniform(0, 360, n_records),  # Course over ground
        'VesselType': np.random.choice(['Cargo', 'Tanker', 'Fishing', 'Passenger', 'Other'], n_records)
    }
    
    # Add some realistic patterns
    # Vessels near ports move slower
    port_mask = (data['LAT'] < 30) & (data['LON'] > -80)
    data['SOG'][port_mask] *= 0.3
    
    sample_df = pd.DataFrame(data)
    
    # Optimize memory
    sample_df = optimize_dataframe_memory(sample_df)
    
    print(f"   ✅ Created synthetic dataset: {sample_df.shape}")
    print(f"   Memory usage: {sample_df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    
    # Initialize analyzer and visualizer for demo
    data_loader = AISDataLoader("demo-bucket", "demo-prefix/")
    analyzer = AISDataAnalyzer(data_loader)
    visualizer = AISVisualizer()
    
    return demonstrate_analysis(sample_df, analyzer, visualizer)

def demonstrate_analysis(df, analyzer, visualizer):
    """Demonstrate analysis capabilities"""
    
    print(f"\n5. Analyzing dataset ({len(df):,} records)...")
    
    # Basic statistics
    print("\n   📈 Basic Statistics:")
    basic_stats = analyzer.get_basic_stats(df)
    print(f"      Shape: {basic_stats['shape']}")
    print(f"      Memory: {basic_stats['memory_usage_mb']:.2f} MB")
    print(f"      Null values: {sum(basic_stats['null_counts'].values()):,}")
    
    # Temporal analysis
    print("\n   ⏰ Temporal Analysis:")
    temporal_stats = analyzer.analyze_temporal_patterns(df)
    if 'error' not in temporal_stats:
        print(f"      Date range: {temporal_stats['date_range']['start']} to {temporal_stats['date_range']['end']}")
        print(f"      Records per hour: {temporal_stats['records_per_hour']:.1f}")
        print(f"      Peak hour: {max(temporal_stats['hourly_distribution'], key=temporal_stats['hourly_distribution'].get)}")
    
    # Vessel analysis
    print("\n   🚢 Vessel Analysis:")
    vessel_stats = analyzer.analyze_vessel_patterns(df)
    if 'error' not in vessel_stats:
        print(f"      Unique vessels: {vessel_stats['unique_vessels']:,}")
        print(f"      Avg records per vessel: {vessel_stats['avg_records_per_vessel']:.1f}")
        top_vessel = list(vessel_stats['top_vessels'].keys())[0]
        print(f"      Most active vessel: {top_vessel} ({vessel_stats['top_vessels'][top_vessel]:,} records)")
    
    # Geographic analysis
    print("\n   🌍 Geographic Analysis:")
    geo_stats = analyzer.analyze_geographic_patterns(df)
    if 'error' not in geo_stats:
        print(f"      Valid coordinates: {geo_stats['valid_coordinates_pct']:.1f}%")
        print(f"      Lat range: {geo_stats['lat_range']['min']:.3f} to {geo_stats['lat_range']['max']:.3f}")
        print(f"      Lon range: {geo_stats['lon_range']['min']:.3f} to {geo_stats['lon_range']['max']:.3f}")
        print(f"      Center: ({geo_stats['geographic_center']['lat']:.3f}, {geo_stats['geographic_center']['lon']:.3f})")
    
    # Generate comprehensive report
    print("\n6. Generating comprehensive report...")
    report = create_summary_report(df)
    
    print(f"\n   📋 Summary Report Generated:")
    print(f"      Dataset: {report['dataset_overview']['total_records']:,} records")
    print(f"      Quality: {report['data_quality']['valid_coordinates_pct']:.1f}% valid coordinates")
    print(f"      Vessels: {report['vessel_statistics']['unique_vessels']:,} unique vessels")
    print(f"      Duplicates: {report['data_quality']['duplicate_records']:,} duplicate records")
    
    # Memory check
    print(f"\n7. Final memory check:")
    print(f"   Current usage: {MemoryMonitor.get_memory_usage():.2f} GB")
    
    # Cleanup demonstration
    print(f"\n8. Cleaning up...")
    del df
    MemoryMonitor.force_garbage_collection()
    print(f"   Memory after cleanup: {MemoryMonitor.get_memory_usage():.2f} GB")
    
    print(f"\n✅ Demo completed successfully!")
    return True

def show_usage_examples():
    """Show code examples for common tasks"""
    
    print("\n" + "=" * 50)
    print("📚 USAGE EXAMPLES")
    print("=" * 50)
    
    examples = [
        ("Basic Setup", '''
from ais_data_utils import AISDataLoader, AISDataAnalyzer
from ..utils.ais_visualization_utils import AISVisualizer

# Initialize components
loader = AISDataLoader("your-bucket", "ais-parquet/")
analyzer = AISDataAnalyzer(loader)
visualizer = AISVisualizer()
'''),
        
        ("Data Discovery", '''
# List available files
files = loader.list_parquet_files()

# Get file metadata
metadata = loader.get_file_metadata(files[0])
print(f"Rows: {metadata['num_rows']:,}")
'''),
        
        ("Smart Sampling", '''
# Create representative sample
sample_df = loader.sample_data(
    file_paths=files[:10],
    sample_size=50000
)

# Optimize memory usage
sample_df = optimize_dataframe_memory(sample_df)
'''),
        
        ("Chunked Processing", '''
# Process large files in chunks
for chunk in loader.load_chunked_data(file_path, chunk_size=10000):
    # Analyze chunk
    result = analyze_chunk(chunk)
    # Clean up
    del chunk
'''),
        
        ("Memory Monitoring", '''
from ais_data_utils import MemoryMonitor

# Check memory usage
usage = MemoryMonitor.get_memory_usage()
print(f"Memory: {usage:.2f} GB")

# Force cleanup if needed
if MemoryMonitor.check_memory_threshold(6.0):
    MemoryMonitor.force_garbage_collection()
'''),
        
        ("Analysis Functions", '''
# Comprehensive analysis
stats = analyzer.get_basic_stats(df)
temporal = analyzer.analyze_temporal_patterns(df)
vessels = analyzer.analyze_vessel_patterns(df)
geo = analyzer.analyze_geographic_patterns(df)
'''),
        
        ("Visualizations", '''
# Create visualizations
fig = visualizer.plot_temporal_patterns(df)
trajectories = visualizer.plot_vessel_trajectories(df)
heatmap = visualizer.create_density_heatmap(df)
dashboard = visualizer.create_interactive_dashboard(df)
''')
    ]
    
    for title, code in examples:
        print(f"\n{title}:")
        print(code.strip())

if __name__ == "__main__":
    # Run the demonstration
    success = demo_analysis()
    
    if success:
        show_usage_examples()
        
        print(f"\n" + "=" * 50)
        print("🎯 NEXT STEPS FOR YOUR DATATHON")
        print("=" * 50)
        print("1. Run: python setup_ais_environment.py")
        print("2. Copy config_template.py to config.py")
        print("3. Update config.py with your S3 bucket details")
        print("4. Open quick_start.ipynb in SageMaker Studio")
        print("5. Start exploring your AIS data!")
        print("\n📖 Read MEMORY_OPTIMIZATION.md for best practices")
        print("🚀 Good luck with your datathon!")
    else:
        print("❌ Demo failed. Check your configuration and try again.")

"""
AIS Data Visualization Utilities
Optimized for large datasets and memory efficiency
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from folium.plugins import HeatMap, MarkerCluster
import warnings
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class AISVisualizer:
    """Memory-efficient visualizations for AIS data"""
    
    def __init__(self, max_points_map=10000, max_points_scatter=5000):
        self.max_points_map = max_points_map
        self.max_points_scatter = max_points_scatter
        
    def sample_for_visualization(self, df: pd.DataFrame, max_points: int, 
                               random_seed: int = 42) -> pd.DataFrame:
        """Sample data for visualization to prevent memory issues"""
        if len(df) <= max_points:
            return df
        
        return df.sample(n=max_points, random_state=random_seed)
    
    def plot_vessel_trajectories(self, df: pd.DataFrame, vessel_col: str = 'MMSI',
                               lat_col: str = 'LAT', lon_col: str = 'LON',
                               timestamp_col: str = 'BaseDateTime',
                               max_vessels: int = 5) -> go.Figure:
        """Plot trajectories for top vessels"""
        
        # Get top vessels by record count
        top_vessels = df[vessel_col].value_counts().head(max_vessels).index
        
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set1
        
        for i, vessel_id in enumerate(top_vessels):
            vessel_data = df[df[vessel_col] == vessel_id].copy()
            
            # Sort by timestamp
            if timestamp_col in vessel_data.columns:
                vessel_data = vessel_data.sort_values(timestamp_col)
            
            # Sample if too many points
            if len(vessel_data) > 1000:
                vessel_data = vessel_data.iloc[::len(vessel_data)//1000]
            
            # Filter valid coordinates
            valid_coords = (
                (vessel_data[lat_col] >= -90) & (vessel_data[lat_col] <= 90) &
                (vessel_data[lon_col] >= -180) & (vessel_data[lon_col] <= 180) &
                vessel_data[lat_col].notna() & vessel_data[lon_col].notna()
            )
            
            valid_data = vessel_data[valid_coords]
            
            if len(valid_data) > 1:
                fig.add_trace(go.Scattermapbox(
                    lat=valid_data[lat_col],
                    lon=valid_data[lon_col],
                    mode='lines+markers',
                    name=f'Vessel {vessel_id}',
                    line=dict(color=colors[i % len(colors)], width=2),
                    marker=dict(size=4)
                ))        
        fig.update_layout(
            mapbox=dict(
                style='open-street-map',
                center=dict(lat=df[lat_col].mean(), lon=df[lon_col].mean()),
                zoom=5
            ),
            title='Vessel Trajectories',
            height=600
        )
        
        return fig
    
    def create_density_heatmap(self, df: pd.DataFrame, lat_col: str = 'LAT', 
                             lon_col: str = 'LON') -> folium.Map:
        """Create a density heatmap using Folium"""
        
        # Filter valid coordinates
        valid_coords = (
            (df[lat_col] >= -90) & (df[lat_col] <= 90) &
            (df[lon_col] >= -180) & (df[lon_col] <= 180) &
            df[lat_col].notna() & df[lon_col].notna()
        )
        
        valid_df = df[valid_coords]
        
        # Sample for heatmap
        heatmap_data = self.sample_for_visualization(valid_df, self.max_points_map)
        
        # Calculate center
        center_lat = heatmap_data[lat_col].mean()
        center_lon = heatmap_data[lon_col].mean()
        
        # Create map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=6)
        
        # Prepare data for heatmap
        heat_data = [[row[lat_col], row[lon_col]] for idx, row in heatmap_data.iterrows()]
        
        # Add heatmap
        HeatMap(heat_data, radius=10, blur=15, max_zoom=1).add_to(m)
        
        return m
    
    def plot_temporal_patterns(self, df: pd.DataFrame, 
                             timestamp_col: str = 'BaseDateTime',
                             vessel_col: str = 'MMSI') -> plt.Figure:
        """Plot various temporal patterns"""
        
        if timestamp_col not in df.columns:
            raise ValueError(f"Timestamp column '{timestamp_col}' not found")
        
        # Convert to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Temporal Patterns in AIS Data', fontsize=16)
        
        # 1. Records per day
        daily_counts = df[timestamp_col].dt.date.value_counts().sort_index()
        daily_counts.plot(ax=axes[0,0], kind='line')
        axes[0,0].set_title('Records per Day')
        axes[0,0].set_xlabel('Date')
        axes[0,0].set_ylabel('Record Count')
        axes[0,0].tick_params(axis='x', rotation=45)
        
        # 2. Records per hour of day
        hourly_counts = df[timestamp_col].dt.hour.value_counts().sort_index()
        hourly_counts.plot(ax=axes[0,1], kind='bar')
        axes[0,1].set_title('Records per Hour of Day')
        axes[0,1].set_xlabel('Hour')
        axes[0,1].set_ylabel('Record Count')
        
        # 3. Records per day of week
        df['day_of_week'] = df[timestamp_col].dt.day_name()
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekly_counts = df['day_of_week'].value_counts().reindex(day_order)
        weekly_counts.plot(ax=axes[1,0], kind='bar')
        axes[1,0].set_title('Records per Day of Week')
        axes[1,0].set_xlabel('Day of Week')
        axes[1,0].set_ylabel('Record Count')
        axes[1,0].tick_params(axis='x', rotation=45)
        
        # 4. Unique vessels per day
        if vessel_col in df.columns:
            daily_vessels = df.groupby(df[timestamp_col].dt.date)[vessel_col].nunique()
            daily_vessels.plot(ax=axes[1,1], kind='line')
            axes[1,1].set_title('Unique Vessels per Day')
            axes[1,1].set_xlabel('Date')
            axes[1,1].set_ylabel('Unique Vessels')
            axes[1,1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        return fig
    
    def plot_vessel_speed_analysis(self, df: pd.DataFrame, 
                                 speed_col: str = 'SOG',
                                 vessel_col: str = 'MMSI') -> plt.Figure:
        """Analyze vessel speed patterns"""
        
        if speed_col not in df.columns:
            raise ValueError(f"Speed column '{speed_col}' not found")
        
        # Filter reasonable speeds (0-50 knots)
        valid_speeds = df[(df[speed_col] >= 0) & (df[speed_col] <= 50)]
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Vessel Speed Analysis', fontsize=16)
        
        # 1. Speed distribution
        valid_speeds[speed_col].hist(bins=50, ax=axes[0,0], alpha=0.7)
        axes[0,0].set_title('Speed Distribution')
        axes[0,0].set_xlabel('Speed (knots)')
        axes[0,0].set_ylabel('Frequency')
        
        # 2. Speed vs time of day
        if 'BaseDateTime' in df.columns:
            df_with_hour = valid_speeds.copy()
            df_with_hour['hour'] = pd.to_datetime(df_with_hour['BaseDateTime']).dt.hour
            hourly_speed = df_with_hour.groupby('hour')[speed_col].mean()
            hourly_speed.plot(ax=axes[0,1], kind='line', marker='o')
            axes[0,1].set_title('Average Speed by Hour of Day')
            axes[0,1].set_xlabel('Hour')
            axes[0,1].set_ylabel('Average Speed (knots)')
        
        # 3. Speed boxplot by vessel type (if available)
        if 'VesselType' in df.columns:
            # Get top vessel types
            top_types = df['VesselType'].value_counts().head(8).index
            type_data = valid_speeds[valid_speeds['VesselType'].isin(top_types)]
            
            sns.boxplot(data=type_data, x='VesselType', y=speed_col, ax=axes[1,0])
            axes[1,0].set_title('Speed Distribution by Vessel Type')
            axes[1,0].set_xlabel('Vessel Type')
            axes[1,0].set_ylabel('Speed (knots)')
            axes[1,0].tick_params(axis='x', rotation=45)
        
        # 4. Speed statistics
        speed_stats = valid_speeds[speed_col].describe()
        axes[1,1].text(0.1, 0.9, f"Speed Statistics:\n\n"
                      f"Count: {speed_stats['count']:,.0f}\n"
                      f"Mean: {speed_stats['mean']:.2f} knots\n"
                      f"Std: {speed_stats['std']:.2f} knots\n"
                      f"Min: {speed_stats['min']:.2f} knots\n"
                      f"25%: {speed_stats['25%']:.2f} knots\n"
                      f"50%: {speed_stats['50%']:.2f} knots\n"
                      f"75%: {speed_stats['75%']:.2f} knots\n"
                      f"Max: {speed_stats['max']:.2f} knots",
                      transform=axes[1,1].transAxes, fontsize=12,
                      verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightgray'))
        axes[1,1].set_xlim(0, 1)
        axes[1,1].set_ylim(0, 1)
        axes[1,1].axis('off')
        
        plt.tight_layout()
        return fig
    
    def create_interactive_dashboard(self, df: pd.DataFrame,
                                   lat_col: str = 'LAT', lon_col: str = 'LON',
                                   vessel_col: str = 'MMSI', 
                                   timestamp_col: str = 'BaseDateTime') -> go.Figure:
        """Create an interactive dashboard with multiple views"""
        
        # Sample data for performance
        dashboard_data = self.sample_for_visualization(df, self.max_points_scatter)
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Geographic Distribution', 'Temporal Pattern', 
                          'Vessel Activity', 'Speed Distribution'),
            specs=[["mapbox", "scatter"],
                   ["bar", "histogram"]]
        )
        
        # 1. Geographic scatter
        valid_coords = (
            (dashboard_data[lat_col] >= -90) & (dashboard_data[lat_col] <= 90) &
            (dashboard_data[lon_col] >= -180) & (dashboard_data[lon_col] <= 180) &
            dashboard_data[lat_col].notna() & dashboard_data[lon_col].notna()
        )
        
        valid_geo_data = dashboard_data[valid_coords]
        
        fig.add_trace(
            go.Scattermapbox(
                lat=valid_geo_data[lat_col],
                lon=valid_geo_data[lon_col],
                mode='markers',
                marker=dict(size=3, opacity=0.6),
                name='Vessel Positions'
            ),
            row=1, col=1
        )
        
        # 2. Temporal pattern
        if timestamp_col in dashboard_data.columns:
            dashboard_data[timestamp_col] = pd.to_datetime(dashboard_data[timestamp_col])
            daily_counts = dashboard_data[timestamp_col].dt.date.value_counts().sort_index()
            
            fig.add_trace(
                go.Scatter(
                    x=daily_counts.index,
                    y=daily_counts.values,
                    mode='lines',
                    name='Daily Records'
                ),
                row=1, col=2
            )
        
        # 3. Vessel activity
        if vessel_col in dashboard_data.columns:
            top_vessels = dashboard_data[vessel_col].value_counts().head(10)
            
            fig.add_trace(
                go.Bar(
                    x=top_vessels.index.astype(str),
                    y=top_vessels.values,
                    name='Top Vessels'
                ),
                row=2, col=1
            )
        
        # 4. Speed distribution
        if 'SOG' in dashboard_data.columns:
            speed_data = dashboard_data[(dashboard_data['SOG'] >= 0) & (dashboard_data['SOG'] <= 50)]
            
            fig.add_trace(
                go.Histogram(
                    x=speed_data['SOG'],
                    nbinsx=30,
                    name='Speed Distribution'
                ),
                row=2, col=2
            )
        
        # Update layout
        fig.update_layout(
            mapbox=dict(
                style='open-street-map',
                center=dict(
                    lat=valid_geo_data[lat_col].mean(),
                    lon=valid_geo_data[lon_col].mean()
                ),
                zoom=5
            ),
            height=800,
            title='AIS Data Interactive Dashboard'
        )
        
        return fig


def create_summary_report(df: pd.DataFrame, 
                        vessel_col: str = 'MMSI',
                        lat_col: str = 'LAT', 
                        lon_col: str = 'LON',
                        timestamp_col: str = 'BaseDateTime') -> Dict:
    """Generate a comprehensive summary report"""
    
    report = {
        'dataset_overview': {
            'total_records': len(df),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024,
            'columns': list(df.columns),
            'date_range': None,
            'geographic_bounds': None
        },
        'data_quality': {
            'missing_values': df.isnull().sum().to_dict(),
            'duplicate_records': df.duplicated().sum(),
            'valid_coordinates_pct': 0
        },
        'vessel_statistics': {
            'unique_vessels': 0,
            'avg_records_per_vessel': 0,
            'most_active_vessels': {}
        },
        'temporal_patterns': {
            'records_per_day': {},
            'peak_hours': {},
            'data_gaps': []
        }
    }
    
    # Temporal analysis
    if timestamp_col in df.columns:
        try:
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])
            report['dataset_overview']['date_range'] = {
                'start': df[timestamp_col].min(),
                'end': df[timestamp_col].max()
            }
            
            # Daily patterns
            daily_counts = df[timestamp_col].dt.date.value_counts().sort_index()
            report['temporal_patterns']['records_per_day'] = daily_counts.to_dict()
            
            # Hourly patterns
            hourly_counts = df[timestamp_col].dt.hour.value_counts().sort_index()
            report['temporal_patterns']['peak_hours'] = hourly_counts.to_dict()
            
        except Exception as e:
            logger.warning(f"Error in temporal analysis: {e}")
    
    # Vessel analysis
    if vessel_col in df.columns:
        report['vessel_statistics']['unique_vessels'] = df[vessel_col].nunique()
        report['vessel_statistics']['avg_records_per_vessel'] = len(df) / df[vessel_col].nunique()
        report['vessel_statistics']['most_active_vessels'] = df[vessel_col].value_counts().head(10).to_dict()
    
    # Geographic analysis
    if lat_col in df.columns and lon_col in df.columns:
        valid_coords = (
            (df[lat_col] >= -90) & (df[lat_col] <= 90) &
            (df[lon_col] >= -180) & (df[lon_col] <= 180) &
            df[lat_col].notna() & df[lon_col].notna()
        )
        
        valid_df = df[valid_coords]
        report['data_quality']['valid_coordinates_pct'] = len(valid_df) / len(df) * 100
        
        if len(valid_df) > 0:
            report['dataset_overview']['geographic_bounds'] = {
                'lat_min': valid_df[lat_col].min(),
                'lat_max': valid_df[lat_col].max(),
                'lon_min': valid_df[lon_col].min(),
                'lon_max': valid_df[lon_col].max(),
                'center_lat': valid_df[lat_col].mean(),
                'center_lon': valid_df[lon_col].mean()
            }
    
    return report

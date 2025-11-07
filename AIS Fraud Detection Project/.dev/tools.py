"""
Shipping Fraud Detection AI Agent Tools

[VERSION]
Event = Datathon 2025
Team = Dreadnaught
Author = Chris Matherne
version = 1.0 Beta
"""

import os
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
# Try multiple possible locations for BaseTool to handle LangChain's evolving structure
try:
    from langchain.tools import BaseTool, ToolException
except ImportError:
    try:
        from langchain_core.tools import BaseTool, ToolException
    except ImportError:
        from langchain.tools.base import BaseTool
        from langchain.tools.base import ToolException
import requests
from duckduckgo_search import DDGS
import folium
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class RunSFDInput(BaseModel):
    start_date: str = Field(description="Start date in YYYY-MM-DD format")
    end_date: str = Field(description="End date in YYYY-MM-DD format")
    output_directory: Optional[str] = Field(None, description="Directory to save output files")
    ship_types: Optional[str] = Field(None, description="Comma-separated list of ship types to analyze (e.g., '70,80')")
    
class RunSFDTool(BaseTool):
    name: str = "run_sfd"
    description: str = "Run the SFD.py script to detect shipping fraud in AIS data"
    args_schema: type[RunSFDInput] = RunSFDInput
    
    def _run(self, start_date: str, end_date: str, output_directory: Optional[str] = None, ship_types: Optional[str] = None) -> str:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        script_path = os.path.join(parent_dir, "SFD.py")
        
        cmd = ["python", script_path, "--start-date", start_date, "--end-date", end_date]
        
        if output_directory:
            cmd.extend(["--output-directory", output_directory])
        
        if ship_types:
            cmd.extend(["--ship-types", ship_types])
            
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return f"SFD.py executed successfully. Output saved to {output_directory or 'default directory'}."
            else:
                return f"Error running SFD.py: {result.stderr}"
        except Exception as e:
            return f"Error: {str(e)}"


class QuerySFDDataInput(BaseModel):
    file_path: str = Field(description="Path to the CSV file to query")
    query_type: str = Field(description="Type of query: 'filter', 'summary', 'columns', or 'head'")
    filter_column: Optional[str] = Field(None, description="Column to filter on (for 'filter' query type)")
    filter_value: Optional[str] = Field(None, description="Value to filter by (for 'filter' query type)")

class QuerySFDDataTool(BaseTool):
    name: str = "query_sfd_data"
    description: str = "Query data from SFD.py output files"
    args_schema: type[QuerySFDDataInput] = QuerySFDDataInput
    
    def _run(self, file_path: str, query_type: str, filter_column: Optional[str] = None, filter_value: Optional[str] = None) -> str:
        try:
            if not os.path.exists(file_path):
                return f"Error: File {file_path} not found"
            
            df = pd.read_csv(file_path)
            
            if query_type == "filter" and filter_column and filter_value:
                if filter_column not in df.columns:
                    return f"Error: Column '{filter_column}' not found in data"
                
                filtered_df = df[df[filter_column] == filter_value]
                return filtered_df.to_string()
                
            elif query_type == "summary":
                return df.describe().to_string()
                
            elif query_type == "columns":
                return ", ".join(df.columns.tolist())
                
            elif query_type == "head":
                return df.head(10).to_string()
                
            else:
                return "Invalid query_type. Use 'filter', 'summary', 'columns', or 'head'"
        
        except Exception as e:
            return f"Error querying data: {str(e)}"


class VesselLookupInput(BaseModel):
    mmsi: str = Field(description="MMSI number of the vessel to look up")

class VesselLookupTool(BaseTool):
    name: str = "vessel_lookup"
    description: str = "Look up vessel information online based on MMSI number"
    args_schema: type[VesselLookupInput] = VesselLookupInput
    
    def _run(self, mmsi: str) -> str:
        try:
            # Search for vessel info using DuckDuckGo
            with DDGS() as ddgs:
                query = f"maritime vessel MMSI {mmsi} information"
                results = list(ddgs.text(query, max_results=5))
            
            # Try to get info from MarineTraffic or similar sites
            # This is a simplified example - you might want to use specific maritime APIs
            vessel_info = self._search_vessel_databases(mmsi)
            
            if not results and not vessel_info:
                return f"No information found for vessel with MMSI {mmsi}"
            
            # Format the results
            response = f"## Information for vessel with MMSI {mmsi}\n\n"
            
            if vessel_info:
                response += "### Vessel Details\n"
                for key, value in vessel_info.items():
                    response += f"- **{key}**: {value}\n"
                response += "\n"
            
            if results:
                response += "### Web Search Results\n"
                for idx, result in enumerate(results, 1):
                    response += f"{idx}. [{result['title']}]({result['href']})\n   {result['body']}\n\n"
            
            return response
        
        except Exception as e:
            return f"Error looking up vessel information: {str(e)}"
    
    def _search_vessel_databases(self, mmsi: str) -> Dict[str, Any]:
        """
        Mock function to search maritime databases.
        In a real implementation, this would connect to actual maritime APIs.
        """
        # This is a placeholder - you would implement actual API calls here
        return {
            "MMSI": mmsi,
            "Vessel Type": "Unknown",
            "Flag": "Unknown",
            "MarineTraffic Link": f"https://www.marinetraffic.com/en/ais/details/ships/mmsi:{mmsi}",
            "VesselFinder Link": f"https://www.vesselfinder.com/vessels/details/{mmsi}"
        }


class GenerateChartInput(BaseModel):
    file_path: str = Field(description="Path to the CSV file to generate chart from")
    chart_type: str = Field(description="Type of chart: 'bar', 'line', 'scatter', 'heatmap', 'pie'")
    x_column: str = Field(description="Column to use for X-axis")
    y_column: Optional[str] = Field(None, description="Column to use for Y-axis (not needed for pie charts)")
    output_file: str = Field(description="Output file path for the chart (.png)")
    title: Optional[str] = Field(None, description="Chart title")

class GenerateChartTool(BaseTool):
    name: str = "generate_chart"
    description: str = "Create charts and visualizations from SFD.py data"
    args_schema: type[GenerateChartInput] = GenerateChartInput
    
    def _run(
        self, 
        file_path: str, 
        chart_type: str, 
        x_column: str, 
        output_file: str, 
        y_column: Optional[str] = None, 
        title: Optional[str] = None
    ) -> str:
        try:
            if not os.path.exists(file_path):
                return f"Error: File {file_path} not found"
            
            df = pd.read_csv(file_path)
            
            if x_column not in df.columns:
                return f"Error: Column '{x_column}' not found in data"
            
            if y_column and y_column not in df.columns:
                return f"Error: Column '{y_column}' not found in data"
            
            plt.figure(figsize=(12, 8))
            
            if chart_type == "bar":
                if not y_column:
                    return "Error: Y-axis column is required for bar charts"
                sns.barplot(x=df[x_column], y=df[y_column])
                
            elif chart_type == "line":
                if not y_column:
                    return "Error: Y-axis column is required for line charts"
                sns.lineplot(x=df[x_column], y=df[y_column])
                
            elif chart_type == "scatter":
                if not y_column:
                    return "Error: Y-axis column is required for scatter plots"
                sns.scatterplot(x=df[x_column], y=df[y_column])
                
            elif chart_type == "heatmap":
                if not y_column:
                    return "Error: Y-axis column is required for heatmaps"
                pivot_table = df.pivot_table(index=x_column, columns=y_column, aggfunc='size', fill_value=0)
                sns.heatmap(pivot_table, annot=True, cmap="YlGnBu")
                
            elif chart_type == "pie":
                df[x_column].value_counts().plot.pie(autopct='%1.1f%%')
                
            else:
                return "Invalid chart_type. Use 'bar', 'line', 'scatter', 'heatmap', or 'pie'"
            
            if title:
                plt.title(title)
                
            plt.tight_layout()
            plt.savefig(output_file)
            plt.close()
            
            return f"Chart successfully generated and saved to {output_file}"
            
        except Exception as e:
            return f"Error generating chart: {str(e)}"

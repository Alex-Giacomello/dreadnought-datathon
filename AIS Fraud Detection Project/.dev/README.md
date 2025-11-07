# SFD.py AI Agent

This AI agent integrates with SFD.py to analyze shipping data for potential fraud detection.

## Features

- Run SFD.py with custom parameters via command-line
- Query and analyze data from SFD.py output files
- Look up vessel information online using MMSI numbers
- Generate custom charts and visualizations from shipping data
- Uses Claude AI for natural language understanding and response generation

## Setup

1. Install the required dependencies:
   ```
   pip install -r AI_agent_requirements.txt
   ```

2. Add your Claude API key to the `AI_agent_Env.env` file:
   ```
   CLAUDE_API_KEY=your_claude_api_key_here
   ```

3. Run the agent:
   ```
   python AI_agent_main.py
   ```

## Example Queries

- "Run SFD.py analysis for October 15-20, 2024"
- "Show me a summary of anomalies detected in the latest report"
- "Look up information about vessel with MMSI 123456789"
- "Generate a bar chart showing anomaly types by date"
- "Find all cargo ships with speed anomalies and show their details"
- "Compare beacon on/off anomalies between October and November 2024"

## Files

- `AI_agent_main.py`: Main application file that initializes the AI agent
- `tools.py`: Contains tools for interacting with SFD.py, querying data, and generating visualizations
- `AI_agent_Env.env`: Environment file for API keys
- `AI_agent_requirements.txt`: Required Python packages

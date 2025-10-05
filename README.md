# Geo Spatial City Planning Agent

A comprehensive AI-powered city planning and analysis platform that combines real-time data collection with machine learning models to generate detailed urban planning insights and reports.

## Overview

This platform serves as an intelligent city planning assistant that can analyze urban environments, predict traffic patterns, assess air quality, optimize transit routes, and provide comprehensive planning recommendations. It integrates multiple data sources and AI models to deliver actionable insights for urban planners and decision-makers.

## Tech Stack

### Backend Framework
- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for running the FastAPI application
- **Python 3.11+**: Core programming language

### AI and Language Models
- **Cerebras Cloud SDK**: Integration with Cerebras AI models
- **OpenAI GPT-4**: Advanced language model for analysis
- **LangChain**: Framework for building applications with LLMs
- **LangChain Cerebras**: Cerebras-specific LangChain integration

### Data Processing and Analysis
- **Pydantic**: Data validation and serialization
- **TikToken**: Token counting and text processing
- **Python-dotenv**: Environment variable management

### Multi-Agent Framework
- **LangChain MCP Adapters**: Model Context Protocol integration
- **LangGraph**: Agent orchestration and workflow management
- **Loguru**: Advanced logging capabilities

### Data Sources Integration
- **DuckDuckGo Search**: Web search capabilities
- **Visual Crossing Weather API**: Weather data and forecasts
- **TomTom Traffic API**: Real-time traffic information
- **AQICN API**: Air quality index data
- **Google Data Commons**: Demographic and statistical data

### Document Processing
- **Markdown**: Report generation
- **WeasyPrint**: PDF generation capabilities
- **Pygments**: Syntax highlighting



## Project Structure

```
Geo-Spatial-City-Planning-Agent/
├── backend.py                 # Main FastAPI application
├── requirements.txt           # Python dependencies
├── .env                      # Environment variables (not in repo)
├── MCP/                      # Model Context Protocol components
│   ├── cerebras_client.py    # Cerebras AI client
│   ├── overall_main.py       # Main query processing pipeline
│   ├── prompts.json          # System prompts and templates
│   ├── mcp_servers.json      # MCP server configurations
│   └── MCP_token_summizer.py # Text summarization utility
├── frontend/                 # Web interface components
│   ├── report.html          # Report generation interface
│   └── app.py              # Alternative frontend application
└── City Planning ML Models MCP/ # ML models directory
    └── integrated_client.py  # ML integration client
```

## Installation and Setup

### Prerequisites
- Python 3.11 or higher
- UV package manager (recommended) or pip
- Required API keys (see Environment Variables section)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/itsbharatj/Geo-Spatial-AI-Agent-for-City-Planning.git
   cd Geo-Spatial-AI-Agent-for-City-Planning
   ```

2. **Install dependencies using UV (recommended)**
   ```bash
   uv sync
   ```
   
   Or using pip:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   CEREBRAS_API_KEY=your_cerebras_api_key
   OPENAI_API_KEY=your_openai_api_key
   TOMTOM_API_KEY=your_tomtom_api_key
   VISUAL_CROSSING_API_KEY=your_visual_crossing_api_key
   PROJECT_ROOT=/path/to/your/project
   ```

## Running the Application

### Start the Backend Server
```bash
uvicorn backend:app --reload
```

The server will start on `http://localhost:8000`

### Alternative: Run with UV
```bash
uv run uvicorn backend:app --reload
```

### Access the Application
- **API Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`
- **Report Generator**: Open `frontend/report.html` in your browser

## API Endpoints

### POST /plan
Generates comprehensive city planning reports using MCP agents.

**Request Body:**
```json
{
  "query": "Analyze traffic patterns and air quality in Delhi for urban planning"
}
```

**Response:** Markdown-formatted comprehensive report

### POST /api/city-data
Analyzes cities based on map coordinates and user queries.

**Request Body:**
```json
{
  "query": "Compare weather and air quality",
  "context": {
    "clickedPoints": [
      {"lat": 28.6139, "lng": 77.2090},
      {"lat": 40.7128, "lng": -74.0060}
    ],
    "mapView": "leaflet"
  }
}
```

**Response:** JSON with city data, charts, and analysis

### GET /health
Returns API health status and configuration.

### GET /
Returns API information and available endpoints.

## Sample Prompts and Queries

### Urban Planning Analysis
```
"Analyze the urban development potential of Mohali, India, including traffic infrastructure, air quality trends, and population growth projections"
```

### Comparative City Analysis
```
"Compare Delhi and Mumbai in terms of air quality, traffic congestion, and urban growth patterns for the next 5 years"
```

### Infrastructure Planning
```
"Evaluate the need for new public transit routes in Chandigarh based on population density and current traffic patterns"
```

### Environmental Impact Assessment
```
"Assess the environmental impact of proposed industrial development in Punjab, focusing on air quality and weather patterns"
```

### Traffic and Transportation
```
"Analyze current traffic flow patterns in Delhi and recommend optimization strategies for peak hours"
```

### Regional Development Planning
```
"Create a comprehensive development plan for smart city initiatives in Mohali, including energy demand forecasting and land use optimization"
```

## Features

### Multi-Source Data Integration
- Real-time weather and climate data
- Traffic flow and congestion information
- Air quality monitoring and forecasting
- Demographic and economic indicators
- Geographic and spatial data

### AI-Powered Analysis
- Query decomposition and sub-question generation
- Multi-agent processing pipeline
- Intelligent data synthesis and summarization
- Natural language report generation

### Comprehensive Reporting
- Markdown-formatted reports
- Executive summaries with key insights
- Actionable recommendations
- Data visualization integration
- Interactive map-based analysis

### Flexible Query Processing
- Natural language input processing
- Context-aware query understanding
- Multi-perspective analysis
- Real-time data integration

## Configuration

### MCP Servers Configuration
The `MCP/mcp_servers.json` file contains configurations for all data source integrations. Each server defines connection parameters, API keys, and data processing settings.

### Prompt Templates
The `MCP/prompts.json` file contains system prompts for:
- Query breakdown and decomposition
- Report generation guidelines
- Analysis structure templates

### Environment Variables
Required environment variables include API keys for various services:
- `CEREBRAS_API_KEY`: Cerebras Cloud API access
- `OPENAI_API_KEY`: OpenAI API access
- `TOMTOM_API_KEY`: TomTom mapping and traffic data
- `VISUAL_CROSSING_API_KEY`: Weather data access

## Development

### Running in Development Mode
```bash
uvicorn backend:app --reload --host 0.0.0.0 --port 8000
```

### Testing Individual Components
```bash
# Test MCP client directly
uv run -m MCP.overall_main

# Test specific modules
python MCP/cerebras_client.py
```

### Adding New Data Sources
1. Add configuration to `MCP/mcp_servers.json`
2. Update environment variables in `.env`
3. Modify query processing in `MCP/overall_main.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/itsbharatj/Geo-Spatial-AI-Agent-for-City-Planning) or open an issue.

## Version

Current Version: 1.0.0

Last Updated: October 2025
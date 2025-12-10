import asyncio
import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
# from openai import OpenAI
from pydantic import BaseModel

from MCP.overall_main import cityplanning_query_runner

load_dotenv()

app = FastAPI(title="Global City Planner API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini client
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
import google.generativeai as genai
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

SYSTEM_PROMPT = """You are an AI backend for a Global City Planner Dashboard. Your role is to:

1. Analyze clicked points on a world map (latitude, longitude coordinates)
2. Identify nearby cities, countries, and regions based on coordinates
3. Generate realistic data for identified cities (weather, air quality, population, etc.)
4. Respond to user queries about locations, comparisons, and analysis
5. Provide contextual insights based on clicked points and queries
6. Handle "where is X located" queries by providing coordinates and creating markers

**CRITICAL: You MUST respond with ONLY valid JSON. No markdown, no code blocks, no explanations.**

**JSON Structure:**
{
  "cities": {
    "<city_key>": {
      "lat": <number>,
      "lng": <number>,
      "name": "<City Name>",
      "country": "<Country>",
      "region": "<Region/State>",
      "population": <number>,
      "aqi": <number 0-500>,
      "temp": <number in celsius>,
      "humidity": <number 0-100>,
      "weather": "<condition>",
      "timezone": "<timezone>",
      "elevation": <number in meters>
    }
  },
  "response": "<natural language response to user query>",
  "updateCharts": ["temperature", "aqi", "population"],
  "switchMapView": "leaflet" or "deckgl",
  "enableLayers": ["column", "hexagon", "scatterplot"],
  "aqiData": [
    {"location": "<city>", "aqi": <number>, "category": "<category>"}
  ],
  "temperatureData": [
    {"time": "HH:MM", "temp": <number>, "humidity": <number>}
  ],
  "highlightCities": ["<city_key>"],
  "addMarkers": [
    {"lat": <number>, "lng": <number>, "label": "<text>", "color": "<color>"}
  ],
  "autoAddPoints": [
    {"lat": <number>, "lng": <number>}
  ]
}

**Guidelines:**
- Analyze clicked point coordinates to determine nearby cities
- Use reverse geocoding knowledge to identify cities near coordinates
- Generate realistic data based on:
  * Geographic location (climate zones, typical weather)
  * City size and development level
  * Current season (it's October 2025)
  * Regional air quality patterns
- When no points are clicked, provide general world data or ask user to click points
- When points are clicked, identify the nearest major city to each point
- Include cities within ~100km of clicked points
- Provide comparisons when multiple points from different regions
- Use city names as keys (lowercase, no spaces: "new_york", "tokyo", "london")
- Always respond with helpful, accurate information
- If coordinates are in ocean/remote areas, mention nearest land/city

**LOCATION QUERIES (WHERE IS X LOCATED):**
When user asks "where is Punjab located", "show me Tokyo", "find Paris", etc:
1. Identify the location's coordinates
2. Add to "autoAddPoints" array - this will automatically place a red marker on the map
3. Create a city entry for that location
4. Add a custom marker with the location name using "addMarkers"
5. Provide informative response about the location

Example for "where is Punjab located":
{
  "cities": {
    "punjab_india": {
      "lat": 31.1471,
      "lng": 75.3412,
      "name": "Punjab",
      "country": "India",
      "region": "Northern India",
      "population": 27704236,
      ...
    }
  },
  "autoAddPoints": [
    {"lat": 31.1471, "lng": 75.3412}
  ],
  "addMarkers": [
    {"lat": 31.1471, "lng": 75.3412, "label": "Punjab, India", "color": "#10b981"}
  ],
  "response": "Punjab is located in northern India, at coordinates 31.15°N, 75.34°E. It borders Pakistan to the west..."
}

**AQI Categories:**
- 0-50: Good
- 51-100: Moderate
- 101-150: Unhealthy for Sensitive Groups
- 151-200: Unhealthy
- 201-300: Very Unhealthy
- 301+: Hazardous

**Example Scenarios:**

User clicks near Tokyo (35.6762, 139.6503) and asks "What's the weather here?"
→ Identify Tokyo, provide weather data, mention it's in Japan

User clicks multiple points across continents and asks "Compare these locations"
→ Identify nearest city to each point, compare weather/AQI/population

User asks "where is London located" (no points clicked)
→ Return autoAddPoints with London coordinates, add marker, create city entry

User clicks in Atlantic Ocean
→ Mention it's in the ocean, identify nearest coastal city

**Response Rules:**
1. ONLY output valid JSON
2. NO markdown formatting
3. NO code blocks (```json)
4. NO extra text before or after JSON
5. Ensure all JSON is properly formatted"""


class QueryRequest(BaseModel):
    query: str


class CityDataRequest(BaseModel):
    query: str
    context: Dict[str, Any]


@app.post("/plan")
async def plan_city(request: QueryRequest):
    """Generate comprehensive city planning report using MCP agents"""
    agent = cityplanning_query_runner(request.query)
    await agent.main_runner()
    report_path = "report.md"
    if os.path.exists(report_path):
        with open(report_path, "r") as f:
            markdown_content = f.read()
        return Response(content=markdown_content, media_type="text/markdown")
    else:
        return Response(content="Report not found.", status_code=404)


@app.post("/api/city-data")
async def analyze_city_data(request: CityDataRequest):
    """
    Main endpoint that processes user queries with clicked point context.
    Uses OpenAI to analyze coordinates and generate relevant city data.
    """
    print("============================")
    print(request)
    print("============================")
    
    try:
        clicked_points = request.context.get("clickedPoints", [])
        
        # Build context for OpenAI
        context_parts = [f"User Query: {request.query}\n"]
        
        if clicked_points:
            context_parts.append(f"\nClicked Points ({len(clicked_points)} total):")
            for i, point in enumerate(clicked_points, 1):
                context_parts.append(f"  Point {i}: Latitude {point['lat']:.4f}, Longitude {point['lng']:.4f}")
        else:
            context_parts.append("\nNo points clicked yet.")
        
        context_parts.append(f"\nCurrent Map View: {request.context.get('mapView', 'leaflet')}")
        context_parts.append(f"Active Layers: {json.dumps(request.context.get('activeLayers', {}))}")
        
        context_str = "\n".join(context_parts)
        
        # Call Gemini API
        chat = model.start_chat()
        response = chat.send_message(
            SYSTEM_PROMPT + "\n\n" + context_str
        )
        
        # Extract and parse response
        try:
            response_text = response.text.strip()
        except:
            # Fallback for blocked responses or safety violations
            response_text = "{}"
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])
        
        # Parse JSON
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            print(f"Response: {response_text[:500]}")
            raise HTTPException(
                status_code=500,
                detail=f"AI returned invalid JSON: {str(e)}"
            )
        
        return data
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Global City Planner API is running",
        "model": "gemini-2.5-flash"
    }


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "Global City Planner API",
        "version": "1.0.0",
        "description": "AI-powered city planning and analysis for any location worldwide",
        "endpoints": {
            "POST /plan": "Generate comprehensive city planning reports",
            "POST /api/city-data": "Analyze cities based on clicked points and queries",
            "GET /health": "Health check"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
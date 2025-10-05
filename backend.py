from fastapi import FastAPI, UploadFile, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncio
import os

from MCP.overall_main import cityplanning_query_runner

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

@app.post("/plan")
async def plan_city(request: QueryRequest):
    agent = cityplanning_query_runner(request.query)
    await agent.main_runner()
    # Assuming report.md is generated in the current working directory
    report_path = "report.md"
    if os.path.exists(report_path):
        return FileResponse(report_path, media_type="text/markdown", filename="report.md")
    else:
        return Response(content="Report not found.", status_code=404)
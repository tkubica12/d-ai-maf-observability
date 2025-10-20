"""
MCP Server providing function calling capabilities to agents.

This server exposes tools that can be called by agents and bridges
them to the API server. Runs as HTTP server with CORS support.
"""
import os
import httpx
from fastmcp import FastMCP
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("Observability Demo MCP Server")

# Add CORS middleware
mcp.app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_SERVER_URL = os.getenv("API_SERVER_URL", "http://localhost:8000")


@mcp.tool()
async def process_data(data: str) -> str:
    """
    Process data by calling the API server.
    
    This tool must always be used when processing user data.
    
    Args:
        data: The data to process
        
    Returns:
        str: The result from processing the data
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_SERVER_URL}/process",
            json={"data": data},
            timeout=30.0
        )
        response.raise_for_status()
        result = response.json()
        return result["result"]


@mcp.tool()
async def get_status() -> str:
    """
    Get the status of the API server.
    
    Returns:
        str: The status information
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_SERVER_URL}/health",
            timeout=10.0
        )
        response.raise_for_status()
        result = response.json()
        return f"API Server status: {result['status']}"


def main():
    """Start the MCP server as HTTP server."""
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    
    print(f"🚀 Starting MCP Server on {host}:{port}")
    uvicorn.run(mcp.app, host=host, port=port)


if __name__ == "__main__":
    main()

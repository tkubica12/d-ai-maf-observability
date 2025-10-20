"""
API Server that receives function calls from MCP server.

This server provides a simple API endpoint that can be called through
function calling from the MCP server.
"""
import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="API Server", version="0.1.0")


class ProcessDataRequest(BaseModel):
    """Request model for processing data."""
    data: str


class ProcessDataResponse(BaseModel):
    """Response model for processing data."""
    result: str
    message: str


@app.get("/")
async def root():
    """Root endpoint returning service information."""
    return {
        "service": "API Server",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/process", response_model=ProcessDataResponse)
async def process_data(request: ProcessDataRequest):
    """
    Process data received from MCP function call.
    
    Args:
        request: The data to process
        
    Returns:
        ProcessDataResponse with the result
    """
    result = f"Processed: {request.data}"
    return ProcessDataResponse(
        result=result,
        message="Data processed successfully"
    )


def main():
    """Start the API server."""
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()

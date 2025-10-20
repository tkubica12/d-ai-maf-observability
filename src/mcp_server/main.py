"""
MCP Server providing function calling capabilities to agents.

This server exposes tools that can be called by agents.
"""
import os
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("Observability Demo MCP Server")

# Static stock data for products
PRODUCT_STOCK = {
    "LAPTOP001": 15,
    "PHONE002": 32,
    "TABLET003": 8,
    "HEADSET004": 45,
    "MONITOR005": 12,
    "KEYBOARD006": 28,
    "MOUSE007": 67,
    "SPEAKER008": 19,
}


@mcp.tool()
async def get_product_stock(product_id: str) -> dict:
    """
    Get the current stock level for a specific product.
    
    Args:
        product_id: The unique identifier of the product
        
    Returns:
        dict: Stock information including product_id and stock_count
    """
    stock_count = PRODUCT_STOCK.get(product_id, 0)
    return {
        "product_id": product_id,
        "stock_count": stock_count,
        "available": stock_count > 0
    }


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
    # Removed API server dependency to keep MCP minimal
    return f"MCP processed: {data}"


@mcp.tool()
async def get_status() -> str:
    """
    Get the status of the MCP server.
    
    Returns:
        str: The status information
    """
    return "MCP Server status: healthy"


def main():
    """Run the server in HTTP transport with configured host/port."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    
    print(f"🚀 Starting MCP Server on {host}:{port}")
    print(f"Health endpoint: http://{host}:{port}/health")
    print(f"MCP endpoint: http://{host}:{port}/mcp/")
    
    # Use mcp.run() with HTTP transport
    mcp.run(transport="http", host=host, port=port)


if __name__ == "__main__":
    main()

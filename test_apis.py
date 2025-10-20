#!/usr/bin/env python3
"""
Quick test script to validate API and MCP server functionality.
"""
import asyncio
import json
import httpx

async def test_api_server():
    """Test the API server endpoints."""
    print("🧪 Testing API Server...")
    
    async with httpx.AsyncClient() as client:
        # Test root endpoint
        response = await client.get("http://localhost:8000/")
        print(f"Root endpoint: {response.status_code} - {response.json()}")
        
        # Test health endpoint
        response = await client.get("http://localhost:8000/health")
        print(f"Health endpoint: {response.status_code} - {response.json()}")
        
        # Test product of the day endpoint
        response = await client.get("http://localhost:8000/product-of-the-day")
        print(f"Product of the day: {response.status_code} - {response.json()}")
        
        # Test it multiple times to see randomness
        print("\nTesting randomness (3 more calls):")
        for i in range(3):
            response = await client.get("http://localhost:8000/product-of-the-day")
            product = response.json()
            print(f"  {i+1}: {product['product_id']} - {product['product_description']}")

async def test_mcp_server():
    """Test the MCP server tools."""
    print("\n🔧 Testing MCP Server...")
    
    async with httpx.AsyncClient() as client:
        # Test get_product_stock for different products
        test_products = ["LAPTOP001", "PHONE002", "INVALID_ID"]
        
        for product_id in test_products:
            # This is a simplified test - in reality MCP tools are called differently
            # but we can test the function directly
            from src.mcp_server.main import get_product_stock
            result = await get_product_stock(product_id)
            print(f"Stock for {product_id}: {result}")

async def main():
    """Run all tests."""
    try:
        await test_api_server()
        await test_mcp_server()
        print("\n✅ All tests completed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
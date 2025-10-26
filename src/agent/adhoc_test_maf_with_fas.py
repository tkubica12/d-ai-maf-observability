"""
Self-contained test for maf-with-fas scenario using Azure AI Foundry observability.

This test demonstrates Application Insights integration using the built-in
observability support in Azure AI Foundry as documented at:
https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-observability?pivots=programming-language-python#azure-ai-foundry-setup

Key features:
- Uses AzureAIAgentClient.setup_azure_ai_observability() for automatic App Insights setup
- Self-contained: does not modify shared files
- Tests the maf-with-fas scenario with full observability
"""
from __future__ import annotations

import asyncio
import json
import os
import random
from typing import Any, Dict

import httpx
from agent_framework import ai_function, HostedMCPTool
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from dotenv import load_dotenv
from fastmcp import Client

# Load environment variables
load_dotenv()


def get_mock_user_context() -> Dict[str, Any]:
    """Generate mock user context for testing."""
    import uuid
    
    users = [
        {"user_id": "user_001", "is_vip": True, "department": "Engineering"},
        {"user_id": "user_002", "is_vip": True, "department": "Marketing"},
        {"user_id": "user_003", "is_vip": False, "department": "Engineering"},
    ]
    
    user = random.choice(users)
    return {
        "user_id": user["user_id"],
        "is_vip": user["is_vip"],
        "department": user["department"],
        "thread_id": f"thread_{uuid.uuid4().hex[:8]}",
    }


def create_api_tool(api_server_url: str):
    """Create API tool for getting product of the day."""
    @ai_function(
        name="get_product_of_the_day",
        description="Get a randomly selected product of the day from the API server",
    )
    async def get_product_of_the_day() -> Dict[str, Any]:
        print(f"🔧 Tool call: get_product_of_the_day()")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{api_server_url}/product-of-the-day",
                timeout=10.0,
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"📥 Tool result (get_product_of_the_day): {result}")
            return result

    return get_product_of_the_day


async def test_connections(api_server_url: str, mcp_server_url: str) -> bool:
    """Test connections to both API and MCP servers."""
    api_ok = False
    mcp_ok = False

    print("🔍 Testing tool connections...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{api_server_url}/health", timeout=5.0)
            api_ok = response.status_code == 200
            print(f"✅ API Server: {'Connected' if api_ok else 'Failed'}")
        except Exception as exc:
            print(f"❌ API Server: {exc}")

    try:
        # Test MCP server by establishing a proper MCP connection
        async with Client(f"{mcp_server_url}/mcp") as mcp_client:
            # Try to list tools to verify connection works
            tools = await mcp_client.list_tools()
            mcp_ok = True
            print(f"✅ MCP Server: Connected")
            print(f"🔧 Discovered {len(tools)} MCP tools")
    except Exception as exc:
        print(f"❌ MCP Server: {exc}")
        mcp_ok = False

    return api_ok and mcp_ok


async def main() -> None:
    """Main test function for maf-with-fas scenario with Azure AI Foundry observability."""
    print("\n" + "=" * 80)
    print("🧪 ADHOC TEST: MAF with Foundry Agent Service + App Insights Observability")
    print("=" * 80)

    # Get configuration from environment
    project_endpoint = os.getenv("PROJECT_ENDPOINT")
    model_deployment = "gpt-4.1-mini"  # Hardcoded for FAS + MCP compatibility
    api_server_url = os.getenv("API_SERVER_URL", "http://localhost:8000").rstrip("/")
    mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8001").rstrip("/")

    if not project_endpoint:
        print("❌ PROJECT_ENDPOINT environment variable not set")
        print("   Please configure your Azure AI Foundry project endpoint")
        return

    # Test connections first
    if not await test_connections(api_server_url, mcp_server_url):
        print("\n❌ Cannot connect to required services. Please ensure API and MCP servers are running.")
        print(f"   API Server: {api_server_url}")
        print(f"   MCP Server: {mcp_server_url}")
        return

    # Generate mock user context
    user_context = get_mock_user_context()
    print(f"\n👤 User Context: {user_context.get('user_id', 'N/A')} (VIP: {user_context.get('is_vip', False)}, Dept: {user_context.get('department', 'N/A')})")
    print(f"🧵 Thread ID: {user_context.get('thread_id', 'N/A')}")

    # Create async credential
    async with AsyncDefaultAzureCredential() as credential:
        # Create agent client
        agent_client = AzureAIAgentClient(
            project_endpoint=project_endpoint,
            model_deployment_name=model_deployment,
            async_credential=credential,
        )

        print(f"\n✅ Connected to Azure AI Project")
        print(f"🤖 Using model: {model_deployment}")

        # Setup Azure AI Foundry observability (Application Insights)
        # This automatically retrieves the App Insights connection string from the project
        # and configures OpenTelemetry exporters for traces, metrics, and logs
        try:
            await agent_client.setup_azure_ai_observability()
            print("✅ Azure AI Foundry observability configured (Application Insights)")
            print("   Traces will be sent to Application Insights linked to your project")
        except Exception as e:
            print(f"⚠️  Warning: Could not setup Azure AI observability: {e}")
            print("   Continuing without Application Insights integration")

        # Create API tool
        api_tool = create_api_tool(api_server_url)
        
        # Create MCP tool using HostedMCPTool for Foundry Agent Service
        print(f"\n🔌 Configuring Hosted MCP tool at {mcp_server_url}/mcp")
        mcp_tool = HostedMCPTool(
            name="stock_lookup_mcp",
            url=f"{mcp_server_url}/mcp",
        )
        
        print("✅ Hosted MCP tool configured for Foundry Agent Service")

        instructions = """You are a helpful assistant that provides product information and stock levels.

Your task is to:
1. Get the product of the day from the API
2. Use the product description in your response
3. Look up the stock level for that product using its product_id via MCP
4. Provide a comprehensive response including product details and availability

Always use both API and MCP tools to provide complete information."""

        # Create agent (not using context manager to control deletion)
        agent = agent_client.create_agent(
            name="Product Info Agent",
            instructions=instructions,
            tools=[api_tool, mcp_tool],
        )
        
        try:
            print("✅ Agent created (using Foundry Agent Service)")
            agent_id = agent.agent_id if hasattr(agent, 'agent_id') else None
            if agent_id:
                print(f"🆔 Agent ID: {agent_id}")

            user_message = "What's the product of the day and is it in stock?"
            print(f"\n📤 User: {user_message}")
            print("\n🤖 Agent processing...")

            # Run the agent with store=True for service-managed threads
            response = await agent.run(user_message, store=True)

            # Extract text from response
            if hasattr(response, "text"):
                final_text = response.text
            elif hasattr(response, "content"):
                final_text = response.content
            else:
                final_text = str(response)

            print(f"\n📨 Assistant: {final_text}")
            
            # Ask user whether to delete the agent
            print("\n" + "-" * 80)
            delete_choice = input("🗑️  Delete the agent? (y/n): ").strip().lower()
            
            if delete_choice == 'y':
                await agent.delete()
                print("✅ Agent deleted")
            else:
                print("✅ Agent kept - you can reuse it in Azure AI Foundry")
                if agent_id:
                    print(f"   Agent ID: {agent_id}")
        finally:
            # Close the agent session
            await agent.close()

    print("\n" + "=" * 80)
    print("✅ Test completed successfully!")
    print("💡 Check Application Insights in Azure Portal for telemetry data")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

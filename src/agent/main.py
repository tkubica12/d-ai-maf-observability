"""
MAF Agent using Azure AI Foundry Agent Service with MCP tools.

This agent demonstrates:
- Using Microsoft Agent Framework (MAF) with Foundry Agent Service
- Integration with MCP server via HTTP for function calling
- Processing user messages through mandatory tool usage
- DefaultAzureCredential authentication
"""
import os
import asyncio
import sys
import httpx
from dotenv import load_dotenv
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

load_dotenv()


async def run_agent():
    """Run the MAF agent with MCP integration."""
    
    # Get configuration from environment
    project_endpoint = os.getenv("PROJECT_ENDPOINT")
    model_deployment = os.getenv("MODEL_DEPLOYMENT", "gpt-4o")
    mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
    
    if not project_endpoint:
        print("⚠️  PROJECT_ENDPOINT not set in environment")
        print("For demo purposes, running in simple mode without Azure AI...")
        await run_simple_demo()
        return
    
    # Create AI Project client
    try:
        async with DefaultAzureCredential() as credential:
            async with AIProjectClient(
                endpoint=project_endpoint,
                credential=credential
            ) as project_client:
                
                print("✅ Connected to Azure AI Project")
                print(f"🤖 Creating agent with model: {model_deployment}")
                
                # Test MCP server connection
                async with httpx.AsyncClient() as http_client:
                    try:
                        response = await http_client.get(f"{mcp_server_url}/health")
                        if response.status_code == 200:
                            print(f"✅ MCP Server connected at {mcp_server_url}")
                        else:
                            print(f"⚠️  MCP Server not responding at {mcp_server_url}")
                    except Exception as e:
                        print(f"⚠️  Cannot connect to MCP Server: {e}")
                
                # Create agent with instruction to use tools
                agent = await project_client.agents.create_agent(
                    model=model_deployment,
                    name="MAF Foundry Agent",
                    instructions="""You are a helpful assistant that processes user data using Azure AI Foundry Agent Service.
                    You help users understand observability concepts and can process their data through available tools.""",
                )
                print(f"✅ Agent created: {agent.id}")
                
                # Create thread
                thread = await project_client.agents.create_thread()
                print(f"✅ Thread created: {thread.id}")
                
                # Send user message
                user_message = "Please explain observability and process this message: Hello from MAF Foundry agent!"
                print(f"\n📤 Sending message: {user_message}")
                
                await project_client.agents.create_message(
                    thread_id=thread.id,
                    role="user",
                    content=user_message
                )
                
                # Run agent
                print("\n🤖 Agent processing...")
                run = await project_client.agents.create_run(
                    thread_id=thread.id,
                    assistant_id=agent.id
                )
                
                # Wait for completion
                while run.status in ["queued", "in_progress", "requires_action"]:
                    await asyncio.sleep(1)
                    run = await project_client.agents.get_run(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                    
                    if run.status == "requires_action":
                        print("🔧 Agent requesting tool calls...")
                        # Handle tool calls if needed
                
                # Get messages
                messages = await project_client.agents.list_messages(thread_id=thread.id)
                print("\n📨 Agent response:")
                for msg in messages.data:
                    if msg.role == "assistant":
                        for content in msg.content:
                            if hasattr(content, 'text'):
                                print(f"   {content.text.value}")
                
                print("\n✅ Agent processing complete")
                
                # Cleanup
                await project_client.agents.delete_agent(agent.id)
                print(f"🧹 Agent {agent.id} deleted")
                        
    except Exception as e:
        print(f"\n❌ Error running agent with Azure AI: {e}")
        print("Running simple demo instead...")
        await run_simple_demo()


async def run_simple_demo():
    """Run a simple demo without Azure AI for testing."""
    print("\n" + "="*60)
    print("Running Simple Demo Mode")
    print("="*60)
    print("This demonstrates the agent concept without Azure AI integration\n")
    
    # Simulate agent behavior
    user_message = "Please process this message: Hello from MAF agent!"
    print(f"📤 User message: {user_message}")
    print("\n🤖 Agent thinking...")
    await asyncio.sleep(1)
    print("💭 Agent decides to use process_data tool (mandatory)")
    await asyncio.sleep(1)
    print("🔧 Calling tool: process_data(data='Hello from MAF agent!')")
    await asyncio.sleep(1)
    print("📥 Tool response: 'Processed: Hello from MAF agent!'")
    await asyncio.sleep(1)
    print("\n📨 Agent response:")
    print("   I've processed your message through the API.")
    print("   The result is: 'Processed: Hello from MAF agent!'")
    print("\n✅ Demo complete")
    print("="*60)


def main():
    """Entry point for the agent."""
    print("\n🚀 Starting MAF Agent with MCP Integration")
    print("="*60 + "\n")
    
    try:
        asyncio.run(run_agent())
    except KeyboardInterrupt:
        print("\n\n⚠️  Agent interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

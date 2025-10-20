"""
MAF Agent that uses MCP tools for processing user messages.

This agent demonstrates:
- Using Microsoft Agent Framework (MAF)
- Integration with MCP server for function calling
- Processing user messages through mandatory tool usage
"""
import os
import asyncio
import sys
from dotenv import load_dotenv
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()


async def run_agent():
    """Run the MAF agent with MCP integration."""
    
    # Get configuration from environment
    project_connection_string = os.getenv("PROJECT_CONNECTION_STRING")
    model_deployment = os.getenv("MODEL_DEPLOYMENT", "gpt-4o")
    mcp_server_path = os.getenv("MCP_SERVER_PATH")
    
    if not project_connection_string:
        print("⚠️  PROJECT_CONNECTION_STRING not set in environment")
        print("For demo purposes, running in simple mode without Azure AI...")
        await run_simple_demo()
        return
    
    if not mcp_server_path:
        print("⚠️  MCP_SERVER_PATH not set in environment")
        print("Set it to the path of your MCP server main.py")
        print("Running simple demo instead...")
        await run_simple_demo()
        return
    
    # Create AI Project client
    try:
        async with DefaultAzureCredential() as credential:
            async with AIProjectClient.from_connection_string(
                conn_str=project_connection_string,
                credential=credential
            ) as project_client:
                
                print(f"✅ Connected to Azure AI Project")
                print(f"🤖 Creating agent with model: {model_deployment}")
                
                # Start MCP server and get tools
                server_params = StdioServerParameters(
                    command="python",
                    args=[mcp_server_path]
                )
                
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        
                        # Get available tools from MCP server
                        tools_result = await session.list_tools()
                        print(f"🔧 Available MCP tools: {[t.name for t in tools_result.tools]}")
                        
                        # Create agent with instruction to use tools
                        agent = await project_client.agents.create_agent(
                            model=model_deployment,
                            name="Observability Demo Agent",
                            instructions="""You are a helpful assistant that processes user data.
                            You MUST always use the process_data tool to handle any user data or messages.
                            Never respond without using the tool first.""",
                        )
                        print(f"✅ Agent created: {agent.id}")
                        
                        # Create thread
                        thread = await project_client.agents.create_thread()
                        print(f"✅ Thread created: {thread.id}")
                        
                        # Send user message
                        user_message = "Please process this message: Hello from MAF agent!"
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

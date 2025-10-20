"""
MAF Agent using direct LLM access with MCP tools.

This agent demonstrates:
- Using Microsoft Agent Framework (MAF) with direct model access
- Integration with MCP server via HTTP for function calling
- Processing user messages through mandatory tool usage
- DefaultAzureCredential authentication
- Direct ChatCompletionsClient access to Azure AI models
"""
import os
import asyncio
import sys
import httpx
import json
from dotenv import load_dotenv
from azure.ai.inference.aio import ChatCompletionsClient
from azure.identity.aio import DefaultAzureCredential

load_dotenv()


async def get_mcp_tools(mcp_server_url: str) -> list:
    """Get available tools from MCP server."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{mcp_server_url}/tools")
            if response.status_code == 200:
                tools_data = response.json()
                return tools_data.get("tools", [])
            else:
                print(f"⚠️  Failed to get tools from MCP server: {response.status_code}")
                return []
    except Exception as e:
        print(f"⚠️  Error getting tools from MCP server: {e}")
        return []


async def call_mcp_tool(mcp_server_url: str, tool_name: str, arguments: dict) -> str:
    """Call a tool on the MCP server."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{mcp_server_url}/tools/{tool_name}",
                json={"arguments": arguments},
                timeout=30.0
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("result", "No result returned")
            else:
                return f"Error calling tool: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error calling tool: {e}"


async def run_direct_agent():
    """Run the MAF agent with direct LLM access."""
    
    # Get configuration from environment
    ai_endpoint = os.getenv("AI_ENDPOINT")  # e.g., https://resource.services.ai.azure.com/models
    model_name = os.getenv("MODEL_NAME", "gpt-4o")
    mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
    
    if not ai_endpoint:
        print("⚠️  AI_ENDPOINT not set in environment")
        print("For demo purposes, running in simple mode without Azure AI...")
        await run_simple_demo()
        return
    
    # Create AI client with direct model access
    try:
        async with DefaultAzureCredential() as credential:
            client = ChatCompletionsClient(
                endpoint=ai_endpoint,
                credential=credential,
                credential_scopes=["https://cognitiveservices.azure.com/.default"],
            )
            
            print("✅ Connected to Azure AI Models directly")
            print(f"🤖 Using model: {model_name}")
            
            # Test MCP server connection and get tools
            async with httpx.AsyncClient() as http_client:
                try:
                    response = await http_client.get(f"{mcp_server_url}/health")
                    if response.status_code == 200:
                        print(f"✅ MCP Server connected at {mcp_server_url}")
                    else:
                        print(f"⚠️  MCP Server not responding at {mcp_server_url}")
                except Exception as e:
                    print(f"⚠️  Cannot connect to MCP Server: {e}")
            
            # Get available tools
            available_tools = await get_mcp_tools(mcp_server_url)
            print(f"🔧 Available MCP tools: {[tool.get('name', 'unknown') for tool in available_tools]}")
            
            # Create system message with tool information
            system_message = """You are a helpful assistant that processes user data using direct Azure AI model access.
            You help users understand observability concepts and can process their data through available tools.
            
            You have access to MCP tools that you can call to process data. When you need to process user data,
            you should call the appropriate tool.
            
            Available tools: process_data, get_status
            
            When calling tools, respond with the tool call in this JSON format:
            {"tool_call": {"name": "tool_name", "arguments": {"arg1": "value1"}}}
            """
            
            # Prepare messages
            user_message = "Please explain observability and process this message: Hello from MAF Direct agent!"
            print(f"\n📤 Sending message: {user_message}")
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]
            
            # Call the model
            print("\n🤖 Agent processing...")
            response = await client.complete(
                model=model_name,
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            assistant_response = response.choices[0].message.content
            print("\n📨 Agent response:")
            print(f"   {assistant_response}")
            
            # Check if the response contains a tool call
            if "tool_call" in assistant_response:
                try:
                    # Extract tool call from response
                    start_idx = assistant_response.find('{"tool_call"')
                    if start_idx != -1:
                        end_idx = assistant_response.find('}', start_idx)
                        if end_idx != -1:
                            # Find the complete JSON object
                            brace_count = 0
                            for i in range(start_idx, len(assistant_response)):
                                if assistant_response[i] == '{':
                                    brace_count += 1
                                elif assistant_response[i] == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        end_idx = i
                                        break
                            
                            tool_call_json = assistant_response[start_idx:end_idx+1]
                            tool_call_data = json.loads(tool_call_json)
                            
                            tool_name = tool_call_data["tool_call"]["name"]
                            tool_args = tool_call_data["tool_call"]["arguments"]
                            
                            print(f"🔧 Calling tool: {tool_name} with args: {tool_args}")
                            
                            # Call the tool
                            tool_result = await call_mcp_tool(mcp_server_url, tool_name, tool_args)
                            print(f"📥 Tool result: {tool_result}")
                            
                            # Continue conversation with tool result
                            messages.append({"role": "assistant", "content": assistant_response})
                            messages.append({"role": "user", "content": f"Tool result: {tool_result}. Please provide a final response."})
                            
                            final_response = await client.complete(
                                model=model_name,
                                messages=messages,
                                max_tokens=500,
                                temperature=0.7
                            )
                            
                            print("\n📨 Final agent response:")
                            print(f"   {final_response.choices[0].message.content}")
                            
                except Exception as e:
                    print(f"⚠️  Error processing tool call: {e}")
            
            print("\n✅ Direct agent processing complete")
            
    except Exception as e:
        print(f"\n❌ Error running direct agent with Azure AI: {e}")
        print("Running simple demo instead...")
        await run_simple_demo()


async def run_simple_demo():
    """Run a simple demo without Azure AI for testing."""
    print("\n" + "="*60)
    print("Running Simple Demo Mode - Direct Agent")
    print("="*60)
    print("This demonstrates the direct agent concept without Azure AI integration\n")
    
    # Simulate agent behavior
    user_message = "Please explain observability and process this message: Hello from MAF Direct agent!"
    print(f"📤 User message: {user_message}")
    print("\n🤖 Agent thinking...")
    await asyncio.sleep(1)
    print("💭 Agent explains observability concepts")
    await asyncio.sleep(1)
    print("💭 Agent decides to use process_data tool")
    await asyncio.sleep(1)
    print("🔧 Calling tool: process_data(data='Hello from MAF Direct agent!')")
    await asyncio.sleep(1)
    print("📥 Tool response: 'Processed: Hello from MAF Direct agent!'")
    await asyncio.sleep(1)
    print("\n📨 Agent response:")
    print("   Observability is the ability to measure the internal states of a system")
    print("   by examining its outputs. It includes metrics, logs, and traces.")
    print("   I've processed your message through the direct API connection.")
    print("   The result is: 'Processed: Hello from MAF Direct agent!'")
    print("\n✅ Demo complete")
    print("="*60)


def main():
    """Entry point for the direct agent."""
    print("\n🚀 Starting MAF Direct Agent with MCP Integration")
    print("="*60 + "\n")
    
    try:
        asyncio.run(run_direct_agent())
    except KeyboardInterrupt:
        print("\n\n⚠️  Agent interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
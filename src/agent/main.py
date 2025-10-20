"""
Unified MAF Agent demonstrating two approaches:
1. Direct LLM calls with function calling for API tools and MCP integration
2. Foundry Agent Service with registered agent lifecycle

This agent demonstrates:
- API function calling to get product of the day
- MCP tool integration for stock lookup
- Sequential testing of both approaches
- Network-based tool integration
"""
import os
import asyncio
import sys
import httpx
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from azure.ai.inference.aio import ChatCompletionsClient
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from fastmcp import Client

load_dotenv()


class ToolRegistry:
    """Registry for managing both API and MCP tools."""
    
    def __init__(self, api_server_url: str, mcp_server_url: str):
        self.api_server_url = api_server_url
        self.mcp_server_url = mcp_server_url
        self.mcp_tools = []
    
    async def test_connections(self) -> bool:
        """Test connections to both API and MCP servers."""
        api_ok = False
        mcp_ok = False
        
        # Test API server connection
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.api_server_url}/health", timeout=5.0)
                api_ok = response.status_code == 200
                print(f"✅ API Server: {'Connected' if api_ok else 'Failed'}")
            except Exception as e:
                print(f"❌ API Server: {e}")
        
        # Test MCP server connection using FastMCP client
        try:
            async with Client(f"{self.mcp_server_url}/mcp") as mcp_client:
                # Test connection and discover tools
                tools = await mcp_client.list_tools()
                self.mcp_tools = tools
                mcp_ok = True
                
                print("✅ MCP Server: Connected")
                print(f"🔧 Discovered {len(tools)} MCP tools:")
                for tool in tools:
                    print(f"   • {tool.name}: {tool.description}")
                    if hasattr(tool, 'inputSchema') and tool.inputSchema:
                        props = tool.inputSchema.get('properties', {})
                        if props:
                            params = ', '.join(props.keys())
                            print(f"     Parameters: {params}")
                
        except Exception as e:
            print(f"❌ MCP Server: {e}")
            # Fallback to basic HTTP test
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.mcp_server_url}/", timeout=5.0)
                    if response.status_code != 200:
                        response = await client.get(f"{self.mcp_server_url}/tools", timeout=5.0)
                    mcp_ok = response.status_code == 200
                    if mcp_ok:
                        print("✅ MCP Server: Connected (HTTP fallback - tool discovery unavailable)")
            except Exception as fallback_e:
                print(f"❌ MCP Server: {fallback_e}")
        
        return api_ok and mcp_ok
    
    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """Get OpenAI function definitions for direct LLM calls."""
        functions = [
            {
                "name": "get_product_of_the_day",
                "description": "Get a randomly selected product of the day from the API server",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
        
        # Add discovered MCP tools
        for tool in self.mcp_tools:
            functions.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') and tool.inputSchema else {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            })
        
        return functions
    
    async def call_function(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a function call."""
        if function_name == "get_product_of_the_day":
            return await self._call_api_product_of_the_day()
        elif function_name in [tool.name for tool in self.mcp_tools]:
            return await self._call_mcp_tool(function_name, arguments)
        else:
            raise ValueError(f"Unknown function: {function_name}")
    
    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call any MCP tool using FastMCP client."""
        try:
            async with Client(f"{self.mcp_server_url}/mcp") as mcp_client:
                result = await mcp_client.call_tool(tool_name, arguments)
                # Handle different result formats
                if hasattr(result, 'content') and result.content:
                    if hasattr(result.content[0], 'text'):
                        # Text result - try to parse as JSON, fallback to plain text
                        try:
                            return json.loads(result.content[0].text)
                        except (json.JSONDecodeError, AttributeError):
                            return {"result": result.content[0].text}
                    else:
                        return {"result": str(result.content[0])}
                else:
                    return {"result": str(result)}
        except Exception as e:
            print(f"⚠️ FastMCP call failed for {tool_name}, falling back to HTTP: {e}")
            # Fallback to HTTP call for backward compatibility
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.mcp_server_url}/tools/{tool_name}",
                    json={"arguments": arguments},
                    timeout=10.0
                )
                if response.status_code == 200:
                    result = response.json()
                    return result.get("result", {})
                else:
                    raise Exception(f"MCP call failed: {response.status_code}")
    
    async def _call_api_product_of_the_day(self) -> Dict[str, Any]:
        """Call API server to get product of the day."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_server_url}/product-of-the-day", timeout=10.0)
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"API call failed: {response.status_code}")


class DirectLLMAgent:
    """Agent using direct LLM calls with function calling."""
    
    def __init__(self, ai_endpoint: str, model_name: str, tool_registry: ToolRegistry):
        self.ai_endpoint = ai_endpoint
        self.model_name = model_name
        self.tool_registry = tool_registry
    
    async def run(self) -> None:
        """Run the direct LLM agent approach."""
        print("\n" + "="*80)
        print("🔄 APPROACH 1: Direct LLM Agent with Function Calling")
        print("="*80)
        
        async with DefaultAzureCredential() as credential:
            client = ChatCompletionsClient(
                endpoint=self.ai_endpoint,
                credential=credential,
                credential_scopes=["https://cognitiveservices.azure.com/.default"],
            )
            
            print("✅ Connected to Azure AI Models directly")
            print(f"🤖 Using model: {self.model_name}")
            
            # System message
            system_message = """You are a helpful assistant that can get product information and stock levels.
            
            Your task is to:
            1. Get the product of the day
            2. Use the product description in your response
            3. Look up the stock level for that product using its product_id
            4. Provide a comprehensive response including product details and availability
            
            Always use the available functions to get current data."""
            
            # User message
            user_message = "What's the product of the day and is it in stock?"
            print(f"\n📤 User: {user_message}")
            
            # Prepare messages with function definitions
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]
            
            # First LLM call with function definitions
            print("\n🤖 Making initial LLM call with function definitions...")
            response = await client.complete(
                model=self.model_name,
                messages=messages,
                functions=self.tool_registry.get_function_definitions(),
                function_call="auto",
                max_tokens=1000,
                temperature=0.7
            )
            
            message = response.choices[0].message
            
            # Process function calls
            if hasattr(message, 'function_call') and message.function_call:
                await self._handle_function_call(client, messages, message)
            else:
                print("📨 Assistant:", message.content)
    
    async def _handle_function_call(self, client, messages: List[Dict], message) -> None:
        """Handle function calls in the conversation."""
        function_name = message.function_call.name
        function_args = json.loads(message.function_call.arguments)
        
        print(f"🔧 Function call: {function_name}({function_args})")
        
        # Execute function
        try:
            result = await self.tool_registry.call_function(function_name, function_args)
            print(f"📥 Function result: {result}")
            
            # Add function call and result to conversation
            messages.append({
                "role": "assistant",
                "content": None,
                "function_call": {
                    "name": function_name,
                    "arguments": message.function_call.arguments
                }
            })
            messages.append({
                "role": "function",
                "name": function_name,
                "content": json.dumps(result)
            })
            
            # Continue conversation - might trigger more function calls
            response = await client.complete(
                model=self.model_name,
                messages=messages,
                functions=self.tool_registry.get_function_definitions(),
                function_call="auto",
                max_tokens=1000,
                temperature=0.7
            )
            
            new_message = response.choices[0].message
            
            # Check for more function calls
            if hasattr(new_message, 'function_call') and new_message.function_call:
                await self._handle_function_call(client, messages, new_message)
            else:
                print("📨 Assistant:", new_message.content)
                
        except Exception as e:
            print(f"❌ Function call failed: {e}")
            messages.append({
                "role": "function", 
                "name": function_name,
                "content": f"Error: {e}"
            })


class FoundryAgentService:
    """Agent using Foundry Agent Service with registered lifecycle."""
    
    def __init__(self, project_endpoint: str, model_deployment: str, tool_registry: ToolRegistry):
        self.project_endpoint = project_endpoint
        self.model_deployment = model_deployment
        self.tool_registry = tool_registry
    
    async def run(self) -> None:
        """Run the Foundry Agent Service approach."""
        print("\n" + "="*80)
        print("🔄 APPROACH 2: Foundry Agent Service with Registered Agent")
        print("="*80)
        
        async with DefaultAzureCredential() as credential:
            async with AIProjectClient(
                endpoint=self.project_endpoint,
                credential=credential
            ) as project_client:
                
                print("✅ Connected to Azure AI Project")
                print(f"🤖 Creating agent with model: {self.model_deployment}")
                
                # Create agent with comprehensive instructions and dynamic tools
                tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": "get_product_of_the_day",
                            "description": "Get a randomly selected product of the day from the API server",
                            "parameters": {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        }
                    }
                ]
                
                # Add discovered MCP tools
                for mcp_tool in self.tool_registry.mcp_tools:
                    tools.append({
                        "type": "function",
                        "function": {
                            "name": mcp_tool.name,
                            "description": mcp_tool.description,
                            "parameters": mcp_tool.inputSchema if hasattr(mcp_tool, 'inputSchema') and mcp_tool.inputSchema else {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        }
                    })
                
                agent = await project_client.agents.create_agent(
                    model=self.model_deployment,
                    name="Product Info Agent",
                    instructions=f"""You are a helpful assistant that provides product information and stock levels.

Your task is to:
1. Get the product of the day from the API
2. Use the product description in your response  
3. Look up the stock level for that product using its product_id via MCP
4. Provide a comprehensive response including product details and availability

You have access to these tools:
- get_product_of_the_day: Gets today's featured product from the API server
{chr(10).join([f"- {tool.name}: {tool.description}" for tool in self.tool_registry.mcp_tools])}

Always use both API and MCP tools to provide complete information.""",
                    tools=tools
                )
                print(f"✅ Agent created: {agent.id}")
                
                try:
                    # Create thread
                    thread = await project_client.agents.create_thread()
                    print(f"✅ Thread created: {thread.id}")
                    
                    # Send user message
                    user_message = "What's the product of the day and is it in stock?"
                    print(f"\n📤 User: {user_message}")
                    
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
                    
                    # Wait for completion and handle tool calls
                    while run.status in ["queued", "in_progress", "requires_action"]:
                        await asyncio.sleep(1)
                        run = await project_client.agents.get_run(
                            thread_id=thread.id,
                            run_id=run.id
                        )
                        
                        if run.status == "requires_action":
                            print("🔧 Agent requesting tool calls...")
                            await self._handle_required_actions(project_client, thread.id, run.id, run.required_action)
                    
                    # Get final messages
                    messages = await project_client.agents.list_messages(thread_id=thread.id)
                    print("\n📨 Agent response:")
                    for msg in messages.data:
                        if msg.role == "assistant":
                            for content in msg.content:
                                if hasattr(content, 'text') and content.text:
                                    print(f"   {content.text.value}")
                
                finally:
                    # Cleanup
                    print(f"\n🧹 Cleaning up agent {agent.id}...")
                    await project_client.agents.delete_agent(agent.id)
                    print("✅ Agent deleted")
    
    async def _handle_required_actions(self, project_client, thread_id: str, run_id: str, required_action) -> None:
        """Handle required actions (tool calls) from the agent."""
        tool_outputs = []
        
        for tool_call in required_action.submit_tool_outputs.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            print(f"   🔧 Calling: {function_name}({function_args})")
            
            try:
                result = await self.tool_registry.call_function(function_name, function_args)
                print(f"   📥 Result: {result}")
                
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(result)
                })
            except Exception as e:
                print(f"   ❌ Error: {e}")
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps({"error": str(e)})
                })
        
        # Submit tool outputs
        await project_client.agents.submit_tool_outputs_to_run(
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs
        )


async def main():
    """Main entry point for unified agent testing."""
    print("🚀 Starting Unified MAF Agent Testing")
    print("="*80)
    
    # Configuration
    ai_endpoint = os.getenv("AI_ENDPOINT")
    project_endpoint = os.getenv("PROJECT_ENDPOINT") 
    model_name = os.getenv("MODEL_NAME", "gpt-4o")
    model_deployment = os.getenv("MODEL_DEPLOYMENT", "gpt-4o")
    api_server_url = os.getenv("API_SERVER_URL", "http://localhost:8000")
    mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
    
    # Initialize tool registry
    tool_registry = ToolRegistry(api_server_url, mcp_server_url)
    
    # Test connections
    print("\n🔍 Testing tool connections...")
    if not await tool_registry.test_connections():
        print("❌ Cannot connect to required services. Please ensure API and MCP servers are running.")
        print(f"   API Server: {api_server_url}")
        print(f"   MCP Server: {mcp_server_url}")
        return
    
    try:
        # Approach 1: Direct LLM Agent
        if ai_endpoint:
            direct_agent = DirectLLMAgent(ai_endpoint, model_name, tool_registry)
            await direct_agent.run()
        else:
            print("\n⚠️  AI_ENDPOINT not configured, skipping direct LLM approach")
        
        # Wait between approaches
        print("\n" + "."*80)
        print("⏳ Waiting 3 seconds before next approach...")
        await asyncio.sleep(3)
        
        # Approach 2: Foundry Agent Service
        if project_endpoint:
            foundry_agent = FoundryAgentService(project_endpoint, model_deployment, tool_registry)
            await foundry_agent.run()
        else:
            print("\n⚠️  PROJECT_ENDPOINT not configured, skipping Foundry Agent Service approach")
        
        print("\n" + "="*80)
        print("✅ All agent approaches completed successfully!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error during agent execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

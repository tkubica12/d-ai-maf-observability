"""
Unified MAF Agent demonstrating multiple observability scenarios.

Implemented Scenarios:
1. local-maf: Local Microsoft Agent Framework with API and MCP tools
2. maf-with-fas: Microsoft Agent Framework with Foundry Agent Service and API and MCP tools

Planned Scenarios:
3. local-maf-multiagent: Local Microsoft Agent Framework multi-agent with API and MCP tools
4. maf-with-fas-multiagent: MAF with Foundry Agent Service multi-agent and API and MCP tools
5. local-maf-with-fas-multiagent: MAF with mix of local and Foundry Agent Service multi-agent

This agent demonstrates:
- API function calling to get product of the day
- MCP tool integration for stock lookup
- Sequential testing of scenarios
- Network-based tool integration
- OpenTelemetry instrumentation with message content logging
"""
from __future__ import annotations

import asyncio
import inspect
import json
import os
import random
import sys
from typing import Any, Callable, Dict, List, Optional, Type
import uuid

import httpx
from dotenv import load_dotenv
from fastmcp import Client
from pydantic import BaseModel, Field, create_model

from agent_framework import ChatAgent, ai_function
from agent_framework.azure import AzureAIAgentClient, AzureOpenAIResponsesClient
from agent_framework.observability import get_tracer, setup_observability
from azure.identity import DefaultAzureCredential
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential

load_dotenv()

# Mock user data for observability demo (as per DESIGN.md)
MOCK_USERS = [
    {"user_id": "user_001", "is_vip": True, "department": "Engineering"},
    {"user_id": "user_002", "is_vip": True, "department": "Marketing"},
    {"user_id": "user_003", "is_vip": True, "department": "Engineering"},
    {"user_id": "user_004", "is_vip": False, "department": "Marketing"},
    {"user_id": "user_005", "is_vip": False, "department": "Engineering"},
]

def get_mock_user_context() -> Dict[str, Any]:
    """Generate mock user context for observability dimensions."""
    user = random.choice(MOCK_USERS)
    return {
        "user_id": user["user_id"],
        "is_vip": user["is_vip"],
        "department": user["department"],
        "thread_id": f"thread_{uuid.uuid4().hex[:8]}",
    }

# Configure OpenTelemetry only if endpoint is configured
otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
if otlp_endpoint:
    # Enable sensitive data logging (prompts, completions) if configured
    enable_sensitive = os.getenv("ENABLE_SENSITIVE_DATA", "true").lower() in ("true", "1", "yes")
    setup_observability(
        enable_sensitive_data=enable_sensitive,
        otlp_endpoint=otlp_endpoint,
    )
    tracer = get_tracer(__name__)
    print(f"🔭 OpenTelemetry configured: {otlp_endpoint}")
    print(f"   Service: {os.getenv('OTEL_SERVICE_NAME', 'agent')}")
    print(f"   Sensitive data logging: {'Enabled' if enable_sensitive else 'Disabled'}")
else:
    print("⚠️  OpenTelemetry disabled (OTEL_EXPORTER_OTLP_ENDPOINT not set)")
    tracer = None


class ToolRegistry:
    """Registry for managing both API and MCP tools via Agent Framework-compatible callables."""

    def __init__(self, api_server_url: str, mcp_server_url: str) -> None:
        self.api_server_url = api_server_url.rstrip("/")
        self.mcp_server_url = mcp_server_url.rstrip("/")
        self.mcp_tools: List[Any] = []

    async def test_connections(self) -> bool:
        """Test connections to both API and MCP servers and cache MCP tool metadata."""
        api_ok = False
        mcp_ok = False

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.api_server_url}/health", timeout=5.0)
                api_ok = response.status_code == 200
                print(f"✅ API Server: {'Connected' if api_ok else 'Failed'}")
            except Exception as exc:  # noqa: BLE001
                print(f"❌ API Server: {exc}")

        try:
            async with Client(f"{self.mcp_server_url}/mcp") as mcp_client:
                self.mcp_tools = await mcp_client.list_tools()
                mcp_ok = True

            print("✅ MCP Server: Connected")
            print(f"🔧 Discovered {len(self.mcp_tools)} MCP tools:")
            for tool in self.mcp_tools:
                description = getattr(tool, "description", "").strip()
                print(f"   • {tool.name}: {description or 'No description provided'}")
                schema = getattr(tool, "inputSchema", None) or {}
                props = schema.get("properties", {})
                if props:
                    params = ", ".join(props.keys())
                    print(f"     Parameters: {params}")
        except Exception as exc:  # noqa: BLE001
            print(f"❌ MCP Server: {exc}")
            mcp_ok = False

        return api_ok and mcp_ok

    def get_agent_tools(self) -> List[Callable[..., Any]]:
        """Return Agent Framework tool callables (API + discovered MCP tools)."""
        tools: List[Callable[..., Any]] = [self._build_api_tool()]
        tools.extend(self._build_mcp_tool_functions())
        return tools

    def _build_api_tool(self) -> Callable[[], Any]:
        registry = self

        @ai_function(
            name="get_product_of_the_day",
            description="Get a randomly selected product of the day from the API server",
        )
        async def get_product_of_the_day() -> Dict[str, Any]:
            registry._log_tool_call("get_product_of_the_day", {})
            result = await registry._call_api_product_of_the_day()
            registry._log_tool_result("get_product_of_the_day", result)
            return result

        return get_product_of_the_day

    def _build_mcp_tool_functions(self) -> List[Callable[..., Any]]:
        functions: List[Callable[..., Any]] = []
        for tool in self.mcp_tools:
            functions.append(self._create_mcp_tool_callable(tool))
        return functions

    def _create_mcp_tool_callable(self, tool: Any) -> Callable[..., Any]:
        tool_name = tool.name
        tool_description = getattr(tool, "description", "") or ""
        schema = getattr(tool, "inputSchema", None) or {}
        registry = self
        
        # For tools with parameters, create a function with named parameters
        if schema.get("properties"):
            params = schema.get("properties", {})
            
            # Create the function code dynamically with explicit parameter names
            param_list = ", ".join(f"{name}: str" for name in params.keys())
            
            # Build the function using exec to get proper parameter names in signature
            func_code = f"""
async def call_tool({param_list}) -> Dict[str, Any]:
    # Build arguments dict from named parameters
    arguments = {{{", ".join(f'"{name}": {name}' for name in params.keys())}}}
    registry._log_tool_call(tool_name, arguments)
    result = await registry._call_mcp_tool(tool_name, arguments)
    registry._log_tool_result(tool_name, result)
    return result
"""
            # Create a namespace with the required variables
            namespace = {
                'Dict': Dict,
                'Any': Any,
                'tool_name': tool_name,
                'registry': registry,
            }
            
            # Execute the function definition
            exec(func_code, namespace)
            call_tool = namespace['call_tool']
            
            # Apply the ai_function decorator
            decorated_tool = ai_function(name=tool_name, description=tool_description)(call_tool)
            return decorated_tool
        
        # For tools without parameters
        @ai_function(name=tool_name, description=tool_description)
        async def call_tool() -> Dict[str, Any]:
            registry._log_tool_call(tool_name, {})
            result = await registry._call_mcp_tool(tool_name, {})
            registry._log_tool_result(tool_name, result)
            return result

        return call_tool

    def _log_tool_call(self, name: str, arguments: Dict[str, Any]) -> None:
        print(f"🔧 Tool call: {name}({arguments})")

    def _log_tool_result(self, name: str, result: Dict[str, Any]) -> None:
        print(f"📥 Tool result ({name}): {result}")

    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tracer:
            span = tracer.start_as_current_span("tool_registry.call_mcp_tool")
        else:
            from contextlib import nullcontext
            span = nullcontext()
            
        with span as s:
            if s:
                s.set_attribute("tool.name", tool_name)
                s.set_attribute("tool.arguments", json.dumps(arguments))

            try:
                async with Client(f"{self.mcp_server_url}/mcp") as mcp_client:
                    result = await mcp_client.call_tool(tool_name, arguments)

                if hasattr(result, "content") and result.content:
                    first_item = result.content[0]
                    if hasattr(first_item, "text") and first_item.text is not None:
                        try:
                            parsed = json.loads(first_item.text)
                        except (json.JSONDecodeError, TypeError):
                            parsed = {"result": first_item.text}
                        if s:
                            s.set_attribute("tool.result", json.dumps(parsed)[:500])
                        return parsed
                    return {"result": str(first_item)}

                parsed_result = {"result": str(result)}
                if s:
                    s.set_attribute("tool.result", json.dumps(parsed_result)[:500])
                return parsed_result
            except Exception as exc:  # noqa: BLE001
                if s:
                    s.record_exception(exc)
                print(f"⚠️ MCP call failed for {tool_name}: {exc}")
                raise

    async def _call_api_product_of_the_day(self) -> Dict[str, Any]:
        if tracer:
            span = tracer.start_as_current_span("tool_registry.call_api_product")
        else:
            from contextlib import nullcontext
            span = nullcontext()
            
        with span:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_server_url}/product-of-the-day",
                    timeout=10.0,
                )
                response.raise_for_status()
                return response.json()



class LocalMAFAgent:
    """Local Microsoft Agent Framework with API and MCP tools (local-maf)."""

    def __init__(
        self,
        ai_endpoint: str,
        model_name: str,
        tool_registry: ToolRegistry,
    ) -> None:
        self.ai_endpoint = ai_endpoint
        self.model_name = model_name
        self.tool_registry = tool_registry

    async def run(self) -> None:
        """Run local MAF agent with API and MCP tools."""
        print("\n" + "=" * 80)
        print("🔄 SCENARIO 1: Local Microsoft Agent Framework with API and MCP tools")
        print("   Scenario ID: local-maf")
        print("=" * 80)

        # Generate mock user context
        user_context = get_mock_user_context()
        print(f"👤 User Context: {user_context['user_id']} (VIP: {user_context['is_vip']}, Dept: {user_context['department']})")
        print(f"🧵 Thread ID: {user_context['thread_id']}")

        credential = DefaultAzureCredential()
        
        # Use AzureOpenAIResponsesClient for Azure OpenAI Responses API
        # The endpoint should be the base Azure OpenAI endpoint (e.g., https://<resource>.openai.azure.com)
        responses_client = AzureOpenAIResponsesClient(
            endpoint=self.ai_endpoint,
            deployment_name=self.model_name,
            api_version="preview",  # Required for Responses API
            credential=credential,
        )

        print("✅ Connected to Azure OpenAI Responses API")
        print(f"🤖 Using model: {self.model_name}")

        tool_callables = self.tool_registry.get_agent_tools()
        
        # Create agent using the responses client's create_agent method
        agent = responses_client.create_agent(
            instructions="""You are a helpful assistant that can get product information and stock levels.

Your task is to:
1. Get the product of the day
2. Use the product description in your response
3. Look up the stock level for that product using its product_id
4. Provide a comprehensive response including product details and availability

Always use the available functions to get current data.""",
            name="ProductInfoAgent",
            tools=tool_callables,
        )

        user_message = "What's the product of the day and is it in stock?"
        print(f"\n📤 User: {user_message}")

        print("\n🤖 Making LLM call with Agent Framework (AzureOpenAIResponsesClient)...")
        
        # Add custom dimensions to the span
        if tracer:
            with tracer.start_as_current_span("scenario.local-maf") as span:
                # Add custom dimensions as per DESIGN.md
                span.set_attribute("user_id", user_context["user_id"])
                span.set_attribute("is_vip", user_context["is_vip"])
                span.set_attribute("department", user_context["department"])
                span.set_attribute("thread_id", user_context["thread_id"])
                span.set_attribute("scenario_id", "local-maf")
                span.set_attribute("scenario_type", "single-agent")
                
                response = await agent.run(user_message)
        else:
            response = await agent.run(user_message)

        # Extract text from response
        if hasattr(response, "text"):
            final_text = response.text
        elif hasattr(response, "content"):
            final_text = response.content
        else:
            final_text = str(response)

        print(f"\n📨 Assistant: {final_text}")


class MAFWithFASAgent:
    """Microsoft Agent Framework with Foundry Agent Service and API and MCP tools (maf-with-fas)."""

    def __init__(
        self,
        project_endpoint: str,
        model_deployment: str,
        tool_registry: ToolRegistry,
    ) -> None:
        self.project_endpoint = project_endpoint
        self.model_deployment = model_deployment
        self.tool_registry = tool_registry

    async def run(self) -> None:
        """Run MAF with Foundry Agent Service and API and MCP tools."""
        print("\n" + "=" * 80)
        print("🔄 SCENARIO 2: Microsoft Agent Framework with Foundry Agent Service")
        print("   Scenario ID: maf-with-fas")
        print("=" * 80)

        # Generate mock user context
        user_context = get_mock_user_context()
        print(f"👤 User Context: {user_context['user_id']} (VIP: {user_context['is_vip']}, Dept: {user_context['department']})")
        print(f"🧵 Thread ID: {user_context['thread_id']}")

        # AzureAIAgentClient requires async credential
        async with AsyncDefaultAzureCredential() as credential:
            agent_client = AzureAIAgentClient(
                project_endpoint=self.project_endpoint,
                model_deployment_name=self.model_deployment,
                async_credential=credential,
            )

            print("✅ Connected to Azure AI Project")
            print(f"🤖 Using model: {self.model_deployment}")

            tool_callables = self.tool_registry.get_agent_tools()
            tool_names = ", ".join(
                t.__name__ if hasattr(t, "__name__") else str(t) for t in tool_callables
            )

            instructions = f"""You are a helpful assistant that provides product information and stock levels.

Your task is to:
1. Get the product of the day from the API
2. Use the product description in your response
3. Look up the stock level for that product using its product_id via MCP
4. Provide a comprehensive response including product details and availability

You have access to these tools: {tool_names}

Always use both API and MCP tools to provide complete information."""

            # Use agent as context manager to properly close sessions
            async with agent_client.create_agent(
                name="Product Info Agent",
                instructions=instructions,
                tools=tool_callables,
            ) as agent:
                print(f"✅ Agent created (using Foundry Agent Service)")

                user_message = "What's the product of the day and is it in stock?"
                print(f"\n📤 User: {user_message}")

                print("\n🤖 Agent processing...")
                
                # Add custom dimensions to the span
                if tracer:
                    with tracer.start_as_current_span("scenario.maf-with-fas") as span:
                        # Add custom dimensions as per DESIGN.md
                        span.set_attribute("user_id", user_context["user_id"])
                        span.set_attribute("is_vip", user_context["is_vip"])
                        span.set_attribute("department", user_context["department"])
                        span.set_attribute("thread_id", user_context["thread_id"])
                        span.set_attribute("scenario_id", "maf-with-fas")
                        span.set_attribute("scenario_type", "single-agent")
                        
                        # Set store=True for service-managed threads to avoid warning
                        response = await agent.run(user_message, store=True)
                else:
                    # Set store=True for service-managed threads to avoid warning
                    response = await agent.run(user_message, store=True)

                # Extract text from response
                if hasattr(response, "text"):
                    final_text = response.text
                elif hasattr(response, "content"):
                    final_text = response.content
                else:
                    final_text = str(response)

                print(f"\n📨 Assistant: {final_text}")


async def main() -> None:
    """Main entry point for unified agent testing."""
    print("🚀 Starting Unified MAF Agent Testing")
    print("=" * 80)

    ai_endpoint = os.getenv("AI_ENDPOINT")
    project_endpoint = os.getenv("PROJECT_ENDPOINT")
    model_name = os.getenv("MODEL_NAME", "gpt-5-nano")
    model_deployment = os.getenv("MODEL_DEPLOYMENT", "gpt-5-nano")
    api_server_url = os.getenv("API_SERVER_URL", "http://localhost:8000")
    mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8001")

    tool_registry = ToolRegistry(api_server_url, mcp_server_url)

    print("\n🔍 Testing tool connections...")
    if not await tool_registry.test_connections():
        print("❌ Cannot connect to required services. Please ensure API and MCP servers are running.")
        print(f"   API Server: {api_server_url}")
        print(f"   MCP Server: {mcp_server_url}")
        return

    try:
        # Scenario 1: Local Microsoft Agent Framework with API and MCP tools
        if ai_endpoint:
            local_maf_agent = LocalMAFAgent(ai_endpoint, model_name, tool_registry)
            await local_maf_agent.run()
        else:
            print("\n⚠️  AI_ENDPOINT not configured, skipping local-maf scenario")

        print("\n" + "." * 80)
        print("⏳ Waiting 3 seconds before next scenario...")
        await asyncio.sleep(3)

        # Scenario 2: Microsoft Agent Framework with Foundry Agent Service and API and MCP tools
        if project_endpoint:
            maf_with_fas_agent = MAFWithFASAgent(project_endpoint, model_deployment, tool_registry)
            await maf_with_fas_agent.run()
        else:
            print("\n⚠️  PROJECT_ENDPOINT not configured, skipping maf-with-fas scenario")

        # TODO: Implement additional scenarios
        # Scenario 3: Local Microsoft Agent Framework multi-agent (local-maf-multiagent)
        # Scenario 4: MAF with Foundry Agent Service multi-agent (maf-with-fas-multiagent)
        # Scenario 5: MAF with mix of local and Foundry Agent Service multi-agent (local-maf-with-fas-multiagent)

        print("\n" + "=" * 80)
        print("✅ All implemented scenarios completed successfully!")
        print("=" * 80)

    except Exception as exc:  # noqa: BLE001
        print(f"\n❌ Error during agent execution: {exc}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        print(f"\n❌ Fatal error: {exc}")
        sys.exit(1)


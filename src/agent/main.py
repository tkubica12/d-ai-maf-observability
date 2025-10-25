"""
Unified MAF Agent demonstrating multiple observability scenarios.

Refactored to use native MAF MCP support:
- MCPStreamableHTTPTool for local-maf scenario
- HostedMCPTool for maf-with-fas scenario

Implemented Scenarios:
1. local-maf: Local Microsoft Agent Framework with API and MCP tools
2. maf-with-fas: Microsoft Agent Framework with Foundry Agent Service with API and MCP tools

Planned Scenarios:
3. local-maf-multiagent: Local Microsoft Agent Framework multi-agent with API and MCP tools
4. maf-with-fas-multiagent: MAF with Foundry Agent Service multi-agent and API and MCP tools
5. local-maf-with-fas-multiagent: MAF with mix of local and Foundry Agent Service multi-agent

This agent demonstrates:
- API function calling to get product of the day
- Native MCP tool integration for stock lookup
- Sequential testing of scenarios
- Network-based tool integration
- OpenTelemetry instrumentation with message content logging
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import random
import sys
from typing import Any, Dict, List, Optional
import uuid

import httpx
from dotenv import load_dotenv
from fastmcp import Client

from agent_framework import ChatAgent, ai_function, MCPStreamableHTTPTool, HostedMCPTool
from agent_framework.azure import AzureAIAgentClient, AzureOpenAIResponsesClient
from agent_framework.observability import get_tracer, get_meter, setup_observability
from azure.identity import DefaultAzureCredential
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential

load_dotenv()

# Configure Python logging - NO console output, only OTLP
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Remove all handlers to prevent console output
logger.handlers.clear()
logger.propagate = False

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
    
    # FIRST: Set up global MeterProvider BEFORE setup_observability
    from opentelemetry import metrics as otel_metrics
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    
    metric_resource = Resource(attributes={
        SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", "agent")
    })
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True),
        export_interval_millis=5000,  # Export every 5 seconds for testing
    )
    meter_provider = MeterProvider(resource=metric_resource, metric_readers=[metric_reader])
    otel_metrics.set_meter_provider(meter_provider)
    
    # THEN: Setup Agent Framework observability (traces + logs)
    setup_observability(
        enable_sensitive_data=enable_sensitive,
        otlp_endpoint=otlp_endpoint,
    )
    tracer = get_tracer(__name__)
    
    # Get meter from the global provider we configured
    meter = meter_provider.get_meter(__name__)
    
    # Enable httpx/aiohttp instrumentation for trace propagation
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
    
    HTTPXClientInstrumentor().instrument()
    AioHttpClientInstrumentor().instrument()
    
    # Create custom counter metric for demo purposes
    agent_call_counter = meter.create_counter(
        name="custom_agent_call_count",
        description="Custom demo metric for agent calls",
        unit="1",
    )
    
    # Configure OTLP logging
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry._logs import set_logger_provider
    
    # Create log provider with resource
    log_resource = Resource(attributes={
        SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", "agent")
    })
    logger_provider = LoggerProvider(resource=log_resource)
    set_logger_provider(logger_provider)
    
    # Add OTLP log exporter
    otlp_log_exporter = OTLPLogExporter(endpoint=otlp_endpoint, insecure=True)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))
    
    # Attach OTLP handler to root logger for telemetry collection
    otlp_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    
    # Configure root logger: NO console handlers, only OTLP
    root_logger = logging.getLogger()
    root_logger.handlers.clear()  # Remove all console handlers
    root_logger.addHandler(otlp_handler)  # Only OTLP handler
    root_logger.setLevel(logging.INFO)
    
    # Also configure our app logger
    logger.addHandler(otlp_handler)
    
    # Suppress noisy library loggers completely (no console, still OTLP)
    for lib_logger_name in [
        "agent_framework.observability",
        "agent_framework._tools", 
        "httpx",
        "azure.core.pipeline.policies",
        "azure.identity",
        "azure.identity.aio",
        "mcp.client",
        "opentelemetry._logs._internal",
    ]:
        lib_logger = logging.getLogger(lib_logger_name)
        lib_logger.setLevel(logging.CRITICAL)  # Suppress almost everything
        lib_logger.propagate = True  # Still send to OTLP via root
    
    logger.info(
        "OpenTelemetry configured",
        extra={
            "otlp_endpoint": otlp_endpoint,
            "service_name": os.getenv("OTEL_SERVICE_NAME", "agent"),
            "sensitive_data_logging": enable_sensitive
        }
    )
else:
    logger.warning("OpenTelemetry disabled (OTEL_EXPORTER_OTLP_ENDPOINT not set)")
    tracer = None
    meter = None
    agent_call_counter = None


async def test_connections(api_server_url: str, mcp_server_url: str) -> bool:
    """Test connections to both API and MCP servers."""
    api_ok = False
    mcp_ok = False

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{api_server_url}/health", timeout=5.0)
            api_ok = response.status_code == 200
            print(f"✅ API Server: {'Connected' if api_ok else 'Failed'}")
            logger.info(f"API Server connection: {'Connected' if api_ok else 'Failed'}")
        except Exception as exc:  # noqa: BLE001
            print(f"❌ API Server: {exc}")
            logger.error("API Server connection failed", exc_info=exc)

    try:
        # Test MCP server by establishing a proper MCP connection
        async with Client(f"{mcp_server_url}/mcp") as mcp_client:
            # Try to list tools to verify connection works
            tools = await mcp_client.list_tools()
            mcp_ok = True
            print(f"✅ MCP Server: Connected")
            print(f"🔧 Discovered {len(tools)} MCP tools")
            logger.info(f"MCP Server connection: Connected")
    except Exception as exc:  # noqa: BLE001
        print(f"❌ MCP Server: {exc}")
        logger.error("MCP Server connection failed", exc_info=exc)
        mcp_ok = False

    return api_ok and mcp_ok


class LocalMAFAgent:
    """Local Microsoft Agent Framework with API and MCP tools (local-maf)."""

    def __init__(
        self,
        ai_endpoint: str,
        model_name: str,
        api_server_url: str,
        mcp_server_url: str,
    ) -> None:
        self.ai_endpoint = ai_endpoint
        self.model_name = model_name
        self.api_server_url = api_server_url.rstrip("/")
        self.mcp_server_url = mcp_server_url.rstrip("/")

    def _create_api_tool(self):
        """Create API tool for getting product of the day."""
        api_url = self.api_server_url

        @ai_function(
            name="get_product_of_the_day",
            description="Get a randomly selected product of the day from the API server",
        )
        async def get_product_of_the_day() -> Dict[str, Any]:
            print(f"🔧 Tool call: get_product_of_the_day()")
            logger.info("Tool call", extra={"tool_name": "get_product_of_the_day", "arguments": {}})
            
            if tracer:
                span = tracer.start_as_current_span("tool.get_product_of_the_day")
            else:
                from contextlib import nullcontext
                span = nullcontext()
                
            with span as s:
                if s:
                    s.set_attribute("tool.name", "get_product_of_the_day")
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{api_url}/product-of-the-day",
                        timeout=10.0,
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    if s:
                        s.set_attribute("tool.result", json.dumps(result)[:500])
                    
                    print(f"📥 Tool result (get_product_of_the_day): {result}")
                    logger.info("Tool result", extra={"tool_name": "get_product_of_the_day", "result": result})
                    return result

        return get_product_of_the_day

    async def run(self) -> None:
        """Run local MAF agent with API and MCP tools."""
        print("\n" + "=" * 80)
        print("🔄 Local Microsoft Agent Framework with API and MCP tools")
        print("   Scenario ID: local-maf")
        print("=" * 80)

        # Generate mock user context
        user_context = get_mock_user_context()
        print(f"👤 User Context: {user_context['user_id']} (VIP: {user_context['is_vip']}, Dept: {user_context['department']})")
        print(f"🧵 Thread ID: {user_context['thread_id']}")
        
        logger.info(
            "Starting local-maf scenario",
            extra={
                "scenario_id": "local-maf",
                "user_id": user_context["user_id"],
                "is_vip": user_context["is_vip"],
                "department": user_context["department"],
                "thread_id": user_context["thread_id"]
            }
        )

        credential = DefaultAzureCredential()
        
        # Use AzureOpenAIResponsesClient for Azure OpenAI Responses API
        responses_client = AzureOpenAIResponsesClient(
            endpoint=self.ai_endpoint,
            deployment_name=self.model_name,
            api_version="preview",
            credential=credential,
        )

        print("✅ Connected to Azure OpenAI Responses API")
        print(f"🤖 Using model: {self.model_name}")
        logger.info("Connected to Azure OpenAI Responses API", extra={"model": self.model_name})

        # Create API tool
        api_tool = self._create_api_tool()
        
        # Create MCP tool using native MCPStreamableHTTPTool
        print(f"🔌 Connecting to MCP server at {self.mcp_server_url}/mcp")
        mcp_tool = MCPStreamableHTTPTool(
            name="stock_lookup_mcp",
            url=f"{self.mcp_server_url}/mcp",
        )
        
        # Note: MCPStreamableHTTPTool is a context manager
        async with mcp_tool:
            print("✅ Connected to MCP server (MCPStreamableHTTPTool)")
            logger.info("Connected to MCP server using MCPStreamableHTTPTool")
            
            # Create agent with both tools
            agent = responses_client.create_agent(
                instructions="""You are a helpful assistant that can get product information and stock levels.

Your task is to:
1. Get the product of the day
2. Use the product description in your response
3. Look up the stock level for that product using its product_id
4. Provide a comprehensive response including product details and availability

Always use the available functions to get current data.""",
                name="ProductInfoAgent",
                tools=[api_tool, mcp_tool],
            )

            user_message = "What's the product of the day and is it in stock?"
            print(f"\n📤 User: {user_message}")
            logger.info("User message", extra={"user_message": user_message, "scenario": "local-maf"})

            print("\n🤖 Making LLM call with Agent Framework (AzureOpenAIResponsesClient)...")
            logger.info("Starting agent execution")
            
            # Record custom metric with dimensions
            if agent_call_counter:
                demo_value = random.randint(1, 100)
                agent_call_counter.add(
                    demo_value,
                    attributes={
                        "service.name": os.getenv("OTEL_SERVICE_NAME", "agent"),
                        "user_id": user_context["user_id"],
                        "is_vip": str(user_context["is_vip"]).lower(),
                        "department": user_context["department"],
                        "thread_id": user_context["thread_id"],
                        "scenario_id": "local-maf",
                        "scenario_type": "single-agent",
                    }
                )
                print(f"📊 Custom metric recorded: custom_agent_call_count={demo_value}")
                logger.info(
                    "Custom metric recorded",
                    extra={
                        "metric_name": "custom_agent_call_count",
                        "metric_value": demo_value,
                        "user_id": user_context["user_id"],
                        "scenario": "local-maf"
                    }
                )
            
            # Add custom dimensions to the span
            if tracer:
                with tracer.start_as_current_span("scenario.local-maf") as span:
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
            logger.info("Agent response", extra={"response": final_text[:200], "scenario": "local-maf"})


class MAFWithFASAgent:
    """Microsoft Agent Framework with Foundry Agent Service and API and MCP tools (maf-with-fas)."""

    def __init__(
        self,
        project_endpoint: str,
        model_deployment: str,
        api_server_url: str,
        mcp_server_url: str,
    ) -> None:
        self.project_endpoint = project_endpoint
        self.model_deployment = model_deployment
        self.api_server_url = api_server_url.rstrip("/")
        self.mcp_server_url = mcp_server_url.rstrip("/")

    def _create_api_tool(self):
        """Create API tool for getting product of the day."""
        api_url = self.api_server_url

        @ai_function(
            name="get_product_of_the_day",
            description="Get a randomly selected product of the day from the API server",
        )
        async def get_product_of_the_day() -> Dict[str, Any]:
            print(f"🔧 Tool call: get_product_of_the_day()")
            logger.info("Tool call", extra={"tool_name": "get_product_of_the_day", "arguments": {}})
            
            if tracer:
                span = tracer.start_as_current_span("tool.get_product_of_the_day")
            else:
                from contextlib import nullcontext
                span = nullcontext()
                
            with span as s:
                if s:
                    s.set_attribute("tool.name", "get_product_of_the_day")
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{api_url}/product-of-the-day",
                        timeout=10.0,
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    if s:
                        s.set_attribute("tool.result", json.dumps(result)[:500])
                    
                    print(f"📥 Tool result (get_product_of_the_day): {result}")
                    logger.info("Tool result", extra={"tool_name": "get_product_of_the_day", "result": result})
                    return result

        return get_product_of_the_day

    async def run(self) -> None:
        """Run MAF with Foundry Agent Service and API and MCP tools."""
        print("\n" + "=" * 80)
        print("🔄 Microsoft Agent Framework with Foundry Agent Service")
        print("   Scenario ID: maf-with-fas")
        print("=" * 80)

        # Generate mock user context
        user_context = get_mock_user_context()
        print(f"👤 User Context: {user_context['user_id']} (VIP: {user_context['is_vip']}, Dept: {user_context['department']})")
        print(f"🧵 Thread ID: {user_context['thread_id']}")
        
        logger.info(
            "Starting maf-with-fas scenario",
            extra={
                "scenario_id": "maf-with-fas",
                "user_id": user_context["user_id"],
                "is_vip": user_context["is_vip"],
                "department": user_context["department"],
                "thread_id": user_context["thread_id"]
            }
        )

        # AzureAIAgentClient requires async credential
        async with AsyncDefaultAzureCredential() as credential:
            agent_client = AzureAIAgentClient(
                project_endpoint=self.project_endpoint,
                model_deployment_name=self.model_deployment,
                async_credential=credential,
            )

            print("✅ Connected to Azure AI Project")
            print(f"🤖 Using model: {self.model_deployment}")
            logger.info("Connected to Azure AI Project", extra={"model": self.model_deployment})

            # Create API tool
            api_tool = self._create_api_tool()
            
            # Create MCP tool using HostedMCPTool for Foundry Agent Service
            # Note: FastMCP mounts at /mcp and creates endpoint at /mcp, so full path is /mcp/mcp
            print(f"🔌 Configuring Hosted MCP tool at {self.mcp_server_url}/mcp")
            mcp_tool = HostedMCPTool(
                name="stock_lookup_mcp",
                url=f"{self.mcp_server_url}/mcp",
            )
            
            print("✅ Hosted MCP tool configured for Foundry Agent Service")
            logger.info("Hosted MCP tool configured for Foundry Agent Service")

            instructions = """You are a helpful assistant that provides product information and stock levels.

Your task is to:
1. Get the product of the day from the API
2. Use the product description in your response
3. Look up the stock level for that product using its product_id via MCP
4. Provide a comprehensive response including product details and availability

Always use both API and MCP tools to provide complete information."""

            # Use agent as context manager to properly close sessions
            async with agent_client.create_agent(
                name="Product Info Agent",
                instructions=instructions,
                tools=[api_tool, mcp_tool],
            ) as agent:
                print("✅ Agent created (using Foundry Agent Service)")
                logger.info("Agent created using Foundry Agent Service")

                user_message = "What's the product of the day and is it in stock?"
                print(f"\n📤 User: {user_message}")
                logger.info("User message", extra={"user_message": user_message, "scenario": "maf-with-fas"})

                print("\n🤖 Agent processing...")
                logger.info("Starting agent execution")
                
                # Record custom metric with dimensions
                if agent_call_counter:
                    demo_value = random.randint(1, 100)
                    agent_call_counter.add(
                        demo_value,
                        attributes={
                            "service.name": os.getenv("OTEL_SERVICE_NAME", "agent"),
                            "user_id": user_context["user_id"],
                            "is_vip": str(user_context["is_vip"]).lower(),
                            "department": user_context["department"],
                            "thread_id": user_context["thread_id"],
                            "scenario_id": "maf-with-fas",
                            "scenario_type": "single-agent",
                        }
                    )
                    print(f"📊 Custom metric recorded: custom_agent_call_count={demo_value}")
                    logger.info(
                        "Custom metric recorded",
                        extra={
                            "metric_name": "custom_agent_call_count",
                            "metric_value": demo_value,
                            "user_id": user_context["user_id"],
                            "scenario": "maf-with-fas"
                        }
                    )
                
                # Add custom dimensions to the span
                if tracer:
                    with tracer.start_as_current_span("scenario.maf-with-fas") as span:
                        span.set_attribute("user_id", user_context["user_id"])
                        span.set_attribute("is_vip", user_context["is_vip"])
                        span.set_attribute("department", user_context["department"])
                        span.set_attribute("thread_id", user_context["thread_id"])
                        span.set_attribute("scenario_id", "maf-with-fas")
                        span.set_attribute("scenario_type", "single-agent")
                        
                        # Set store=True for service-managed threads
                        response = await agent.run(user_message, store=True)
                else:
                    # Set store=True for service-managed threads
                    response = await agent.run(user_message, store=True)

                # Extract text from response
                if hasattr(response, "text"):
                    final_text = response.text
                elif hasattr(response, "content"):
                    final_text = response.content
                else:
                    final_text = str(response)

                print(f"\n📨 Assistant: {final_text}")
                logger.info("Agent response", extra={"response": final_text[:200], "scenario": "maf-with-fas"})


async def main(scenarios: Optional[List[str]] = None) -> None:
    """Main entry point for unified agent testing."""
    print("🚀 Starting Unified MAF Agent Testing")
    print("=" * 80)
    logger.info("Starting Unified MAF Agent Testing")

    ai_endpoint = os.getenv("AI_ENDPOINT")
    project_endpoint = os.getenv("PROJECT_ENDPOINT")
    model_name = os.getenv("MODEL_NAME", "gpt-5-nano")
    model_deployment = os.getenv("MODEL_DEPLOYMENT", "gpt-5-nano")
    api_server_url = os.getenv("API_SERVER_URL", "http://localhost:8000")
    mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8001")

    print("\n🔍 Testing tool connections...")
    logger.info("Testing tool connections")
    if not await test_connections(api_server_url, mcp_server_url):
        print("❌ Cannot connect to required services. Please ensure API and MCP servers are running.")
        print(f"   API Server: {api_server_url}")
        print(f"   MCP Server: {mcp_server_url}")
        logger.error("Cannot connect to required services", extra={"api_url": api_server_url, "mcp_url": mcp_server_url})
        return

    try:
        # Decide which scenarios to run. If `scenarios` is None or empty -> run all implemented scenarios.
        run_all = not scenarios

        def should_run(name: str) -> bool:
            return run_all or (scenarios is not None and name in scenarios)

        # Scenario 1: Local Microsoft Agent Framework with API and MCP tools
        if should_run("local-maf"):
            if ai_endpoint:
                local_maf_agent = LocalMAFAgent(ai_endpoint, model_name, api_server_url, mcp_server_url)
                await local_maf_agent.run()
            else:
                print("\n⚠️  AI_ENDPOINT not configured, skipping local-maf scenario")
                logger.warning("AI_ENDPOINT not configured, skipping local-maf scenario")

        # If running multiple scenarios, wait a bit between them
        if run_all:
            print("\n" + "." * 80)
            print("⏳ Waiting 3 seconds before next scenario...")
            await asyncio.sleep(3)
        else:
            # If user explicitly requested multiple scenarios (space/comma separated) and included both,
            # give a short pause between user-requested scenarios as well.
            if scenarios is not None and len(scenarios) > 1:
                print("\n" + "." * 80)
                print("⏳ Waiting 3 seconds before next scenario...")
                await asyncio.sleep(3)

        # Scenario 2: Microsoft Agent Framework with Foundry Agent Service and API and MCP tools
        if should_run("maf-with-fas"):
            if project_endpoint:
                maf_with_fas_agent = MAFWithFASAgent(project_endpoint, model_deployment, api_server_url, mcp_server_url)
                await maf_with_fas_agent.run()
            else:
                print("\n⚠️  PROJECT_ENDPOINT not configured, skipping maf-with-fas scenario")
                logger.warning("PROJECT_ENDPOINT not configured, skipping maf-with-fas scenario")

        # TODO: Implement additional scenarios
        # Scenario 3: Local Microsoft Agent Framework multi-agent (local-maf-multiagent)
        # Scenario 4: MAF with Foundry Agent Service multi-agent (maf-with-fas-multiagent)
        # Scenario 5: MAF with mix of local and Foundry Agent Service multi-agent (local-maf-with-fas-multiagent)

        print("\n" + "=" * 80)
        print("✅ All requested scenarios completed successfully!")
        print("=" * 80)
        logger.info("All requested scenarios completed successfully")

    except Exception as exc:  # noqa: BLE001
        print(f"\n❌ Error during agent execution: {exc}")
        logger.error("Error during agent execution", exc_info=exc)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description="Unified MAF Agent test runner")
        parser.add_argument("-s", "--scenarios", nargs="*",
                            help=("Scenarios to run. Provide space-separated values like: -s local-maf maf-with-fas "
                                  "or a single comma-separated string: -s local-maf,maf-with-fas."
                                  "If omitted, all implemented scenarios will run."),
                            default=None)

        args = parser.parse_args()

        # Available scenario IDs implemented in this script
        available_scenarios = ["local-maf", "maf-with-fas"]

        scenario_list = None
        # args.scenarios is None when the user did not pass -s at all -> run all
        # If the user passed -s but no values, argparse yields an empty list -> treat as error
        if args.scenarios is not None:
            if len(args.scenarios) == 0:
                print("No scenarios specified after -s/--scenarios. Available scenarios:")
                for s in available_scenarios:
                    print(f"  - {s}")
                sys.exit(2)

            # Support comma-separated single argument or multiple space-separated args
            if len(args.scenarios) == 1 and "," in args.scenarios[0]:
                scenario_list = [s.strip() for s in args.scenarios[0].split(",") if s.strip()]
            else:
                scenario_list = [s.strip() for s in args.scenarios if s.strip()]

            if not scenario_list:
                print("No valid scenarios provided. Available scenarios:")
                for s in available_scenarios:
                    print(f"  - {s}")
                sys.exit(2)

            # Validate requested scenarios
            invalid = [s for s in scenario_list if s not in available_scenarios]
            if invalid:
                print(f"Unknown scenario(s): {', '.join(invalid)}")
                print("Available scenarios:")
                for s in available_scenarios:
                    print(f"  - {s}")
                sys.exit(2)

        # Run main with optional scenarios list
        asyncio.run(main(scenarios=scenario_list))
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        logger.warning("Testing interrupted by user")
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        print(f"\n❌ Fatal error: {exc}")
        logger.error("Fatal error", exc_info=exc)
        sys.exit(1)

"""
Unified MAF Agent demonstrating multiple observability scenarios.

Scenarios are organized in separate modules under scenarios/ for better maintainability.

Implemented Scenarios:
- local-maf: Local Microsoft Agent Framework with API and MCP tools
- maf-with-fas: Microsoft Agent Framework with Foundry Agent Service with API and MCP tools
- local-maf-multiagent: Local MAF multi-agent with facilitator + worker pattern

Planned Scenarios:
- local-maf-with-a2a: MAF with worker as A2A service
- local-maf-with-fas-a2a: Foundry-hosted facilitator calling A2A worker

This agent demonstrates:
- API function calling to get product of the day
- Native MCP tool integration for stock lookup
- Multi-agent collaboration patterns
- Sequential testing of scenarios
- OpenTelemetry instrumentation with message content logging
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import random
import sys
from typing import Any, Dict
import uuid

import httpx
from dotenv import load_dotenv
from fastmcp import Client

from agent_framework.observability import get_tracer, get_meter, setup_observability

# Import scenario implementations
from scenarios import LocalMAFAgent, MAFWithFASAgent, LocalMAFMultiAgent

# OpenTelemetry Baggage for cross-span context propagation
from opentelemetry import baggage, context
from opentelemetry.sdk.trace import SpanProcessor, ReadableSpan

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
    """Generate mock user context for observability dimensions using OTel semantic conventions."""
    user = random.choice(MOCK_USERS)
    roles = ["vip"] if user["is_vip"] else []
    return {
        "user.id": user["user_id"],  # Langfuse expected attribute for user identification
        "user.roles": roles,  # OTel standard for user roles (VIP status)
        "organization.department": user["department"],  # Custom namespaced attribute
        "session.id": f"session_{uuid.uuid4().hex[:8]}",  # Langfuse expected attribute for session tracking
    }


class BaggageSpanProcessor(SpanProcessor):
    """
    Custom SpanProcessor that automatically copies baggage values to span attributes.
    
    This ensures that user/session context set via Baggage API is available as
    queryable attributes on all spans (including child spans from frameworks/libraries).
    """
    
    # Define which baggage keys to copy to span attributes
    BAGGAGE_KEYS = [
        "user.id",
        "session.id", 
        "organization.department",
        "user.roles",
    ]
    
    def on_start(self, span: "ReadableSpan", parent_context: context.Context = None) -> None:
        """Called when a span is started - copy baggage to span attributes."""
        if parent_context is None:
            parent_context = context.get_current()
        
        # Copy each baggage item to span attributes
        for key in self.BAGGAGE_KEYS:
            value = baggage.get_baggage(key, parent_context)
            if value is not None:
                span.set_attribute(key, value)
    
    def on_end(self, span: "ReadableSpan") -> None:
        """Called when a span ends - no action needed."""
        pass
    
    def shutdown(self) -> None:
        """Called on shutdown - no cleanup needed."""
        pass
    
    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Called on flush - no action needed."""
        return True


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
    
    # Add BaggageSpanProcessor to automatically propagate baggage to all spans
    from opentelemetry import trace as trace_api
    tracer_provider = trace_api.get_tracer_provider()
    if hasattr(tracer_provider, 'add_span_processor'):
        baggage_processor = BaggageSpanProcessor()
        tracer_provider.add_span_processor(baggage_processor)
        logger.info("BaggageSpanProcessor registered for automatic context propagation")
    
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


async def main(scenarios: list[str] | None = None) -> None:
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

        # local-maf: Local Microsoft Agent Framework with API and MCP tools
        if should_run("local-maf"):
            if ai_endpoint:
                local_maf_agent = LocalMAFAgent(
                    ai_endpoint=ai_endpoint,
                    model_name=model_name,
                    api_server_url=api_server_url,
                    mcp_server_url=mcp_server_url,
                    tracer=tracer,
                    meter=meter,
                    agent_call_counter=agent_call_counter,
                    get_mock_user_context=get_mock_user_context,
                )
                await local_maf_agent.run()
            else:
                print("\n⚠️  AI_ENDPOINT not configured, skipping local-maf scenario")
                logger.warning("AI_ENDPOINT not configured, skipping local-maf scenario")

        # If running multiple scenarios, wait a bit between them
        if run_all or (scenarios is not None and len(scenarios) > 1 and should_run("maf-with-fas")):
            print("\n" + "." * 80)
            print("⏳ Waiting 3 seconds before next scenario...")
            await asyncio.sleep(3)

        # maf-with-fas: Microsoft Agent Framework with Foundry Agent Service and API and MCP tools
        if should_run("maf-with-fas"):
            if project_endpoint:
                # TODO: Remove hardcoded model when FAS supports gpt-5-nano with MCP
                # Currently FAS with MCP requires gpt-4.1-mini as a workaround
                maf_with_fas_agent = MAFWithFASAgent(
                    project_endpoint=project_endpoint,
                    model_deployment="gpt-4.1-mini",  # Hardcoded workaround for FAS + MCP
                    api_server_url=api_server_url,
                    mcp_server_url=mcp_server_url,
                    tracer=tracer,
                    meter=meter,
                    agent_call_counter=agent_call_counter,
                    get_mock_user_context=get_mock_user_context,
                )
                await maf_with_fas_agent.run()
            else:
                print("\n⚠️  PROJECT_ENDPOINT not configured, skipping maf-with-fas scenario")
                logger.warning("PROJECT_ENDPOINT not configured, skipping maf-with-fas scenario")

        # If running multiple scenarios, wait a bit between them
        if run_all or (scenarios is not None and len(scenarios) > 1 and should_run("local-maf-multiagent")):
            print("\n" + "." * 80)
            print("⏳ Waiting 3 seconds before next scenario...")
            await asyncio.sleep(3)

        # local-maf-multiagent: Local Microsoft Agent Framework multi-agent with facilitator + worker pattern
        if should_run("local-maf-multiagent"):
            if ai_endpoint:
                local_maf_multiagent = LocalMAFMultiAgent(
                    ai_endpoint=ai_endpoint,
                    model_name=model_name,
                    api_server_url=api_server_url,
                    mcp_server_url=mcp_server_url,
                    tracer=tracer,
                    meter=meter,
                    agent_call_counter=agent_call_counter,
                    get_mock_user_context=get_mock_user_context,
                )
                await local_maf_multiagent.run()
            else:
                print("\n⚠️  AI_ENDPOINT not configured, skipping local-maf-multiagent scenario")
                logger.warning("AI_ENDPOINT not configured, skipping local-maf-multiagent scenario")

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
        available_scenarios = ["local-maf", "maf-with-fas", "local-maf-multiagent"]

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
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)

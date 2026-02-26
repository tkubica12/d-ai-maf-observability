"""Local Microsoft Agent Framework multi-agent with workflow orchestration (local-maf-multiagent)."""
from __future__ import annotations

import json
import logging
import os
import random
from typing import Any, Dict

import httpx
from agent_framework import (
    tool,
    MCPStreamableHTTPTool,
    WorkflowBuilder,
    Agent,
)
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import DefaultAzureCredential

# OpenTelemetry Baggage for cross-span context propagation
from opentelemetry import baggage, context

# Get logger from main
logger = logging.getLogger(__name__)


class LocalMAFMultiAgent:
    """Local Microsoft Agent Framework multi-agent with workflow orchestration (local-maf-multiagent)."""

    def __init__(
        self,
        ai_endpoint: str,
        model_name: str,
        api_server_url: str,
        mcp_server_url: str,
        tracer=None,
        meter=None,
        agent_call_counter=None,
        token_usage_counter=None,
        get_mock_user_context=None,
    ) -> None:
        self.ai_endpoint = ai_endpoint
        self.model_name = model_name
        self.api_server_url = api_server_url.rstrip("/")
        self.mcp_server_url = mcp_server_url.rstrip("/")
        self.tracer = tracer
        self.meter = meter
        self.agent_call_counter = agent_call_counter
        self.token_usage_counter = token_usage_counter
        self.get_mock_user_context = get_mock_user_context

    def _create_api_tool(self):
        """Create API tool for getting product of the day."""
        api_url = self.api_server_url
        tracer = self.tracer

        @tool(
            name="get_product_of_the_day",
            description="Get a randomly selected product of the day from the API server",
        )
        async def get_product_of_the_day() -> Dict[str, Any]:
            print(f"  🔧 [Worker] Tool call: get_product_of_the_day()")
            logger.info("Worker tool call", extra={"agent": "worker", "tool_name": "get_product_of_the_day", "arguments": {}})
            
            if tracer:
                span = tracer.start_as_current_span("worker.tool.get_product_of_the_day")
            else:
                from contextlib import nullcontext
                span = nullcontext()
                
            with span as s:
                if s:
                    s.set_attribute("agent.role", "worker")
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
                    
                    print(f"  📥 [Worker] Tool result: {result}")
                    logger.info("Worker tool result", extra={"agent": "worker", "tool_name": "get_product_of_the_day", "result": result})
                    return result

        return get_product_of_the_day

    async def _create_worker_agent(self):
        """Create worker agent with API and MCP tools."""
        credential = DefaultAzureCredential()
        
        responses_client = AzureOpenAIResponsesClient(
            base_url=f"{self.ai_endpoint.rstrip('/')}/openai/v1/",
            deployment_name=self.model_name,
            api_version="preview",
            credential=credential,
        )

        # Create API tool
        api_tool = self._create_api_tool()
        
        # Create MCP tool
        mcp_tool = MCPStreamableHTTPTool(
            name="stock_lookup_mcp",
            url=f"{self.mcp_server_url}/mcp",
        )
        
        # Create worker agent with tools
        worker_agent = responses_client.as_agent(
            instructions="""You are a specialized worker agent that provides product information and stock levels.

Your task is to:
1. Get the product of the day from the API
2. Look up the stock level for that product using its product_id via MCP
3. Return comprehensive information including product details and availability

Always use both tools to provide complete information. Be concise but thorough.""",
            name="WorkerAgent",
            tools=[api_tool, mcp_tool],
        )
        
        return worker_agent, mcp_tool

    async def run(self) -> None:
        """Run local MAF multi-agent with workflow orchestration."""
        print("\n" + "=" * 80)
        print("🔄 Local Microsoft Agent Framework Multi-Agent")
        print("   Scenario ID: local-maf-multiagent")
        print("   Pattern: Workflow Orchestration")
        print("=" * 80)

        # Generate mock user context
        user_context = self.get_mock_user_context() if self.get_mock_user_context else {}
        is_vip = "vip" in user_context.get("user.roles", [])
        print(f"👤 User Context: {user_context.get('user.id', 'N/A')} (VIP: {is_vip}, Dept: {user_context.get('organization.department', 'N/A')})")
        print(f"🧵 Session ID: {user_context.get('session.id', 'N/A')}")
        
        logger.info(
            "Starting local-maf-multiagent scenario with workflow orchestration",
            extra={
                "scenario_id": "local-maf-multiagent",
                "orchestration": "workflow",
                "user.id": user_context.get("user.id"),
                "user.roles": user_context.get("user.roles"),
                "organization.department": user_context.get("organization.department"),
                "session.id": user_context.get("session.id")
            }
        )

        # Create worker agent
        print("\n🔧 Creating worker agent...")
        worker_agent, mcp_tool = await self._create_worker_agent()
        
        async with mcp_tool:
            print("✅ Worker agent created with API and MCP tools")
            logger.info("Worker agent created with tools", extra={"agent": "worker"})

            # Create facilitator agent for workflow orchestration
            credential = DefaultAzureCredential()
            facilitator_client = AzureOpenAIResponsesClient(
                base_url=f"{self.ai_endpoint.rstrip('/')}/openai/v1/",
                deployment_name=self.model_name,
                api_version="preview",
                credential=credential,
            )

            facilitator_agent = facilitator_client.as_agent(
                name="FacilitatorAgent",
                instructions="You are a facilitator that synthesizes information from worker agents into a comprehensive, user-friendly response.",
            )

            print("🔧 Creating workflow orchestration...")
            print(f"🤖 Using model: {self.model_name}")
            logger.info("Creating workflow", extra={"model": self.model_name})

            # Build workflow chain
            workflow = WorkflowBuilder(start_executor=worker_agent).add_chain([worker_agent, facilitator_agent]).build()

            print("✅ Workflow created")
            logger.info("Workflow built successfully")

            user_message = "What's the product of the day and is it in stock?"
            print(f"\n📤 User → Workflow: {user_message}")
            logger.info("User message", extra={"user_message": user_message, "scenario": "local-maf-multiagent"})

            print("\n🤖 Workflow orchestration processing...")
            logger.info("Starting workflow orchestration execution")
            
            # Set baggage for automatic propagation to all child spans
            ctx = context.get_current()
            ctx = baggage.set_baggage("user.id", user_context.get("user.id", "unknown"), ctx)
            ctx = baggage.set_baggage("session.id", user_context.get("session.id", "unknown"), ctx)
            ctx = baggage.set_baggage("organization.department", user_context.get("organization.department", "unknown"), ctx)
            roles = user_context.get("user.roles", [])
            if roles:
                ctx = baggage.set_baggage("user.roles", ",".join(roles), ctx)
            
            # Attach context so baggage is active for this execution
            token = context.attach(ctx)
            
            try:
                # Record custom metric with dimensions
                if self.agent_call_counter:
                    demo_value = random.randint(1, 100)
                    is_vip = "vip" in user_context.get("user.roles", [])
                    self.agent_call_counter.add(
                        demo_value,
                        attributes={
                            "service.name": os.getenv("OTEL_SERVICE_NAME", "agent"),
                            "user.id": user_context.get("user.id", "unknown"),
                            "user.is_vip": str(is_vip).lower(),
                            "organization.department": user_context.get("organization.department", "unknown"),
                            "session.id": user_context.get("session.id", "unknown"),
                            "scenario_id": "local-maf-multiagent",
                            "scenario_type": "multi-agent",
                            "orchestration": "workflow",
                        }
                    )
                    print(f"📊 Custom metric recorded: custom_agent_call_count={demo_value}")
                    logger.info(
                        "Custom metric recorded",
                        extra={
                            "metric_name": "custom_agent_call_count",
                            "metric_value": demo_value,
                            "user.id": user_context.get("user.id"),
                            "scenario": "local-maf-multiagent",
                            "orchestration": "workflow"
                        }
                    )
            
                # Add scenario-specific attributes (baggage will auto-add user context)
                if self.tracer:
                    with self.tracer.start_as_current_span("scenario.local-maf-multiagent.workflow") as span:
                        span.set_attribute("scenario_id", "local-maf-multiagent")
                        span.set_attribute("scenario_type", "multi-agent")
                        span.set_attribute("orchestration", "workflow")
                        span.set_attribute("agent.pattern", "workflow-orchestration")
                        
                        result = await workflow.run(user_message)
                else:
                    result = await workflow.run(user_message)

                # Extract and display result
                if hasattr(result, "text"):
                    final_text = result.text
                elif hasattr(result, "content"):
                    final_text = result.content
                else:
                    final_text = str(result)

                print("\n" + "=" * 50)
                print("✨ FINAL RESULT:")
                print("=" * 50)
                print(final_text)
                print("=" * 50)

                print("\n✅ Workflow orchestration completed")
                logger.info(
                    "Multi-agent workflow completed with workflow orchestration",
                    extra={
                        "scenario": "local-maf-multiagent",
                        "orchestration": "workflow"
                    }
                )
            
            finally:
                # Detach context to clean up baggage
                context.detach(token)

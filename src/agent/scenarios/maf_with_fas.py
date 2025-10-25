"""Microsoft Agent Framework with Foundry Agent Service and API and MCP tools (maf-with-fas)."""
from __future__ import annotations

import json
import logging
import os
import random
from typing import Any, Dict

import httpx
from agent_framework import ai_function, HostedMCPTool
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential

# Get logger from main
logger = logging.getLogger(__name__)


class MAFWithFASAgent:
    """Microsoft Agent Framework with Foundry Agent Service and API and MCP tools (maf-with-fas)."""

    def __init__(
        self,
        project_endpoint: str,
        model_deployment: str,
        api_server_url: str,
        mcp_server_url: str,
        tracer=None,
        meter=None,
        agent_call_counter=None,
        get_mock_user_context=None,
    ) -> None:
        self.project_endpoint = project_endpoint
        self.model_deployment = model_deployment
        self.api_server_url = api_server_url.rstrip("/")
        self.mcp_server_url = mcp_server_url.rstrip("/")
        self.tracer = tracer
        self.meter = meter
        self.agent_call_counter = agent_call_counter
        self.get_mock_user_context = get_mock_user_context

    def _create_api_tool(self):
        """Create API tool for getting product of the day."""
        api_url = self.api_server_url
        tracer = self.tracer

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
        user_context = self.get_mock_user_context() if self.get_mock_user_context else {}
        print(f"👤 User Context: {user_context.get('user_id', 'N/A')} (VIP: {user_context.get('is_vip', False)}, Dept: {user_context.get('department', 'N/A')})")
        print(f"🧵 Thread ID: {user_context.get('thread_id', 'N/A')}")
        
        logger.info(
            "Starting maf-with-fas scenario",
            extra={
                "scenario_id": "maf-with-fas",
                "user_id": user_context.get("user_id"),
                "is_vip": user_context.get("is_vip"),
                "department": user_context.get("department"),
                "thread_id": user_context.get("thread_id")
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
                if self.agent_call_counter:
                    demo_value = random.randint(1, 100)
                    self.agent_call_counter.add(
                        demo_value,
                        attributes={
                            "service.name": os.getenv("OTEL_SERVICE_NAME", "agent"),
                            "user_id": user_context.get("user_id", "unknown"),
                            "is_vip": str(user_context.get("is_vip", False)).lower(),
                            "department": user_context.get("department", "unknown"),
                            "thread_id": user_context.get("thread_id", "unknown"),
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
                            "user_id": user_context.get("user_id"),
                            "scenario": "maf-with-fas"
                        }
                    )
                
                # Add custom dimensions to the span
                if self.tracer:
                    with self.tracer.start_as_current_span("scenario.maf-with-fas") as span:
                        span.set_attribute("user_id", user_context.get("user_id", "unknown"))
                        span.set_attribute("is_vip", user_context.get("is_vip", False))
                        span.set_attribute("department", user_context.get("department", "unknown"))
                        span.set_attribute("thread_id", user_context.get("thread_id", "unknown"))
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

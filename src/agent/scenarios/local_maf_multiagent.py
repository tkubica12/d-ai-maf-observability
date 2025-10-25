"""Local Microsoft Agent Framework multi-agent with Magentic orchestration (local-maf-multiagent)."""
from __future__ import annotations

import json
import logging
import os
import random
from typing import Any, Dict

import httpx
from agent_framework import (
    ai_function,
    MCPStreamableHTTPTool,
    MagenticBuilder,
    MagenticCallbackEvent,
    MagenticCallbackMode,
    MagenticAgentMessageEvent,
    MagenticOrchestratorMessageEvent,
    MagenticFinalResultEvent,
    ChatAgent,
)
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import DefaultAzureCredential

# Get logger from main
logger = logging.getLogger(__name__)


class LocalMAFMultiAgent:
    """Local Microsoft Agent Framework multi-agent with Magentic orchestration (local-maf-multiagent)."""

    def __init__(
        self,
        ai_endpoint: str,
        model_name: str,
        api_server_url: str,
        mcp_server_url: str,
        tracer=None,
        meter=None,
        agent_call_counter=None,
        get_mock_user_context=None,
    ) -> None:
        self.ai_endpoint = ai_endpoint
        self.model_name = model_name
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
            endpoint=self.ai_endpoint,
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
        worker_agent = responses_client.create_agent(
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
        """Run local MAF multi-agent with Magentic orchestration."""
        print("\n" + "=" * 80)
        print("🔄 Local Microsoft Agent Framework Multi-Agent")
        print("   Scenario ID: local-maf-multiagent")
        print("   Pattern: Magentic Orchestration")
        print("=" * 80)

        # Generate mock user context
        user_context = self.get_mock_user_context() if self.get_mock_user_context else {}
        print(f"👤 User Context: {user_context.get('user_id', 'N/A')} (VIP: {user_context.get('is_vip', False)}, Dept: {user_context.get('department', 'N/A')})")
        print(f"🧵 Thread ID: {user_context.get('thread_id', 'N/A')}")
        
        logger.info(
            "Starting local-maf-multiagent scenario with Magentic orchestration",
            extra={
                "scenario_id": "local-maf-multiagent",
                "orchestration": "magentic",
                "user_id": user_context.get("user_id"),
                "is_vip": user_context.get("is_vip"),
                "department": user_context.get("department"),
                "thread_id": user_context.get("thread_id")
            }
        )

        # Create worker agent
        print("\n🔧 Creating worker agent...")
        worker_agent, mcp_tool = await self._create_worker_agent()
        
        async with mcp_tool:
            print("✅ Worker agent created with API and MCP tools")
            logger.info("Worker agent created with tools", extra={"agent": "worker"})

            # Create Azure OpenAI Responses client for the Magentic manager
            credential = DefaultAzureCredential()
            responses_client = AzureOpenAIResponsesClient(
                endpoint=self.ai_endpoint,
                deployment_name=self.model_name,
                api_version="preview",
                credential=credential,
            )

            # Wrap the responses client in a ChatAgent for Magentic compatibility
            # The StandardMagenticManager will use this chat client
            manager_agent = ChatAgent(
                chat_client=responses_client,
                name="MagenticManager",
                instructions="You are a Magentic orchestrator managing specialized worker agents.",
            )

            print("🔧 Creating Magentic orchestration workflow...")
            print(f"🤖 Using model: {self.model_name}")
            logger.info("Creating Magentic workflow", extra={"model": self.model_name})

            # Create event callback for tracking orchestration
            async def on_event(event: MagenticCallbackEvent) -> None:
                if isinstance(event, MagenticOrchestratorMessageEvent):
                    # Manager's planning and coordination messages
                    message_text = getattr(event.message, 'text', '') if event.message else ''
                    print(f"\n[🎯 ORCHESTRATOR:{event.kind}]\n{message_text}\n{'-' * 40}")
                    logger.info(
                        "Orchestrator event",
                        extra={
                            "event_type": "orchestrator",
                            "kind": event.kind,
                            "message": message_text[:200]
                        }
                    )
                
                elif isinstance(event, MagenticAgentMessageEvent):
                    # Agent responses
                    msg = event.message
                    if msg is not None:
                        response_text = (msg.text or "").replace("\n", " ")
                        print(f"\n[🤖 AGENT:{event.agent_id}] {msg.role.value}\n{response_text[:200]}...\n{'-' * 40}")
                        logger.info(
                            "Agent response",
                            extra={
                                "event_type": "agent_message",
                                "agent_id": event.agent_id,
                                "role": msg.role.value,
                                "response_length": len(response_text)
                            }
                        )
                
                elif isinstance(event, MagenticFinalResultEvent):
                    # Final synthesized result
                    print("\n" + "=" * 50)
                    print("✨ FINAL RESULT:")
                    print("=" * 50)
                    if event.message is not None:
                        print(event.message.text)
                    print("=" * 50)
                    logger.info(
                        "Final result received",
                        extra={
                            "event_type": "final_result",
                            "has_message": event.message is not None
                        }
                    )

            # Build Magentic workflow with StandardMagenticManager
            workflow = (
                MagenticBuilder()
                .participants(worker=worker_agent)
                .on_event(on_event, mode=MagenticCallbackMode.NON_STREAMING)
                .with_standard_manager(
                    chat_client=responses_client,  # Use the responses client directly
                    max_round_count=10,
                    max_stall_count=3,
                    max_reset_count=2,
                )
                .build()
            )

            print("✅ Magentic workflow created")
            logger.info("Magentic workflow built successfully")

            user_message = "What's the product of the day and is it in stock?"
            print(f"\n📤 User → Workflow: {user_message}")
            logger.info("User message", extra={"user_message": user_message, "scenario": "local-maf-multiagent"})

            print("\n🤖 Magentic orchestration processing...")
            logger.info("Starting Magentic orchestration execution")
            
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
                        "scenario_id": "local-maf-multiagent",
                        "scenario_type": "multi-agent",
                        "orchestration": "magentic",
                    }
                )
                print(f"📊 Custom metric recorded: custom_agent_call_count={demo_value}")
                logger.info(
                    "Custom metric recorded",
                    extra={
                        "metric_name": "custom_agent_call_count",
                        "metric_value": demo_value,
                        "user_id": user_context.get("user_id"),
                        "scenario": "local-maf-multiagent",
                        "orchestration": "magentic"
                    }
                )
            
            # Add custom dimensions to the span and run workflow
            if self.tracer:
                with self.tracer.start_as_current_span("scenario.local-maf-multiagent.magentic") as span:
                    span.set_attribute("user_id", user_context.get("user_id", "unknown"))
                    span.set_attribute("is_vip", user_context.get("is_vip", False))
                    span.set_attribute("department", user_context.get("department", "unknown"))
                    span.set_attribute("thread_id", user_context.get("thread_id", "unknown"))
                    span.set_attribute("scenario_id", "local-maf-multiagent")
                    span.set_attribute("scenario_type", "multi-agent")
                    span.set_attribute("orchestration", "magentic")
                    span.set_attribute("agent.pattern", "magentic-orchestration")
                    
                    # Run workflow - events are handled by on_event callback
                    async for event in workflow.run_stream(user_message):
                        pass  # Events processed in callback
            else:
                # Run workflow without tracing
                async for event in workflow.run_stream(user_message):
                    pass  # Events processed in callback

            print("\n✅ Magentic orchestration completed")
            logger.info(
                "Multi-agent workflow completed with Magentic orchestration",
                extra={
                    "scenario": "local-maf-multiagent",
                    "orchestration": "magentic"
                }
            )

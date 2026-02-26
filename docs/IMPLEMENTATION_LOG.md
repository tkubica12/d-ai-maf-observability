# Implementation Log

## 2025-10-26: Langfuse Integration

Added Langfuse via Helm chart (in its own namespace) as an LLM-specific observability platform alongside Aspire Dashboard and Azure Monitor. The OTEL Collector was updated to export traces to Langfuse's OTLP HTTP endpoint using HTTP/protobuf (Langfuse does not support gRPC). This gives us multi-destination telemetry: Azure Monitor for enterprise monitoring, Aspire for dev debugging, and Langfuse for LLM cost tracking and prompt analysis.

## 2025-10-25: Prometheus Remote Write Sidecar

Implemented the Azure-recommended sidecar container pattern for Azure Monitor Prometheus remote write. The OTEL Collector's `prometheusremotewrite` exporter cannot natively acquire Azure AD tokens, so a Microsoft sidecar container (localhost:8081) handles workload-identity-based token acquisition and injects Authorization headers before forwarding to the Azure Monitor DCE endpoint.

## 2025-10-25: Multi-Agent Implementation

Added a facilitator-worker multi-agent pattern using MAF. The facilitator handles user interaction and delegates to a worker agent that has API and MCP tools. Agent code was refactored from a monolithic `main.py` into a `scenarios/` module with one class per scenario file for maintainability.

## 2025-10-24: Observability Fixes

Fixed trace context propagation by adding httpx and aiohttp client instrumentation so distributed traces span all services under a single trace_id. Fixed the custom metrics API (dict must be passed as `attributes=` keyword arg, not positional). Cleaned up console logging by suppressing library loggers to CRITICAL while preserving full telemetry via OTLP.

## 2025-10-24: Azure AI Agents SDK Fixes

Fixed API compatibility issues in the Foundry Agent Service approach to align with current Azure AI Agents SDK surface.

## 2025-01-XX: OpenTelemetry Implementation

Added three-signal observability (traces, metrics, logs) to all services using OTLP exporters pointed at `localhost:4317`. Manual spans capture business context (tool names, product IDs) while FastAPI auto-instrumentation covers the HTTP layer. Design choices: dual console+OTLP output, `OTEL_PYTHON_EXCLUDED_URLS` for health filtering, and manual instrumentation over `openinference-instrumentation-mcp` since FastMCP uses a different transport.

## 2025-10-20: Basic Service Implementation

Created the three core services: Agent (MAF + MCP client), MCP Server (FastMCP with function-calling tools), and API Server (FastAPI REST endpoints). All services use pyproject.toml with uv, .env-based configuration, and Python 3.12 Docker images. A demo mode allows running the agent without Azure credentials.

## 2025-10-20: Azure Integration and RBAC

Converted MCP Server from stdio to HTTP transport (port 8001) and added DefaultAzureCredential authentication across all services. Configured RBAC role assignments in Terraform using `random_uuid` resources (Terraform lacks a built-in `uuidv4()` function). Key architectural constraint: this project uses only the azapi provider — no azurerm.



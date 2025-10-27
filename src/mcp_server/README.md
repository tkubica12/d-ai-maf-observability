# MCP Server

FastMCP-based MCP (Model Context Protocol) server providing function calling tools to AI agents. Instrumented with OpenTelemetry for comprehensive distributed tracing.

## Available Tools

### get_product_stock
Get the current stock level for a specific product.

**Input**: 
- `product_id` (string) - Product identifier

**Output**:
```json
{
  "product_id": "LAPTOP001",
  "stock_count": 15,
  "available": true
}
```

**Products**:
- LAPTOP001, PHONE002, TABLET003, HEADSET004
- MONITOR005, KEYBOARD006, MOUSE007, SPEAKER008

### get_status
Get the status of the MCP server.

**Output**: `"MCP Server status: healthy"`

## Observability

### Automatic Instrumentation
- **MCP Protocol Instrumentation**: OpenInference MCP instrumentor
- **FastAPI Auto-Instrumentation**: HTTP layer automatically traced
- **Trace Context Propagation**: Receives and forwards trace context

### Manual Instrumentation
- **Custom Spans**: Tool-specific spans with `tool.name`, `tool.type`, and `product_id` attributes
- **Nested Spans**: Inner span for tool logic, outer span for MCP processing
- **Structured Logging**: OTLP logs with product details and results

### OTEL Configuration
Environment variables configured via Kubernetes deployment:
- `OTEL_EXPORTER_OTLP_ENDPOINT`: Collector endpoint (gRPC)
- `OTEL_SERVICE_NAME`: Service identifier (default: "mcp-server")
- `OTEL_PYTHON_EXCLUDED_URLS`: Health check endpoint excluded from traces

## Deployment

The MCP server runs as a Kubernetes deployment:

### Accessing the Service

**Internal (within cluster)**:
```
http://maf-demo-mcp-tool:8001/mcp
```

**External (via ingress)**:
```
https://mcp-tool.{your-domain}/mcp
```

### Testing from Outside Cluster

```powershell
# Get the ingress URL from Terraform
cd infra
$mcpUrl = terraform output -raw mcp_tool_url

# Test health endpoint
curl "$mcpUrl/health"

# Note: MCP protocol requires proper client, not direct curl
```

### Testing from Agent Container

The agent automatically connects to the MCP server using native MAF MCP tools:
- `MCPStreamableHTTPTool` (for local-maf scenarios)
- `HostedMCPTool` (for maf-with-fas scenarios)

## Endpoints

- **GET** `/health` - Health check (excluded from traces)
- **POST** `/mcp` - MCP protocol endpoint (SSE/streaming)
- **GET** `/mcp/sse` - Server-sent events for MCP communication

## Configuration

Environment variables (auto-configured in Kubernetes):
- `OTEL_EXPORTER_OTLP_ENDPOINT` - OTEL collector endpoint (required)
- `OTEL_SERVICE_NAME` - Service name for telemetry (default: "mcp-server")
- `HOST` - Bind address (default: "0.0.0.0")
- `PORT` - Listen port (default: 8001)

## Container Image

Built via ACR remote build tasks:

```powershell
# Build and push (from scripts directory)
cd scripts
uv run build_and_push.py
```

Image: `{acr-name}.azurecr.io/mcp-tool:{version}`

## Observability Features

### Trace Context Propagation
- Receives trace context from agent via MCP protocol
- Maintains context across streaming responses
- Creates child spans for all tool executions

### MCP Protocol Tracing
- Tool call request/response pairs
- Parameter serialization and validation
- Error handling and propagation
- Streaming response chunks

**Note on Trace Context Propagation**: Due to FastMCP Client architecture, trace context from agent to MCP server is not automatically propagated. MCP protocol expects trace context in JSON-RPC `params._meta` field, but FastMCP Client doesn't expose hooks to inject this. As a result, agent→MCP calls create separate trace IDs. MCP server-side instrumentation still captures all tool executions with full observability.

### Structured Logs
- Automatic correlation with traces
- Product lookup details
- Stock availability checks
- Exported to OTEL collector

### Metrics Export
- Tool invocation counts by tool name
- Tool execution duration
- Success/failure rates
- Exported to OTEL collector → Prometheus

## Architecture Integration

```
Agent (MAF)
    ↓ MCP Protocol
MCP Server (this service)
    ↓ Tool Execution
Internal Logic (stock data)
    ↓ OTLP
OTEL Collector
    ↓
Aspire Dashboard / Langfuse / Azure Monitor
```

The MCP server extends AI agent capabilities with function calling tools while maintaining full observability context throughout the execution chain.

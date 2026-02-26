# MCP Server

FastMCP-based Model Context Protocol server providing function calling tools to AI agents, instrumented with OpenTelemetry.

## Available Tools

### get_product_stock

Returns stock level for a product. Input: `product_id` (string). Output:

```json
{"product_id": "LAPTOP001", "stock_count": 15, "available": true}
```

Known product IDs: `LAPTOP001`, `PHONE002`, `TABLET003`, `HEADSET004`, `MONITOR005`, `KEYBOARD006`, `MOUSE007`, `SPEAKER008`.

### get_status

Returns `"MCP Server status: healthy"`.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (excluded from traces) |
| POST | `/mcp` | MCP protocol endpoint (SSE/streaming) |
| GET | `/mcp/sse` | Server-sent events for MCP communication |

## Configuration

| Variable | Description |
|----------|-------------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTEL collector endpoint (required) |
| `OTEL_SERVICE_NAME` | Service name for telemetry (default: `mcp-server`) |
| `HOST` | Bind address (default: `0.0.0.0`) |
| `PORT` | Listen port (default: `8001`) |

## Testing

```bash
# Internal (from agent container)
curl http://maf-demo-mcp-tool:8001/health

# External (via ingress) — health only; MCP protocol requires a proper client
curl "https://mcp-tool.{your-domain}/health"
```

## Trace Context Caveat

Due to FastMCP Client architecture, trace context from agent to MCP server is not automatically propagated — the client doesn't expose hooks to inject context into the JSON-RPC `params._meta` field. As a result, agent→MCP calls create separate trace IDs, though MCP server-side instrumentation still captures all tool executions.

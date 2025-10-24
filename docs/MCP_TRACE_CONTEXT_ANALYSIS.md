# MCP Trace Context Propagation Analysis

## Summary

After extensive research, here's what we discovered about trace context propagation with MCP (Model Context Protocol):

## Key Findings

### 1. `openinference-instrumentation-mcp` Package

**What it does:**
- Instruments **low-level MCP Python SDK** (`mcp.client.*` and `mcp.server.*`)
- Propagates trace context via `params._meta` field in JSON-RPC messages
- Works by wrapping MCP transport layers (stdio, sse, streamable-http)

**What it requires:**
- Application must use the official MCP Python SDK (`mcp>=1.6.0`)
- Both client AND server must be instrumented
- Works at the transport level (client/server transports)

### 2. Our Architecture

**Agent (Client) Side:**
- Uses `FastMCP.Client` (high-level wrapper)
- Makes HTTP calls via `httpx`
- **Does NOT use low-level `mcp.client` SDK**
- ❌ `MCPInstrumentor` on agent side won't help (wrong abstraction level)

**MCP Server Side:**
- Uses `FastMCP` server framework
- FastMCP internally uses `mcp.server` transports
- ✅ `MCPInstrumentor` CAN help (instruments underlying transports)

### 3. The Gap

**Problem:** Agent→MCP trace context not propagating because:

1. **HTTP Instrumentation** (`HTTPXClientInstrumentor`):
   - Adds `traceparent` header to HTTP requests
   - MCP protocol ignores HTTP headers
   - MCP expects context in JSON-RPC `params._meta` field

2. **FastMCP Client**:
   - Convenience wrapper around HTTP calls
   - Doesn't expose hooks to modify JSON-RPC `params._meta`
   - Not built with OpenTelemetry integration in mind

3. **Microsoft Agent Framework**:
   - Uses tools via HTTP/function calls
   - No MCP-specific trace propagation logic
   - Would need custom implementation

## Solutions

### Implemented (Agent-side metrics fix):

```python
# BEFORE: Agent Framework setup_observability() doesn't configure metrics export
meter = get_meter(__name__)  # Returns meter but no global provider set

# AFTER: Manually set global MeterProvider before setup_observability()
meter_provider = MeterProvider(resource=metric_resource, metric_readers=[metric_reader])
otel_metrics.set_meter_provider(meter_provider)  # Global provider set
setup_observability(...)  # Now traces work
meter = meter_provider.get_meter(__name__)  # Get meter from our provider
```

✅ **Result**: Custom agent metrics now export correctly

### Implemented (MCP Server-side):

```python
# MCP Server gets MCP instrumentation
from openinference.instrumentation.mcp import MCPInstrumentor
MCPInstrumentor().instrument(tracer_provider=tracer_provider)
```

✅ **Result**: FastMCP server transport layer is instrumented

### Still Missing (Trace Propagation):

**Agent→MCP trace context** still doesn't propagate because:

1. **FastMCP Client** doesn't support injecting context into `params._meta`
2. **httpx instrumentation** only adds HTTP headers (not used by MCP protocol)
3. Need custom middleware/wrapper to inject context

**Potential Solutions:**

#### Option A: Custom FastMCP Client Wrapper
```python
from opentelemetry import trace, propagate, context

class TracedMCPClient:
    def __init__(self, base_url):
        self.client = Client(base_url)
    
    async def call_tool(self, name: str, arguments: dict):
        # Inject trace context into params._meta
        ctx_carrier = {}
        propagate.inject(ctx_carrier)
        
        # Modify the request to include _meta
        if not arguments:
            arguments = {}
        arguments["_meta"] = ctx_carrier
        
        return await self.client.call_tool(name, arguments)
```

#### Option B: Fork/PR FastMCP
- Add OpenTelemetry support to FastMCP client
- Automatically inject trace context
- Submit PR to jlowin/fastmcp

#### Option C: Use Low-Level MCP SDK
```python
# Instead of FastMCP Client, use official mcp.client
from mcp.client.streamable_http import streamablehttp_client
from openinference.instrumentation.mcp import MCPInstrumentor

MCPInstrumentor().instrument()  # Now it works!
```

## Current State

### ✅ Working:
- Agent→API trace correlation (httpx instrumentation)
- API server metrics export
- MCP server metrics export (after fix)
- Agent custom metrics export (after fix)

### ❌ Not Working:
- Agent→MCP trace correlation (FastMCP Client limitation)

### ⚠️ Workaround:
- Accept that Agent→MCP traces won't be correlated
- MCP server traces still captured (just separate trace_id)
- For demo purposes, this may be acceptable

## Recommendations

1. **Short-term (Demo)**: Accept separate traces for Agent→MCP calls
2. **Medium-term**: Implement Option A (custom wrapper) for trace injection
3. **Long-term**: Option B (contribute to FastMCP) or Option C (switch to low-level SDK)

## References

- [OpenInference MCP Instrumentation](https://github.com/Arize-ai/openinference/tree/main/python/instrumentation/openinference-instrumentation-mcp)
- [Arize Phoenix MCP Tracing Docs](https://arize.com/docs/phoenix/integrations/python/mcp-tracing)
- [Google ADK Issue #3063](https://github.com/google/adk-python/issues/3063) - Similar problem with MCP trace propagation

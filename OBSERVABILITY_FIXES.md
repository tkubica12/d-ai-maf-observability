# Observability Issues and Fixes

## Issues Identified

### 1. Custom Metrics from Agent NOT Received ❌
**Problem**: Agent Framework's custom metrics not appearing in OTEL backend  
**Root Cause**: `agent_call_counter.add()` was using incorrect API - dict as positional argument instead of `attributes=` named parameter

**Fix Applied**:
```python
# WRONG (old)
agent_call_counter.add(demo_value, {...})

# CORRECT (new)
agent_call_counter.add(demo_value, attributes={...})
```

### 2. Metrics from FastAPI API Service Working ✅
No issues - properly configured with MeterProvider.

### 3. Metrics from FastMCP Server NOT Coming ❌
**Problem**: MCP server metrics not being exported despite configuration  
**Root Cause**: FastMCP's underlying FastAPI app needs to be instrumented AFTER mcp.run() is configured, or the instrumentation timing is off

**Current Status**: Code looks correct but may need runtime verification. The instrumentation is:
```python
FastAPIInstrumentor.instrument_app(mcp.app, meter_provider=meter_provider)
```

**Verification Needed**: Check if `mcp.app` exists before `mcp.run()` is called.

### 4. Trace Context NOT Propagated (Agent → API/MCP) ❌
**Problem**: Traces from agent, API, and MCP are independent - no parent-child relationship  
**Root Cause**: httpx and aiohttp HTTP clients not instrumented to inject trace context headers (traceparent, tracestate)

**Fix Applied**:
```python
# Added to agent/main.py
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor

HTTPXClientInstrumentor().instrument()
AioHttpClientInstrumentor().instrument()
```

**How it works**:
- Agent makes HTTP request → httpx instrumentation injects `traceparent` header with current trace context
- API/MCP receive request → FastAPI instrumentation extracts `traceparent` and creates child span
- Result: Complete distributed trace from agent → API/MCP

### 5. Logs Working Fine ✅
All structured logging to OTLP working correctly, console output cleaned up.

## Changes Made

### src/agent/main.py
1. ✅ Added httpx instrumentation: `HTTPXClientInstrumentor().instrument()`
2. ✅ Added aiohttp instrumentation: `AioHttpClientInstrumentor().instrument()`
3. ✅ Fixed custom metric API: Changed to `attributes=` parameter
4. ✅ Removed all console logging (only OTLP)
5. ✅ Added friendly print for metric recording

### src/agent/Dockerfile
1. ✅ Added 15-second sleep before starting agent to wait for API/MCP readiness

## Testing Checklist

After rebuilding and redeploying:

### Metrics
- [ ] Agent: `custom_agent_call_count` appears in OTEL backend with dimensions (user_id, is_vip, department, scenario_id, thread_id)
- [ ] API: FastAPI HTTP metrics (`http.server.duration`, `http.server.request.size`, etc.) present
- [ ] MCP: FastAPI HTTP metrics present (may need code adjustment if not working)

### Traces
- [ ] Agent creates root span
- [ ] API requests show as child spans of agent span (same trace_id)
- [ ] MCP requests show as child spans of agent span (same trace_id)
- [ ] Custom spans visible: `api.tool.process_product_request`, `mcp.tool.process_stock_lookup`, `mcp.get_product_stock`

### Trace Propagation Verification
Query your OTEL backend:
```kusto
// Find agent trace
traces
| where service_name == "agent"
| take 1
| project trace_id

// Check if same trace_id exists in api-tool and mcp-tool
traces
| where trace_id == "<agent_trace_id_from_above>"
| summarize services = make_set(service_name)
// Should show: ["agent", "api-tool", "mcp-tool"]
```

### Logs
- [x] All services sending structured logs to OTLP
- [x] No console spam from libraries in agent

## Dependencies

Ensure these packages are installed (already in pyproject.toml):

**Agent**:
- `opentelemetry-instrumentation-httpx>=0.51b0` ✅
- `opentelemetry-instrumentation-aiohttp-client>=0.51b0` ✅

**API Server**:
- `opentelemetry-instrumentation-fastapi>=0.51b0` ✅

**MCP Server**:
- `opentelemetry-instrumentation-fastapi>=0.51b0` ✅

## Known Limitations

1. **Agent Framework Metrics Export**: The Agent Framework's `setup_observability()` should configure metrics export via OTLP, but if custom metrics still don't appear, may need to manually configure MeterProvider similar to how we did for logs.

2. **FastMCP Timing**: The MCP server instrumentation happens before `mcp.run()`. If metrics still don't appear, we may need to instrument after the app is fully initialized.

## Debugging Tips

### Check Trace Propagation
```python
# In agent code after HTTP call, print headers sent:
print(f"Request headers: {response.request.headers}")
# Should see: traceparent: 00-<trace_id>-<span_id>-01
```

### Verify Metric Export
```python
# Add after metric recording:
from opentelemetry import metrics as metrics_api
meter_provider = metrics_api.get_meter_provider()
print(f"MeterProvider: {type(meter_provider)}")
# Should be: MeterProvider (not _DefaultMeterProvider)
```

### MCP Server App Reference
```python
# Check if mcp.app is available before run():
if hasattr(mcp, 'app'):
    print(f"MCP app type: {type(mcp.app)}")
    # Should show FastAPI app instance
```

## Next Steps

1. Rebuild containers: `uv run .\build_and_push.py`
2. Redeploy to K8s: `helm upgrade ...`
3. Run agent and verify all telemetry
4. Query OTEL backend to confirm:
   - Custom metrics present
   - Traces properly correlated across services
   - Logs structured and complete

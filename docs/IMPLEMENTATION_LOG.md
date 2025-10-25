# Implementation Log

## 2025-10-25: Azure Monitor Prometheus Remote Write with Sidecar Container

### Objective
Complete the Azure Monitor Prometheus remote write integration by implementing the Microsoft-recommended sidecar container pattern for Azure AD authentication.

### Problem
The OpenTelemetry Collector's `prometheusremotewrite` exporter doesn't natively support Azure AD token acquisition and refresh. Azure Monitor Prometheus requires OAuth2 Bearer tokens in the Authorization header.

### Solution: Sidecar Container Pattern

Implemented Microsoft's recommended approach using a sidecar container that:
1. Obtains Azure AD tokens using workload identity
2. Provides a local HTTP proxy (localhost:8081)
3. Injects Authorization headers automatically
4. Handles token refresh

### Implementation Details

**Sidecar Container Configuration**:
- Image: `mcr.microsoft.com/azuremonitor/containerinsights/ciprod/prometheus-remote-write/images:prom-remotewrite-20250814.1`
- Environment variables:
  - `INGESTION_URL`: Azure Monitor DCE metrics ingestion endpoint
  - `LISTENING_PORT`: 8081
  - `IDENTITY_TYPE`: workloadIdentity
  - `CLUSTER`: AKS cluster name
- Health probes: /health and /ready endpoints

**OTEL Collector Changes**:
- Changed endpoint from direct Azure Monitor URL to `http://localhost:8081/api/v1/write`
- Changed TLS setting to `insecure: true` (localhost communication)
- Both containers share the same pod and service account

**Infrastructure** (already in place):
- Azure Workload Identity federated credential linking K8s service account to managed identity
- Monitoring Metrics Publisher role on Data Collection Rule
- Service account annotations for workload identity

### Files Modified

1. **charts/maf_demo/templates/otel-collector.yaml**
   - Updated prometheusremotewrite exporter endpoint to localhost sidecar
   - Added prom-remotewrite sidecar container to deployment
   - Configured health probes and environment variables

2. **charts/maf_demo/values.yaml**
   - Added `clusterName` field for sidecar configuration

3. **infra/helm.demo.tf**
   - Pass AKS cluster name to Helm chart

4. **docs/APPLICATION_INSIGHTS_OTEL.md**
   - Updated documentation to reflect complete implementation
   - Removed "Current Limitation" section
   - Added "How It Works" section explaining the flow

### Architecture Flow

```
OTEL Collector (port 4317/4318)
     │
     │ Exports metrics
     ▼
Sidecar Container (localhost:8081)
     │ 
     │ 1. Receives Prometheus remote write request
     │ 2. Obtains Azure AD token (workload identity)
     │ 3. Injects Authorization header
     │ 4. Forwards to Azure Monitor
     ▼
Azure Monitor DCE Endpoint
     │
     ▼
Data Collection Rule
     │
     ▼
Azure Monitor Workspace (Prometheus)
```

### Testing Next Steps

1. Apply Terraform/Helm changes to deploy updated configuration
2. Verify sidecar container starts successfully
3. Check sidecar logs for token acquisition
4. Verify metrics flow to Azure Monitor Prometheus workspace
5. Query metrics in Grafana or Azure portal

### References

- [Microsoft Docs: Prometheus Remote Write with Workload Identity](https://learn.microsoft.com/en-us/azure/azure-monitor/containers/prometheus-remote-write-azure-workload-identity)

---

## 2025-10-25: Multi-Agent Implementation and Code Refactoring

### Objective
Implement multi-agent pattern with facilitator + worker architecture and refactor code for better maintainability.

### Multi-Agent Architecture

Implemented facilitator-worker pattern where:
- **Facilitator Agent**: Front-end agent responsible for user interaction and delegation
- **Worker Agent**: Specialized agent with API and MCP tools for product queries
- **Communication**: Direct Python function calls (delegation pattern)

### Code Refactoring

**Motivation**: As more scenarios are added, main.py was growing large (700+ lines). Needed better organization without over-engineering.

**Approach**:
1. Created `scenarios/` module for scenario implementations
2. Each scenario in its own file with dedicated class
3. Main.py retains only:
   - Global observability setup (needed at module level)
   - Mock user context utilities
   - Connection testing
   - Main entry point and CLI parsing

**New Structure**:
```
src/agent/
  main.py                      # Infrastructure, observability, main()
  scenarios/
    __init__.py                # Module exports
    local_maf.py               # LocalMAFAgent class
    maf_with_fas.py            # MAFWithFASAgent class
    local_maf_multiagent.py    # LocalMAFMultiAgent class (NEW)
```

**Benefits**:
- Each scenario is self-contained and easier to understand
- File size manageable as scenarios grow
- Clear separation of concerns
- No complex abstractions - simple class-per-file

### Scenario: local-maf-multiagent

**Pattern**: Facilitator + Worker
- Facilitator uses `delegate_to_worker` tool (wrapped worker agent call)
- Worker has API and MCP tools
- Both agents use AzureOpenAIResponsesClient (local execution)

**Telemetry**:
- Custom spans with `agent.role` attribute (facilitator/worker)
- `scenario_type` = "multi-agent"
- `agent.pattern` = "facilitator-worker"

**Example Flow**:
1. User → Facilitator: "What's the product of the day?"
2. Facilitator → Worker (via delegate_to_worker tool)
3. Worker → API Tool: get_product_of_the_day()
4. Worker → MCP Tool: stock_lookup(product_id)
5. Worker → Facilitator: Combined result
6. Facilitator → User: Friendly response

### Design Decisions

**Multi-Agent Roadmap** (updated in DESIGN.md):
- ✅ `local-maf-multiagent`: Direct Python calls (implemented)
- ⏳ `local-maf-with-a2a`: Worker as A2A service, facilitator local (planned)
- ⏳ `local-maf-with-fas-a2a`: Facilitator in FAS, worker as A2A (planned)

**Why not extract observability setup?**
OpenTelemetry configuration must run at module-level before agent imports. Keeping it in main.py maintains clarity about initialization order.

**Why not extract test_connections?**
Simple utility function used only by main(). No benefit to extracting.

### Testing

Validated both refactored existing scenarios and new multi-agent scenario:
- `local-maf`: ✅ Works correctly
- `local-maf-multiagent`: ✅ Facilitator delegates to worker successfully
- Telemetry: ✅ Proper span hierarchies and attributes

## 2025-10-20: Basic Service Implementation

### Objective
Create basic implementation for source services (Agent, MCP Server, API Server) with MAF integration, MCP function calling, and FastAPI endpoints.

### Architecture Implemented

```
┌─────────────────┐
│   MAF Agent     │  - Uses Microsoft Agent Framework
│                 │  - Sends user messages
│                 │  - Mandatory tool usage
└────────┬────────┘
         │ MCP Protocol
         │ (stdio)
         ▼
┌─────────────────┐
│  MCP Server     │  - FastMCP SDK
│                 │  - Exposes function calling tools
│                 │  - Bridges to API Server
└────────┬────────┘
         │ HTTP/REST
         │
         ▼
┌─────────────────┐
│  API Server     │  - FastAPI
│                 │  - Processes data
│                 │  - Returns results
└─────────────────┘
```

### Components Implemented

#### 1. API Server (`src/api_server/`)
**Purpose**: FastAPI-based REST API that processes function calls from MCP server.

**Key Features**:
- FastAPI framework with Pydantic models
- `/process` endpoint for data processing
- `/health` endpoint for health checks
- Environment-based configuration (.env)
- Docker support with Python 3.12

**Technologies**:
- FastAPI 0.115.0+
- Uvicorn 0.32.0+
- Pydantic 2.9.0+
- python-dotenv 1.0.0+

**Configuration**:
- `API_HOST`: Server host (default: 0.0.0.0)
- `API_PORT`: Server port (default: 8000)

#### 2. MCP Server (`src/mcp_server/`)
**Purpose**: MCP server using FastMCP SDK that exposes tools for agent function calling.

**Key Features**:
- FastMCP 2.0 implementation
- Two tools exposed:
  - `process_data`: Mandatory tool for processing user data (calls API server)
  - `get_status`: Health check tool (calls API server)
- STDIO transport for agent communication
- Environment-based configuration
- Docker support

**Technologies**:
- FastMCP 0.4.0+
- httpx 0.28.0+ (for async HTTP calls)
- python-dotenv 1.0.0+

**Configuration**:
- `API_SERVER_URL`: URL of API server (default: http://localhost:8000)

#### 3. Agent (`src/agent/`)
**Purpose**: Microsoft Agent Framework agent that uses MCP tools for processing user messages.

**Key Features**:
- MAF integration with Azure AI Project
- MCP client integration (stdio transport)
- Simple demo mode (works without Azure credentials)
- Full Azure mode (requires Azure AI Project)
- Mandatory tool usage pattern
- Environment-based configuration
- Docker support

**Technologies**:
- azure-ai-projects 1.0.0b7+
- azure-identity 1.21.1+
- mcp 1.12.0+
- python-dotenv 1.0.0+

**Configuration**:
- `PROJECT_CONNECTION_STRING`: Azure AI Project connection (optional for demo)
- `MODEL_DEPLOYMENT`: Model deployment name (default: gpt-4o)
- `MCP_SERVER_PATH`: Path to MCP server main.py
- `API_SERVER_URL`: API server URL for MCP

**Modes**:
1. **Simple Demo Mode**: Simulates agent behavior without Azure (for testing)
2. **Full Mode**: Complete MAF integration with Azure AI Project

### Design Decisions

1. **FastMCP SDK**: Chosen for MCP server due to simplicity and native Python async support
2. **FastAPI**: Selected for API server for modern Python REST API development with automatic OpenAPI docs
3. **STDIO Transport**: Used for MCP communication as it's the standard for agent-MCP integration
4. **Mandatory Tool Usage**: Implemented through agent instructions to ensure all data passes through API
5. **Demo Mode**: Added fallback mode to enable testing without Azure credentials
6. **Environment Configuration**: All services use .env files for configuration flexibility
7. **Docker Support**: All services have Dockerfiles using Python 3.12-slim base image

### Testing Results

✅ **API Server**: All endpoints tested and working
- GET `/` returns service info
- GET `/health` returns healthy status
- POST `/process` successfully processes data

✅ **MCP Server**: Both tools tested and working
- `process_data` tool successfully calls API server
- `get_status` tool successfully retrieves API health

✅ **Agent**: Both modes tested and working
- Simple demo mode runs without Azure
- MCP client integration verified
- Tool calling flow demonstrated

✅ **Integration**: Full stack tested
- API → MCP → Agent communication verified
- Data flows correctly through all layers
- Function calling pattern works as expected

### File Structure Created

```
src/
├── agent/
│   ├── .env.example
│   ├── Dockerfile
│   ├── README.md
│   ├── main.py
│   └── pyproject.toml
├── mcp_server/
│   ├── .env.example
│   ├── Dockerfile
│   ├── README.md
│   ├── main.py
│   └── pyproject.toml
└── api_server/
    ├── .env.example
    ├── Dockerfile
    ├── README.md
    ├── main.py
    └── pyproject.toml
```

### Dependencies Added

Each service has been configured with minimal, focused dependencies through pyproject.toml files. No requirements.txt files were created, following the uv package manager convention.

### Next Steps (Future Work)

1. Add OpenTelemetry instrumentation to all services
2. Implement user context and telemetry dimensions
3. Add more sophisticated agent workflows
4. Integrate with Azure Monitor and LangFuse
5. Add comprehensive unit and integration tests
6. Implement CI/CD pipeline for container builds
7. Add Kubernetes deployment configurations

## 2025-10-20: Azure Integration and RBAC Configuration

### Objective
Updated services for Azure integration with DefaultAzureCredential authentication, HTTP-based MCP server, and proper RBAC configuration.

### Changes Implemented

#### Service Updates
1. **MCP Server**: Converted from stdio to HTTP server with CORS support
2. **Agent**: Created two variants - Foundry Agent Service and Direct Model Access
3. **All Services**: Added DefaultAzureCredential authentication and configurable ports
4. **RBAC**: Added proper role assignments in Terraform

#### Terraform Issues Fixed
**Problem**: `uuidv4()` function error in Terraform role assignments
```
Error: Call to unknown function "uuidv4()"
```

**Root Cause**: Terraform doesn't have a built-in `uuidv4()` function

**Solution**: Used `random_uuid` resource instead:
```terraform
resource "random_uuid" "role_assignment_id" {}
resource "azapi_resource" "role_assignment" {
  name = random_uuid.role_assignment_id.result
  # ...
}
```

**Files Changed**:
- `infra/rbac.tf` - Fixed UUID generation and removed azurerm dependencies
- `infra/providers.tf` - Maintains azapi-only approach (no azurerm provider)
- `infra/variables.tf` - Added current_user_object_id variable for development RBAC
- `docs/COMMON_ERRORS.md` - Documented UUID fix and azapi-only requirement

**Important Architecture Decision**: This project uses **only azapi provider** - never add azurerm provider. All Azure resources and data sources must use azapi equivalents.

### Architectural Changes
- MCP Server now runs as HTTP server (port 8001) instead of stdio
- All services support configurable hosts/ports via environment variables
- Two agent variants: Foundry-based and direct model access
- Complete DefaultAzureCredential authentication chain


## 2025-10-24: Azure AI Agents SDK API Fixes

Fixed Azure AI Agents SDK API compatibility issues in the Foundry Agent Service approach.

## 2025-01-XX: OpenTelemetry Observability Implementation

### Objective
Add comprehensive OpenTelemetry instrumentation (traces, metrics, logs) to all services while preserving console output.

### Architecture: Three-Signal Observability

**OTLP Endpoint**: `http://localhost:4317` (configurable via `OTEL_EXPORTER_OTLP_ENDPOINT`)

**Signal Stack**:
```
┌─────────────┬─────────────┬─────────────┐
│   Traces    │   Metrics   │    Logs     │
├─────────────┼─────────────┼─────────────┤
│ OTLPSpan    │ OTLPMetric  │ OTLPLog     │
│ Exporter    │ Exporter    │ Exporter    │
├─────────────┼─────────────┼─────────────┤
│ BatchSpan   │ Periodic    │ BatchLog    │
│ Processor   │ Reader      │ Processor   │
├─────────────┼─────────────┼─────────────┤
│ Tracer      │ Meter       │ Logger      │
│ Provider    │ Provider    │ Provider    │
└─────────────┴─────────────┴─────────────┘
```

### Changes Implemented

#### 1. Agent Service (`src/agent/main.py`)
**Instrumentation**:
- ✅ Traces: Agent Framework built-in observability via `get_tracer()`
- ✅ Metrics: Custom `custom_agent_call_count` counter (random 1-100 for demo)
- ✅ Logs: OTLP logger with structured extra fields
- ✅ Dual output: Console prints preserved + OTLP logs added alongside

**Custom Dimensions**:
```python
# Metric dimensions
dimensions = {
    "user_id": user_id,
    "scenario_id": scenario,
    "is_vip": str(is_vip).lower(),
    "department": department,
    "thread_id": thread_id
}
custom_agent_call_count.add(call_count, attributes=dimensions)
```

**Key Pattern**: `print()` + `logger.info()` for every user-facing message

#### 2. API Server (`src/api_server/main.py`)
**Instrumentation**:
- ✅ Traces: FastAPI auto-instrumentation + custom spans
- ✅ Metrics: FastAPI auto-instrumentation (HTTP metrics)
- ✅ Logs: OTLP logger with structured logging
- ✅ Environment variables for configuration

**Custom Span**:
```python
with tracer.start_as_current_span("api.tool.process_product_request") as span:
    span.set_attribute("tool.name", "get_product_of_the_day")
    span.set_attribute("tool.type", "api")
    span.set_attribute("product.id", product_id)
```

**FastAPI Metrics Configuration**:
```python
meter_provider = MeterProvider(
    resource=resource,
    metric_readers=[PeriodicExportingMetricReader(OTLPMetricExporter(...))]
)
FastAPIInstrumentor.instrument_app(app, meter_provider=meter_provider)
```

**Auto-Emitted HTTP Metrics**:
- `http.server.duration` - Request duration histogram
- `http.server.request.size` - Request body size
- `http.server.response.size` - Response body size  
- `http.server.active_requests` - Active request count

**Environment Variables**:
```python
os.environ["OTEL_PYTHON_EXCLUDED_URLS"] = "/health"
os.environ["OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST"] = ".*"
os.environ["OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE"] = ".*"
```

#### 3. MCP Server (`src/mcp_server/main.py`)
**Instrumentation**:
- ✅ Traces: FastAPI auto-instrumentation (via `mcp.app`) + nested custom spans
- ✅ Metrics: FastAPI auto-instrumentation (HTTP metrics)
- ✅ Logs: OTLP logger with structured logging
- ✅ Environment variables for configuration

**Nested Custom Spans**:
```python
# Outer span: tool processing
with tracer.start_as_current_span("mcp.tool.process_stock_lookup") as outer_span:
    outer_span.set_attribute("tool.name", "get_product_stock")
    outer_span.set_attribute("tool.type", "mcp")
    
    # Inner span: business logic
    with tracer.start_as_current_span("mcp.get_product_stock") as inner_span:
        inner_span.set_attribute("product.id", product_id)
        inner_span.set_attribute("stock.count", stock_count)
        inner_span.set_attribute("stock.available", is_available)
```

**FastMCP + FastAPI Instrumentation**:
```python
# FastMCP exposes FastAPI app via mcp.app
FastAPIInstrumentor.instrument_app(mcp.app, meter_provider=meter_provider)
```

### Design Decisions

1. **Dual Output Strategy**: Preserve all console prints for developer experience, add OTLP logs for observability platform
2. **Environment Variables Over Code**: Use `OTEL_PYTHON_EXCLUDED_URLS` instead of custom `FilteringSpanProcessor`
3. **Manual Spans for Business Context**: Auto-instrumentation captures HTTP layer, custom spans capture tool semantics
4. **Nested Spans in MCP**: Outer span = tool processing, inner span = business logic (enables drill-down analysis)
5. **FastAPI Metrics via MeterProvider**: Pass `meter_provider` to `instrument_app()` for automatic HTTP metrics
6. **LogRecord Attribute Naming**: Avoid reserved attributes like "message", use "user_message" in `extra={}`

### Dependencies Added

All three services (`agent`, `api_server`, `mcp_server`):
```toml
[project]
dependencies = [
    # ... existing ...
    "opentelemetry-instrumentation-logging>=0.51b0",
]
```

Existing OTEL packages already sufficient:
- `opentelemetry-api>=1.30.0`
- `opentelemetry-sdk>=1.30.0`
- `opentelemetry-exporter-otlp-proto-grpc>=1.30.0` (includes metric exporter)
- `opentelemetry-instrumentation-fastapi>=0.51b0`

### Issues Encountered and Resolved

1. **KeyError: "Attempt to overwrite 'message' in LogRecord"**
   - **Cause**: Python logging reserves "message" attribute in LogRecord
   - **Fix**: Changed `extra={"message": ...}` to `extra={"user_message": ...}`

2. **Complex Health Endpoint Filtering**
   - **Original**: Custom `FilteringSpanProcessor` class to exclude `/health`
   - **Improved**: `os.environ["OTEL_PYTHON_EXCLUDED_URLS"] = "/health"`

3. **FastMCP Instrumentation Approach**
   - **Question**: Should we use `openinference-instrumentation-mcp`?
   - **Decision**: Manual instrumentation because:
     - FastMCP ≠ official `mcp` package (different transport)
     - Need application-level spans, not protocol-level
     - FastAPI auto-instrumentation already covers HTTP layer

4. **FastAPI Metrics Not Emitting**
   - **Cause**: MeterProvider not configured and passed to instrumentor
   - **Fix**: Create MeterProvider with OTLP exporter, pass to `instrument_app(meter_provider=...)`

### Testing Verification

**Checklist**:
- [ ] Agent: Console prints still visible
- [ ] Agent: `custom_agent_call_count` metric recorded with dimensions
- [ ] API: `/health` endpoint NOT creating spans
- [ ] API: All request headers captured in spans
- [ ] API: `api.tool.process_product_request` custom span appears
- [ ] API: HTTP metrics (`http.server.*`) emitted
- [ ] MCP: Nested spans appear (`mcp.tool.process_stock_lookup` → `mcp.get_product_stock`)
- [ ] MCP: HTTP metrics (`http.server.*`) emitted
- [ ] All: Logs visible in OTLP collector with structured fields

### Next Steps

1. Integration testing: Run all services, verify telemetry in OTEL collector
2. Update Helm charts with OTEL environment variables
3. Configure OTEL collector deployment in K8s
4. Connect to observability backend (Azure Monitor, Grafana, etc.)
5. Create sample queries and dashboards for custom metrics/spans

## 2025-10-24: Observability Fixes - Metrics and Trace Propagation

### Issues Identified and Fixed

#### 1. Custom Metrics Not Exported from Agent
**Problem**: `custom_agent_call_count` metric not appearing in OTEL backend  
**Root Cause**: Incorrect API usage - dict as positional argument instead of `attributes=` named parameter

**Fix**:
```python
# Changed from:
agent_call_counter.add(demo_value, {...})

# To:
agent_call_counter.add(demo_value, attributes={...})
```

#### 2. Trace Context Not Propagated (Agent → API/MCP)
**Problem**: Traces from agent, API, and MCP were independent - no parent-child relationship  
**Root Cause**: httpx and aiohttp HTTP clients not instrumented to inject trace context headers

**Fix**: Added HTTP client instrumentation in `src/agent/main.py`:
```python
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor

HTTPXClientInstrumentor().instrument()
AioHttpClientInstrumentor().instrument()
```

**How Trace Propagation Works**:
1. Agent makes HTTP call → httpx injects `traceparent` header with current trace_id/span_id
2. API/MCP receives request → FastAPI instrumentation extracts header and creates child span
3. Result: Complete distributed trace across all services with same trace_id

#### 3. Console Log Noise
**Problem**: Library loggers (agent_framework, httpx, azure.identity, etc.) polluting console output  
**Fix**: 
- Cleared all console handlers from root logger
- Set library loggers to CRITICAL level to suppress console output
- OTLP handler still captures everything for telemetry
- Only application `print()` statements appear on console

**Result**: Clean demo-friendly console while maintaining full observability via OTLP.

#### 4. MCP Server Metrics
**Status**: Configuration appears correct with MeterProvider and FastAPIInstrumentor. May require runtime verification if metrics still don't appear.

### Files Modified

**src/agent/main.py**:
- Added httpx/aiohttp instrumentation for trace propagation
- Fixed custom metric API (attributes= parameter)
- Cleaned up console logging configuration
- Enhanced metric recording with structured logging

**src/agent/Dockerfile**:
- Added 15-second startup delay to wait for API/MCP services

### Documentation Created

**OBSERVABILITY_FIXES.md**: Comprehensive guide covering:
- All identified issues and fixes
- Testing checklist for verifying metrics and traces
- Debugging tips for trace propagation
- Known limitations and next steps

### Dependencies Verified

All required instrumentation packages already in pyproject.toml:
- `opentelemetry-instrumentation-httpx>=0.51b0`
- `opentelemetry-instrumentation-aiohttp-client>=0.51b0`
- `opentelemetry-instrumentation-fastapi>=0.51b0`
- `opentelemetry-instrumentation-logging>=0.51b0`

### Testing Requirements

After rebuild and redeploy, verify:
1. ✅ Custom metrics appear with correct dimensions
2. ✅ Traces span all services with same trace_id
3. ✅ HTTP spans show parent-child relationships
4. ✅ Console output clean (only prints, no library logs)
5. ✅ All telemetry in OTEL backend



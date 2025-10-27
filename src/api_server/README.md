# API Server

FastAPI server providing REST API endpoints for AI agent function calling. Instrumented with OpenTelemetry for comprehensive distributed tracing.

## Endpoints

### Health Check
- **GET** `/health` - Returns health status
- **Response**: `{"status": "healthy"}`

### Product of the Day
- **GET** `/product-of-the-day` - Returns a randomly selected product
- **Response**: `{"product_id": "LAPTOP001", "product_description": "High-performance gaming laptop with RTX 4080"}`
- **Products**: 8 different products in rotation

### Data Processing
- **POST** `/process` - Processes data (demo endpoint)
- **Request**: `{"data": "string"}`
- **Response**: `{"result": "Processed: string", "message": "Data processed successfully"}`

## Observability

### Automatic Instrumentation
- **FastAPI Auto-Instrumentation**: All HTTP endpoints automatically traced
- **HTTP Metadata**: Request/response headers, status codes, paths
- **Metrics**: Request counts, latencies, error rates

### Manual Instrumentation
- **Custom Spans**: Tool-specific spans with `tool.name` and `tool.type` attributes
- **Structured Logging**: OTLP logs with request/response correlation
- **Product Tracking**: Product ID attributes for tracing product queries

### OTEL Configuration
Environment variables configured via Kubernetes deployment:
- `OTEL_EXPORTER_OTLP_ENDPOINT`: Collector endpoint (gRPC)
- `OTEL_SERVICE_NAME`: Service identifier (default: "api-server")
- `OTEL_PYTHON_EXCLUDED_URLS`: Health check endpoint excluded from traces

## Deployment

The API server runs as a Kubernetes deployment:

### Accessing the Service

**Internal (within cluster)**:
```
http://maf-demo-api-tool:8000
```

**External (via ingress)**:
```
https://api-tool.{your-domain}
```

### Testing from Outside Cluster

```powershell
# Get the ingress URL from Terraform
cd infra
$apiUrl = terraform output -raw api_tool_url

# Test health endpoint
curl "$apiUrl/health"

# Test product endpoint
curl "$apiUrl/product-of-the-day"
```

### Testing from Agent Container

```bash
# Inside agent container (kubectl exec)
curl http://maf-demo-api-tool:8000/health
curl http://maf-demo-api-tool:8000/product-of-the-day
```

## Configuration

Environment variables (auto-configured in Kubernetes):
- `OTEL_EXPORTER_OTLP_ENDPOINT` - OTEL collector endpoint (required)
- `OTEL_SERVICE_NAME` - Service name for telemetry (default: "api-server")
- `HOST` - Bind address (default: "0.0.0.0")
- `PORT` - Listen port (default: 8000)

## Container Image

Built via ACR remote build tasks:

```powershell
# Build and push (from scripts directory)
cd scripts
uv run build_and_push.py
```

Image: `{acr-name}.azurecr.io/api-tool:{version}`

## Observability Features

### Trace Context Propagation
- Receives trace context from agent via HTTP headers
- Propagates context to downstream services
- Creates child spans for all operations

### Structured Logs
- Automatic correlation with traces
- JSON-formatted logs sent via OTLP
- Filtered log levels (INFO+ in production)

### Metrics Export
- Request counts by endpoint and status
- Request duration histograms
- Active request gauges
- Exported to OTEL collector → Prometheus

## Architecture Integration

```
Agent (MAF)
    ↓ HTTP Function Call
API Server (this service)
    ↓ OTLP
OTEL Collector
    ↓
Aspire Dashboard / Langfuse / Azure Monitor
```

The API server acts as a function calling target for AI agents, providing structured data while maintaining full observability context.

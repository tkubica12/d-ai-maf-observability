# API Server

FastAPI server providing REST API endpoints for AI agent function calling, instrumented with OpenTelemetry.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check — returns `{"status": "healthy"}` |
| GET | `/product-of-the-day` | Returns a random product (`product_id`, `product_description`) from 8 products |
| POST | `/process` | Demo data processing — accepts `{"data": "string"}` |

## Configuration

| Variable | Description |
|----------|-------------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTEL collector endpoint (required) |
| `OTEL_SERVICE_NAME` | Service name for telemetry (default: `api-server`) |
| `HOST` | Bind address (default: `0.0.0.0`) |
| `PORT` | Listen port (default: `8000`) |

## Testing

```bash
# Internal (from agent container)
curl http://maf-demo-api-tool:8000/health
curl http://maf-demo-api-tool:8000/product-of-the-day

# External (via ingress)
curl "https://api-tool.{your-domain}/health"
curl "https://api-tool.{your-domain}/product-of-the-day"
```

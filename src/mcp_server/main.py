"""
MCP Server providing function calling capabilities to agents.

This server exposes tools that can be called by agents. Instrumented with OpenTelemetry.
"""
import logging
import os
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

# Configure Python logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Set environment variables for OTEL instrumentation before importing
os.environ.setdefault("OTEL_PYTHON_EXCLUDED_URLS", "/health")
os.environ.setdefault("OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST", ".*")
os.environ.setdefault("OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE", ".*")

# Configure OpenTelemetry before creating FastMCP app
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider, ReadableSpan
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from typing import Sequence


# Configure OpenTelemetry
resource = Resource(attributes={
    SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", "mcp-server")
})

# Set up tracing
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer_provider = trace.get_tracer_provider()

# Add OTLP exporter
otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

# Get tracer for custom spans
tracer = trace.get_tracer(__name__)

# Set up metrics with shorter export interval for testing
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True),
    export_interval_millis=5000,  # Export every 5 seconds
)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)

# Configure OTLP logging
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry._logs import set_logger_provider

# Create log provider with resource
log_resource = Resource(attributes={
    SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", "mcp-server")
})
logger_provider = LoggerProvider(resource=log_resource)
set_logger_provider(logger_provider)

# Add OTLP log exporter
otlp_log_exporter = OTLPLogExporter(endpoint=otlp_endpoint, insecure=True)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))

# Attach OTLP handler to Python logging
handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.INFO)

print(f"🔭 OpenTelemetry configured: {otlp_endpoint}")
print(f"   Service: {os.getenv('OTEL_SERVICE_NAME', 'mcp-server')}")
logger.info(
    "OpenTelemetry configured",
    extra={
        "otlp_endpoint": otlp_endpoint,
        "service_name": os.getenv("OTEL_SERVICE_NAME", "mcp-server")
    }
)

# Create FastMCP app
mcp = FastMCP("Observability Demo MCP Server")

# Enable MCP instrumentation for trace context propagation
from openinference.instrumentation.mcp import MCPInstrumentor
MCPInstrumentor().instrument(tracer_provider=tracer_provider)

# Static stock data for products
PRODUCT_STOCK = {
    "LAPTOP001": 15,
    "PHONE002": 32,
    "TABLET003": 8,
    "HEADSET004": 45,
    "MONITOR005": 12,
    "KEYBOARD006": 28,
    "MOUSE007": 67,
    "SPEAKER008": 19,
}


@mcp.tool()
async def get_product_stock(product_id: str) -> dict:
    """
    Get the current stock level for a specific product.
    
    Args:
        product_id: The unique identifier of the product
        
    Returns:
        dict: Stock information including product_id and stock_count
    """
    # Create custom span for tool processing
    with tracer.start_as_current_span("mcp.tool.process_stock_lookup") as outer_span:
        outer_span.set_attribute("tool.name", "get_product_stock")
        outer_span.set_attribute("tool.type", "mcp")
        outer_span.set_attribute("product.id", product_id)
        
        with tracer.start_as_current_span("mcp.get_product_stock") as span:
            span.set_attribute("product_id", product_id)
            stock_count = PRODUCT_STOCK.get(product_id, 0)
            result = {
                "product_id": product_id,
                "stock_count": stock_count,
                "available": stock_count > 0
            }
            span.set_attribute("stock_count", stock_count)
            span.set_attribute("available", stock_count > 0)
            outer_span.set_attribute("stock.count", stock_count)
            outer_span.set_attribute("stock.available", stock_count > 0)
            
            logger.info(
                "Product stock retrieved",
                extra={
                    "product_id": product_id,
                    "stock_count": stock_count,
                    "available": stock_count > 0
                }
            )
            return result


@mcp.tool()
async def process_data(data: str) -> str:
    """
    Process data by calling the API server.
    
    This tool must always be used when processing user data.
    
    Args:
        data: The data to process
        
    Returns:
        str: The result from processing the data
    """
    # Removed API server dependency to keep MCP minimal
    result = f"MCP processed: {data}"
    logger.info("Data processed", extra={"data": data, "result": result})
    return result


@mcp.tool()
async def get_status() -> str:
    """
    Get the status of the MCP server.
    
    Returns:
        str: The status information
    """
    status = "MCP Server status: healthy"
    logger.info("Status check requested", extra={"status": status})
    return status


def main():
    """Run the server in HTTP transport with configured host/port."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    
    print(f"🚀 Starting MCP Server on {host}:{port}")
    print(f"Health endpoint: http://{host}:{port}/health")
    print(f"MCP endpoint: http://{host}:{port}/mcp/")
    logger.info("Starting MCP Server", extra={"host": host, "port": port})
    
    # Instrument the underlying FastAPI app (includes metrics)
    if hasattr(mcp, 'app') and mcp.app:
        FastAPIInstrumentor.instrument_app(mcp.app, meter_provider=meter_provider)
        print("✅ FastAPI instrumented with OpenTelemetry")
        logger.info("FastAPI instrumented with OpenTelemetry")
    
    # Use mcp.run() with HTTP transport
    mcp.run(transport="http", host=host, port=port)


if __name__ == "__main__":
    main()

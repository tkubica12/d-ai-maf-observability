"""
MCP Server providing function calling capabilities to agents.

This server exposes tools that can be called by agents. Instrumented with OpenTelemetry.
"""
import os
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

# Configure OpenTelemetry before creating FastMCP app
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, ReadableSpan
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from typing import Sequence


def health_endpoint_filter(span: ReadableSpan) -> bool:
    """Filter out health check endpoints from traces."""
    if span.attributes:
        http_target = span.attributes.get("http.target")
        url_path = span.attributes.get("url.path")
        if http_target == "/health" or url_path == "/health":
            return False
    return True


class FilteringSpanProcessor(BatchSpanProcessor):
    """Span processor that filters spans before export."""
    
    def __init__(self, span_exporter: SpanExporter, filter_fn=None):
        super().__init__(span_exporter)
        self.filter_fn = filter_fn or (lambda span: True)
    
    def on_end(self, span: ReadableSpan) -> None:
        if self.filter_fn(span):
            super().on_end(span)


# Configure OpenTelemetry
resource = Resource(attributes={
    SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", "mcp-server")
})

trace.set_tracer_provider(TracerProvider(resource=resource))
tracer_provider = trace.get_tracer_provider()

# Add OTLP exporter with filtering
otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
tracer_provider.add_span_processor(
    FilteringSpanProcessor(otlp_exporter, filter_fn=health_endpoint_filter)
)

# Get tracer for custom spans
tracer = trace.get_tracer(__name__)

print(f"🔭 OpenTelemetry configured: {otlp_endpoint}")
print(f"   Service: {os.getenv('OTEL_SERVICE_NAME', 'mcp-server')}")

# Create FastMCP app
mcp = FastMCP("Observability Demo MCP Server")

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
    return f"MCP processed: {data}"


@mcp.tool()
async def get_status() -> str:
    """
    Get the status of the MCP server.
    
    Returns:
        str: The status information
    """
    return "MCP Server status: healthy"


def main():
    """Run the server in HTTP transport with configured host/port."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    
    print(f"🚀 Starting MCP Server on {host}:{port}")
    print(f"Health endpoint: http://{host}:{port}/health")
    print(f"MCP endpoint: http://{host}:{port}/mcp/")
    
    # Instrument the underlying FastAPI app
    if hasattr(mcp, 'app') and mcp.app:
        FastAPIInstrumentor.instrument_app(mcp.app)
        print("✅ FastAPI instrumented with OpenTelemetry")
    
    # Use mcp.run() with HTTP transport
    mcp.run(transport="http", host=host, port=port)


if __name__ == "__main__":
    main()

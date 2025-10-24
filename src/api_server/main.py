"""
API Server that receives function calls from MCP server.

This server provides a simple API endpoint that can be called through
function calling from the MCP server. Instrumented with OpenTelemetry.
"""
import os
import random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Configure OpenTelemetry before creating FastAPI app
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Custom span filter to exclude /health endpoint
def health_endpoint_filter(span):
    """Filter out /health endpoint from traces."""
    if span.attributes:
        # Check various possible attribute names for the URL path
        http_target = (
            span.attributes.get("http.target") 
            or span.attributes.get("url.path")
            or span.attributes.get("http.url")
            or span.attributes.get("url.full")
        )
        if http_target and "/health" in str(http_target):
            return False
    return True

# Configure OpenTelemetry
resource = Resource(attributes={
    SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", "api-server")
})

trace.set_tracer_provider(TracerProvider(resource=resource))
tracer_provider = trace.get_tracer_provider()

# Add OTLP exporter with filter
otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)

# Wrap processor with filtering
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

class FilteringSpanProcessor(BatchSpanProcessor):
    """Span processor that filters spans based on a predicate."""
    def __init__(self, span_exporter, span_filter=None, **kwargs):
        super().__init__(span_exporter, **kwargs)
        self._span_filter = span_filter or (lambda span: True)
    
    def on_end(self, span):
        if self._span_filter(span):
            super().on_end(span)

tracer_provider.add_span_processor(
    FilteringSpanProcessor(otlp_exporter, span_filter=health_endpoint_filter)
)

print(f"🔭 OpenTelemetry configured: {otlp_endpoint}")
print(f"   Service: {os.getenv('OTEL_SERVICE_NAME', 'api-server')}")

# Create FastAPI app
app = FastAPI(title="API Server", version="0.1.0")

# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static product data
PRODUCTS = [
    {"product_id": "LAPTOP001", "product_description": "High-performance gaming laptop with RTX 4080"},
    {"product_id": "PHONE002", "product_description": "Latest smartphone with AI-powered camera"},
    {"product_id": "TABLET003", "product_description": "Professional tablet with stylus support"},
    {"product_id": "HEADSET004", "product_description": "Wireless noise-canceling headphones"},
    {"product_id": "MONITOR005", "product_description": "4K ultra-wide monitor for productivity"},
    {"product_id": "KEYBOARD006", "product_description": "Mechanical gaming keyboard with RGB lighting"},
    {"product_id": "MOUSE007", "product_description": "Precision wireless gaming mouse"},
    {"product_id": "SPEAKER008", "product_description": "Premium Bluetooth speaker system"},
]


class ProcessDataRequest(BaseModel):
    """Request model for processing data."""
    data: str


class ProcessDataResponse(BaseModel):
    """Response model for processing data."""
    result: str
    message: str


class ProductResponse(BaseModel):
    """Response model for product of the day."""
    product_id: str
    product_description: str


@app.get("/")
async def root():
    """Root endpoint returning service information."""
    return {
        "service": "API Server",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/product-of-the-day", response_model=ProductResponse)
async def get_product_of_the_day():
    """
    Get a randomly selected product of the day.
    
    Returns:
        ProductResponse: Randomly selected product with ID and description
    """
    product = random.choice(PRODUCTS)
    return ProductResponse(
        product_id=product["product_id"],
        product_description=product["product_description"]
    )


@app.post("/process", response_model=ProcessDataResponse)
async def process_data(request: ProcessDataRequest):
    """
    Process data received from MCP function call.
    
    Args:
        request: The data to process
        
    Returns:
        ProcessDataResponse with the result
    """
    result = f"Processed: {request.data}"
    return ProcessDataResponse(
        result=result,
        message="Data processed successfully"
    )


def main():
    """Start the API server."""
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    print(f"🚀 Starting API Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()

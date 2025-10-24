"""
API Server that receives function calls from MCP server.

This server provides a simple API endpoint that can be called through
function calling from the MCP server. Instrumented with OpenTelemetry.
"""
import logging
import os
import random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Configure Python logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Set environment variables for OTEL instrumentation before importing
os.environ.setdefault("OTEL_PYTHON_EXCLUDED_URLS", "/health")
os.environ.setdefault("OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST", ".*")
os.environ.setdefault("OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE", ".*")

# Configure OpenTelemetry before creating FastAPI app
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Configure OpenTelemetry
resource = Resource(attributes={
    SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", "api-server")
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

# Set up metrics
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
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
    SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", "api-server")
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
print(f"   Service: {os.getenv('OTEL_SERVICE_NAME', 'api-server')}")
logger.info(
    "OpenTelemetry configured",
    extra={
        "otlp_endpoint": otlp_endpoint,
        "service_name": os.getenv("OTEL_SERVICE_NAME", "api-server")
    }
)

# Create FastAPI app
app = FastAPI(title="API Server", version="0.1.0")

# Instrument FastAPI with OpenTelemetry (includes metrics)
FastAPIInstrumentor.instrument_app(app, meter_provider=meter_provider)

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
    # Create custom span for tool processing
    with tracer.start_as_current_span("api.tool.process_product_request") as span:
        span.set_attribute("tool.name", "get_product_of_the_day")
        span.set_attribute("tool.type", "api")
        
        product = random.choice(PRODUCTS)
        span.set_attribute("product.id", product["product_id"])
        
        logger.info(
            "Product of the day requested",
            extra={
                "product_id": product["product_id"],
                "product_description": product["product_description"]
            }
        )
        
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
    logger.info("Data processed", extra={"data": request.data, "result": result})
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
    logger.info("Starting API Server", extra={"host": host, "port": port})
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()

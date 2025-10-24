# Agent

Microsoft Agent Framework (MAF) agents demonstrating multiple observability scenarios.

## Observability Scenarios

The `main.py` provides comprehensive testing of MAF scenarios with different deployment patterns:

### Implemented Scenarios

#### Scenario 1: Local Microsoft Agent Framework (`local-maf`)
- Local agent using AzureOpenAIResponsesClient
- Direct calls to Azure OpenAI endpoint
- Function calling for API tools and MCP tools
- Manual orchestration with full control
- Use case: Development, testing, custom logic

#### Scenario 2: MAF with Foundry Agent Service (`maf-with-fas`)
- Agent lifecycle managed by Azure AI Foundry Agent Service
- Uses AzureAIAgentClient for agent creation and execution
- Same tool integration (API and MCP)
- Managed conversation state and threading
- Use case: Production deployments, enterprise scale

### Planned Scenarios

- **Scenario 3**: `local-maf-multiagent` - Local multi-agent collaboration
- **Scenario 4**: `maf-with-fas-multiagent` - Foundry multi-agent orchestration
- **Scenario 5**: `local-maf-with-fas-multiagent` - Hybrid multi-agent architecture

## Tool Integration

The unified agent demonstrates network-based tool integration:

### API Tools (via HTTP Function Calling)
- **get_product_of_the_day**: Calls API server to get today's featured product
- Returns: `{product_id, product_description}`

### MCP Tools (via MCP Server)
- **get_product_stock**: Calls MCP server to get stock levels
- Input: `product_id` from API call
- Returns: `{product_id, stock_count, available}`

### End-to-End Flow
1. Agent gets product of the day via API function call
2. Uses product description in response
3. Looks up stock using product_id via MCP
4. Provides comprehensive answer with both product info and availability

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Create `.env` file (see `.env.example` for reference):
```bash
cp .env.example .env
```

3. Configure Azure AI endpoints and ensure proper RBAC roles are assigned:
   - For Foundry variant: Set `PROJECT_ENDPOINT`
   - For Direct variant: Set `AI_ENDPOINT`

4. Ensure MCP server is running on configured port (default: 8001)

5. Make sure the API server is running (default: 8000)

## Running

Run all implemented scenarios:
```bash
uv run main.py
```

The agent will execute scenarios sequentially:
1. local-maf (if AI_ENDPOINT configured)
2. maf-with-fas (if PROJECT_ENDPOINT configured)

### Simple Demo Mode
If endpoints are not configured, scenarios are skipped with informative messages.

## Docker

Build and run:
```bash
docker build -t agent .
docker run --env-file .env agent
```

## Configuration

Environment variables:
- `AI_ENDPOINT` - Azure OpenAI endpoint (for local-maf, e.g., https://<resource>.openai.azure.com)
- `PROJECT_ENDPOINT` - Azure AI Foundry project endpoint (for maf-with-fas)
- `MODEL_NAME` - Model deployment name for local-maf (default: gpt-4o)
- `MODEL_DEPLOYMENT` - Model deployment name for maf-with-fas (default: gpt-4o)
- `API_SERVER_URL` - API server URL (default: http://localhost:8000)
- `MCP_SERVER_URL` - MCP server URL (default: http://localhost:8001)
- `OTEL_EXPORTER_OTLP_ENDPOINT` - OpenTelemetry collector endpoint (optional, e.g., http://localhost:4317)
- `OTEL_SERVICE_NAME` - Service name for telemetry (default: agent)

## Authentication

Both agents use DefaultAzureCredential which attempts authentication in this order:
1. Environment variables (service principal)
2. Managed identity (when running in Azure)
3. Azure CLI (during development)
4. Visual Studio Code
5. Azure PowerShell

Ensure proper RBAC roles are assigned:
- `Cognitive Services User` - Basic model access
- `Cognitive Services OpenAI User` - OpenAI model access
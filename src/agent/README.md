# Agent

Microsoft Agent Framework (MAF) agents with unified testing approach for Azure AI integration.

## Unified Agent Testing

The new `unified_agent.py` provides comprehensive testing of both MAF approaches in a single file:

### Approach 1: Direct LLM Agent with Function Calling
- Direct calls to Azure AI models via ChatCompletionsClient
- Function calling for API tools (get product of the day)
- MCP integration for stock lookup
- Manual orchestration and conversation management

### Approach 2: Foundry Agent Service with Registered Agent  
- Complete agent lifecycle management through Azure AI Foundry
- Agent registration, execution, and cleanup
- Built-in tool integration and orchestration
- Managed conversation state and threading

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

### Foundry Agent Service Variant
```bash
python main.py
```

### Direct Model Access Variant
```bash
python main_direct.py
```

### Simple Demo Mode (No Azure Required)
If endpoints are not configured, agents run in demo mode showing expected behavior.

## Docker

Build and run:
```bash
docker build -t agent .
docker run --env-file .env agent
```

## Configuration

Environment variables:
- `PROJECT_ENDPOINT` - Azure AI Foundry project endpoint (for Foundry variant)
- `AI_ENDPOINT` - Direct Azure AI models endpoint (for Direct variant)
- `MODEL_DEPLOYMENT` / `MODEL_NAME` - Model deployment name (default: gpt-4o)
- `MCP_SERVER_URL` - MCP server URL (default: http://localhost:8001)
- `API_SERVER_URL` - API server URL for MCP (default: http://localhost:8000)
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8002)

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
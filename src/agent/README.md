# Agent

Microsoft Agent Framework (MAF) agents with two variants for Azure AI integration.

## Agent Variants

### 1. Foundry Agent Service (`main.py`)
Uses Azure AI Foundry Agent Service for complete agent lifecycle management:
- Full MAF agent runtime through Azure AI Foundry
- Built-in tool integration and orchestration
- Managed conversation state and threading
- Uses DefaultAzureCredential for authentication

### 2. Direct Model Access (`main_direct.py`)
Direct LLM access with MAF patterns:
- Direct calls to Azure AI models via ChatCompletionsClient
- Manual tool orchestration and conversation management
- Custom agent logic implementation
- Uses DefaultAzureCredential for authentication

## Features

- Uses Microsoft Agent Framework (MAF) for agent runtime
- Integrates with MCP server via HTTP for tool calling
- DefaultAzureCredential authentication (no API keys needed)
- CORS support for web integration
- Configurable ports and endpoints

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
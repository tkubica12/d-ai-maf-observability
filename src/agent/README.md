# Agent

Microsoft Agent Framework (MAF) agent that integrates with MCP server for function calling.

## Features

- Uses MAF for agent runtime
- Integrates with MCP server for tool calling
- Mandatory tool usage for data processing
- Sends simple user messages and reports back responses

## Setup

1. Install dependencies:
```bash
pip install azure-ai-projects azure-identity python-dotenv mcp
```

2. Create `.env` file (see `.env.example` for reference):
```bash
cp .env.example .env
```

3. Configure your Azure AI Project connection string in `.env`:
```
PROJECT_CONNECTION_STRING=endpoint=https://your-project.cognitiveservices.azure.com/;...
```

4. Ensure MCP server path is correctly set (default: `../mcp_server/main.py`)

5. Make sure the API server is running (or update API_SERVER_URL in MCP server config)

## Running

### Simple Demo Mode (No Azure Required)
If PROJECT_CONNECTION_STRING is not set, the agent runs in demo mode:
```bash
python main.py
```

### Full Mode (Azure AI Project Required)
With Azure AI Project configured:
```bash
python main.py
```

The agent will:
1. Connect to Azure AI Project
2. Start MCP server as subprocess
3. Create an agent with available MCP tools
4. Send a test message
5. Use the `process_data` tool (mandatory)
6. Display the response

## Docker

Build and run:
```bash
docker build -t agent .
docker run --env-file .env agent
```

## Configuration

Environment variables:
- `PROJECT_CONNECTION_STRING` - Azure AI Project connection (optional for demo)
- `MODEL_DEPLOYMENT` - Model deployment name (default: gpt-4o)
- `MCP_SERVER_PATH` - Path to MCP server main.py (default: ../mcp_server/main.py)
- `API_SERVER_URL` - API server URL for MCP (default: http://localhost:8000)
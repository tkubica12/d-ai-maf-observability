# MCP Server

FastMCP-based MCP server that provides function calling tools to agents via HTTP streaming.

## Features

- HTTP-based MCP server (not stdio)
- CORS enabled for web integration
- Configurable host and port
- Tool bridging to API server
- Health check endpoint

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Create `.env` file (see `.env.example` for reference):
```bash
cp .env.example .env
```

3. Make sure the API server is running on the configured URL (default: http://localhost:8000)

4. Run the MCP server:
```bash
python main.py
```

The server will start on the configured host:port with CORS enabled.

## Available Tools

- `process_data` - Process data by calling the API server (mandatory tool)
- `get_status` - Get the status of the API server

## Endpoints

- `/health` - Health check endpoint
- `/tools` - List available tools
- `/tools/{tool_name}` - Execute specific tool

## Docker

Build and run:
```bash
docker build -t mcp-server .
docker run --env Variables .env -p 8001:8001 mcp-server
```

## Configuration

Environment variables:
- `API_SERVER_URL` - URL of the API server (default: http://localhost:8000)
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8001)
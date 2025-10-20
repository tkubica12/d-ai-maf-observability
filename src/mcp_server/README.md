# MCP Server

FastMCP-based MCP server that provides function calling tools to agents.

## Setup

1. Install dependencies:
```bash
pip install fastmcp httpx python-dotenv
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

## Available Tools

- `process_data` - Process data by calling the API server (mandatory tool)
- `get_status` - Get the status of the API server

## Docker

Build and run:
```bash
docker build -t mcp-server .
docker run mcp-server
```

## Configuration

Environment variables:
- `API_SERVER_URL` - URL of the API server (default: http://localhost:8000)
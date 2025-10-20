# d-ai-maf-observability
Microsoft Agent Framework observability

## Overview

This project demonstrates comprehensive observability for Microsoft Agent Framework (MAF) applications with MCP (Model Context Protocol) integration and API-based function calling.

## Architecture

```
Agent (MAF) → MCP Server → API Server
```

- **Agent**: Microsoft Agent Framework agent with MCP tool integration
- **MCP Server**: FastMCP-based server exposing function calling tools
- **API Server**: FastAPI REST API processing data from function calls

## Quick Start

### Prerequisites

- Python 3.12+
- pip or uv package manager

### 1. API Server

```bash
cd src/api_server
pip install fastapi uvicorn pydantic python-dotenv
cp .env.example .env
python main.py
```

The API server will start on http://localhost:8000

### 2. MCP Server

```bash
cd src/mcp_server
pip install fastmcp httpx python-dotenv
cp .env.example .env
python main.py
```

### 3. Agent

```bash
cd src/agent
pip install azure-ai-projects azure-identity python-dotenv mcp
cp .env.example .env
python main.py
```

The agent will run in demo mode if Azure credentials are not configured.

## Documentation

- [Design Document](docs/DESIGN.md) - Architecture and design decisions
- [Implementation Log](docs/IMPLEMENTATION_LOG.md) - Development history and decisions
- [Agent README](src/agent/README.md) - Agent service details
- [MCP Server README](src/mcp_server/README.md) - MCP server details
- [API Server README](src/api_server/README.md) - API server details

## Docker Support

Each service includes a Dockerfile:

```bash
# API Server
cd src/api_server
docker build -t api-server .
docker run -p 8000:8000 api-server

# MCP Server
cd src/mcp_server
docker build -t mcp-server .
docker run mcp-server

# Agent
cd src/agent
docker build -t agent .
docker run --env-file .env agent
```

## Development Guidelines

See [AGENTS.md](AGENTS.md) for development guidelines and best practices.

# API Server

FastAPI-based API server that receives function calls from the MCP server.

## Setup

1. Install dependencies:
```bash
uv pip install -r pyproject.toml
```

2. Create `.env` file (see `.env.example` for reference):
```bash
cp .env.example .env
```

3. Run the server:
```bash
python main.py
```

The server will start on http://localhost:8000

## Endpoints

- `GET /` - Service information
- `GET /health` - Health check
- `POST /process` - Process data (called via MCP function calling)

## Docker

Build and run:
```bash
docker build -t api-server .
docker run -p 8000:8000 api-server
```

## Configuration

Environment variables:
- `API_HOST` - Server host (default: 0.0.0.0)
- `API_PORT` - Server port (default: 8000)
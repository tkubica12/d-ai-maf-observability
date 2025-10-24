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

## Deployment to Azure (Production)

### Prerequisites
- Azure subscription
- Terraform installed
- kubectl configured
- Azure CLI authenticated

### 1. Configure Infrastructure

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### 2. Deploy Infrastructure

```bash
terraform init
terraform plan
terraform apply
```

This deploys:
- AKS cluster with monitoring
- Azure Container Registry
- Azure AI Services
- OpenTelemetry Collector
- Aspire Dashboard at `https://aspire.{domain}`
- Ingress with TLS certificates

### 3. Build and Push Images

```bash
cd ../scripts
uv run build_and_push.py
```

This builds and pushes three container images to ACR:
- `agent` - MAF agent with workload identity
- `api-tool` - REST API server
- `mcp-tool` - MCP server

Versions are automatically incremented and tracked in `infra/images.auto.tfvars`.

### 4. Deploy Updated Helm Chart

```bash
cd ../infra
terraform apply  # Updates Helm release with new image tags
```

### 5. Access Services

Get URLs from Terraform outputs:
```bash
terraform output api_tool_url          # API Server
terraform output mcp_tool_url          # MCP Server  
terraform output aspire_dashboard_url  # Observability UI
```

**Agent** runs inside the cluster with:
- Workload identity for Azure AI authentication
- Internal service URLs for API and MCP tools
- OTEL endpoint at `maf-demo-otel-collector:4317`

### 6. View Telemetry

Open Aspire Dashboard to see:
- **Traces**: Distributed traces across services
- **Metrics**: Request rates and durations
- **Logs**: Structured application logs

Generate test traces:
```bash
curl $(terraform output -raw api_tool_url)/health
curl $(terraform output -raw api_tool_url)/product-of-the-day
```

## Observability

### OpenTelemetry Stack
- **Collector**: `maf-demo-otel-collector:4317` (OTLP gRPC)
- **Aspire Dashboard**: Web UI at `https://aspire.{domain}`
- **Console Debug**: Collector logs spans for troubleshooting

### Instrumentation
- **Agent**: Manual OTEL SDK with custom business logic spans
- **API Server**: Automatic FastAPI instrumentation
- **MCP Server**: Hybrid auto + manual instrumentation

All services use standard OTEL environment variables automatically configured in Kubernetes.

### Troubleshooting

**View collector logs**:
```bash
kubectl logs -n maf-demo -l app.kubernetes.io/component=otel-collector -f
```

**Check service telemetry**:
```bash
kubectl logs -n maf-demo -l app.kubernetes.io/component=api-tool
# Look for: 🔭 OpenTelemetry configured: http://...
```

**Port forward Aspire locally**:
```bash
kubectl port-forward -n maf-demo svc/maf-demo-aspire-dashboard 18888:18888
# Open http://localhost:18888
```

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
docker run -p 8001:8001 mcp-server

# Agent
cd src/agent
docker build -t agent .
docker run --env-file .env agent
```

## Development Guidelines

See [AGENTS.md](AGENTS.md) for development guidelines and best practices.

# Microsoft Agent Framework Observability Demo

Comprehensive observability for Microsoft Agent Framework (MAF) applications across different deployment scenarios and interaction patterns.

## Scenarios

| Scenario | Hosting | Agents | Description |
|----------|---------|--------|-------------|
| `local-maf` | Local | Single | MAF running locally, accessing tools via API and MCP from local runtime |
| `maf-with-fas` | Cloud | Single | MAF leveraging FAS, accessing tools via API and MCP from FAS in cloud |
| `local-maf-multiagent` ✅ | Local | Multi | MAF with Magentic orchestration of two local agents |
| `maf-with-fas-multiagent` | Cloud | Multi | MAF leveraging FAS with connected agents, both in FAS (cloud) |
| `local-maf-with-fas-multiagent` | Hybrid | Multi | MAF hosting one agent communicating with second agent running in FAS |
| `local-maf-multiagent-a2a` | Hybrid | Multi (via A2A) | MAF hosting one agent communicating with generic A2A agent running outside of MAF |
| `maf-with-fas-multiagent-a2a` | Cloud | Multi (via A2A) | MAF leveraging FAS for agents where one agent is generic A2A agent running outside of FAS/MAF |

## Architecture

```
Agent (MAF) → [MCP Server, API Server] → Azure OpenAI / Foundry Agent Service
              ↓
         OTEL Collector → Aspire Dashboard
```

**Components**:
- **Agent**: MAF with Magentic orchestration, MCP tools, API integration
- **MCP Server**: FastMCP-based function calling tools
- **API Server**: FastAPI REST API for data processing
- **OTEL Stack**: Distributed tracing, metrics, and logs

## Quick Start (Local Development)

### Run Agent with Scenarios

```bash
cd src/agent
uv run main.py -s local-maf              # Single agent, local
uv run main.py -s maf-with-fas           # Single agent, cloud (FAS)
uv run main.py -s local-maf-multiagent   # Multi-agent, Magentic orchestration
```

### Run Supporting Services

```bash
# API Server (port 8000)
cd src/api_server && uv run main.py

# MCP Server (port 8001)
cd src/mcp_server && uv run main.py
```

Configure `.env` files in each directory (see `.env.example`).

## Documentation

- **[Design Document](docs/DESIGN.md)** - Complete architecture, scenario matrix, telemetry strategy
- [Implementation Log](docs/IMPLEMENTATION_LOG.md) - Development history
- Service READMEs: [Agent](src/agent/README.md) | [MCP Server](src/mcp_server/README.md) | [API Server](src/api_server/README.md)

## Deployment to Azure

See [Design Document](docs/DESIGN.md) for infrastructure details.

### Quick Deploy

```bash
# 1. Configure
cd infra && cp terraform.tfvars.example terraform.tfvars
# Edit with your values

# 2. Deploy infrastructure
terraform init && terraform apply

# 3. Build & push images
cd ../scripts && uv run build_and_push.py

# 4. Update deployment
cd ../infra && terraform apply
```

**Access**:
- Aspire Dashboard: `https://aspire.{domain}`
- API Server: `$(terraform output -raw api_tool_url)`
- MCP Server: `$(terraform output -raw mcp_tool_url)`

## Observability Stack

- **OTEL Collector**: Centralized telemetry (`otel-collector:4317`)
- **Aspire Dashboard**: Traces, metrics, logs visualization
- **Instrumentation**: Agent (manual spans), API/MCP (auto + manual)

Generate test traces:
```bash
curl $(terraform output -raw api_tool_url)/product-of-the-day
```

## Development

See [AGENTS.md](AGENTS.md) for development guidelines and best practices.

---

**Status**: Phase 2 - Multi-Agent Patterns (3 of 7 scenarios implemented)  
**Tech Stack**: Python 3.12+ | MAF | FastAPI | FastMCP | OpenTelemetry | Terraform | AKS

# Agent

Microsoft Agent Framework (MAF) agents demonstrating multiple observability scenarios with comprehensive telemetry instrumentation.

## Observability Scenarios

The `main.py` provides comprehensive testing of MAF scenarios with different deployment patterns and agent collaboration models.

### Implemented Scenarios

#### Scenario 1: Local Microsoft Agent Framework (`local-maf`)
- Agent using AzureOpenAIResponsesClient
- Direct calls to Azure OpenAI endpoint
- Function calling for API tools and MCP tools
- Manual orchestration with full control
- **Pattern**: Single agent with direct model access
- **Use case**: Development, testing, custom logic

#### Scenario 2: MAF with Foundry Agent Service (`maf-with-fas`)
- Agent lifecycle managed by Azure AI Foundry Agent Service
- Uses AzureAIAgentClient for agent creation and execution
- Same tool integration (API and MCP)
- Managed conversation state and threading
- **Pattern**: Single agent with managed service
- **Use case**: Production deployments, enterprise scale

#### Scenario 3: Local MAF Multi-Agent (`local-maf-multiagent`)
- Magentic orchestration pattern with StandardMagenticManager
- Facilitator (orchestrator) + Worker agent architecture
- Built-in Agent Framework multi-agent collaboration
- Dynamic task decomposition and delegation
- **Pattern**: Multi-agent with intelligent coordination
- **Use case**: Complex workflows, specialized agent roles

### Planned Scenarios

- **Scenario 4**: `maf-with-fas-multiagent` - FAS multi-agent orchestration
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

## Running in Deployed Environment

The agent runs inside a Kubernetes pod in the AKS cluster. Access it via kubectl:

```powershell
# Get the agent pod name
kubectl get pods -n maf-demo | Select-String "agent"

# Connect to the agent container
kubectl exec -it -n maf-demo <agent-pod-name> -- /bin/bash

# Inside the container - run specific scenarios
uv run main.py -s local-maf              # Single agent, Azure OpenAI
uv run main.py -s maf-with-fas           # Single agent, Foundry Agent Service
uv run main.py -s local-maf-multiagent   # Multi-agent, Magentic orchestration

# Run all implemented scenarios
uv run main.py
```

### Scenario Selection

Run specific scenarios by providing one or more scenario IDs:

```bash
# Single scenario
uv run main.py -s local-maf

# Multiple scenarios (space-separated)
uv run main.py -s local-maf maf-with-fas

# Multiple scenarios (comma-separated)
uv run main.py -s local-maf,maf-with-fas

# All scenarios (default when no -s flag)
uv run main.py
```

Available scenario IDs:
- `local-maf`: Local MAF with Azure OpenAI
- `maf-with-fas`: MAF with Foundry Agent Service
- `local-maf-multiagent`: Multi-agent with Magentic orchestration

## Configuration

Environment variables are automatically configured via Kubernetes deployment:

- `AI_ENDPOINT` - Azure OpenAI endpoint (for local-maf)
- `PROJECT_ENDPOINT` - Azure AI Foundry project endpoint (for maf-with-fas)
- `MODEL_NAME` - Model deployment name (default: gpt-5-nano)
- `MODEL_DEPLOYMENT` - Model deployment name (default: gpt-5-nano)
- `API_SERVER_URL` - API server URL (internal Kubernetes service or ingress)
- `MCP_SERVER_URL` - MCP server URL (internal Kubernetes service or ingress)
- `OTEL_EXPORTER_OTLP_ENDPOINT` - OpenTelemetry collector endpoint
- `OTEL_SERVICE_NAME` - Service name for telemetry (default: agent)
- `AZURE_CLIENT_ID` - Workload identity client ID (auto-configured)
- `AZURE_TENANT_ID` - Azure tenant ID (auto-configured)

## Authentication

The agent uses **Azure Workload Identity** for authentication to Azure services:
- Automatically configured via Kubernetes service account
- Federated identity credentials for pod-to-Azure authentication
- No secrets or credentials needed in code or configuration
- Proper RBAC roles assigned via Terraform:
  - `Cognitive Services User` - Basic model access
  - `Cognitive Services OpenAI User` - OpenAI model access

## Observability Features

Each scenario demonstrates comprehensive telemetry:

### OpenTelemetry Instrumentation
- **Traces**: Distributed traces across agent, API, and MCP servers
- **Metrics**: Custom business metrics (agent calls, token usage)
- **Logs**: Structured logs with correlation IDs
- **Baggage**: User context propagation across all spans

### User Context Dimensions
- `user.id`: Mock user identifiers (user_001 through user_005)
- `user.roles`: VIP status for filtering
- `session.id`: Session tracking
- `organization.department`: Department-based analysis
- `scenario_id`: Which scenario is running
- `scenario_type`: single-agent or multi-agent

### Trace Visibility
All agent executions create rich telemetry visible in:
- **Aspire Dashboard**: Distributed traces, logs, metrics
- **Langfuse**: AI-specific traces with token counts and costs
- **Azure AI Foundry**: Foundry Agent Service traces (for maf-with-fas)

## Container Image

The agent is built as a Docker container with:
- Base image: Python 3.12
- Package manager: uv (for fast dependency resolution)
- Dependencies: Microsoft Agent Framework, OpenTelemetry SDK, Azure SDKs
- Entrypoint: Kept alive for kubectl exec access (not auto-running)

Build locally (optional):
```powershell
cd src/agent
docker build -t agent:local .
```

Production images are built via ACR remote build tasks (see `scripts/build_and_push.py`).
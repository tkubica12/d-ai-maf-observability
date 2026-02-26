# Agent

MAF agents demonstrating multiple observability scenarios with OpenTelemetry instrumentation.

## Scenarios

| ID | Pattern | Status |
|----|---------|--------|
| `local-maf` | Single agent, direct Azure OpenAI | ✅ Implemented |
| `maf-with-fas` | Single agent, Foundry Agent Service | ✅ Implemented |
| `local-maf-multiagent` | Multi-agent, Magentic orchestration | ✅ Implemented |
| `maf-with-fas-multiagent` | FAS multi-agent orchestration | 🔲 Planned |
| `local-maf-with-fas-multiagent` | Hybrid multi-agent architecture | 🔲 Planned |

## Running

The agent runs inside a Kubernetes pod. Access it via kubectl:

```powershell
# Get the agent pod name
kubectl get pods -n maf-demo | Select-String "agent"

# Connect to the agent container
kubectl exec -it -n maf-demo <agent-pod-name> -- /bin/bash

# Run specific scenarios
uv run main.py -s local-maf              # Single agent, Azure OpenAI
uv run main.py -s maf-with-fas           # Single agent, Foundry Agent Service
uv run main.py -s local-maf-multiagent   # Multi-agent, Magentic orchestration

# Run all implemented scenarios
uv run main.py
```

### Scenario Selection

```bash
uv run main.py -s local-maf                    # Single scenario
uv run main.py -s local-maf maf-with-fas       # Multiple (space-separated)
uv run main.py -s local-maf,maf-with-fas       # Multiple (comma-separated)
uv run main.py                                  # All scenarios (default)
```

## Configuration

| Variable | Description |
|----------|-------------|
| `AI_ENDPOINT` | Azure OpenAI endpoint (for `local-maf`) |
| `PROJECT_ENDPOINT` | Azure AI Foundry project endpoint (for `maf-with-fas`) |
| `MODEL_NAME` | Model deployment name (default: `gpt-5-nano`) |
| `MODEL_DEPLOYMENT` | Model deployment name (default: `gpt-5-nano`) |
| `API_SERVER_URL` | API server URL (internal K8s service or ingress) |
| `MCP_SERVER_URL` | MCP server URL (internal K8s service or ingress) |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry collector endpoint |
| `OTEL_SERVICE_NAME` | Service name for telemetry (default: `agent`) |
| `AZURE_CLIENT_ID` | Workload identity client ID (auto-configured) |
| `AZURE_TENANT_ID` | Azure tenant ID (auto-configured) |

## Authentication

The agent uses Azure Workload Identity, automatically configured via Kubernetes service account federation. No secrets or credentials are needed in code — RBAC roles (`Cognitive Services User`, `Cognitive Services OpenAI User`) are assigned via Terraform.
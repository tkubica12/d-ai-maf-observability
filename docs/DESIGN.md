# Microsoft Agent Framework Observability Demo

## Purpose

Demonstrate comprehensive observability capabilities for Microsoft Agent Framework (MAF) applications across different deployment scenarios and interaction patterns. This project showcases how to instrument, collect, and visualize telemetry data from AI agents using OpenTelemetry standards.

## Observability Scenarios

### Scenario Matrix

| Scenario ID | Hosting | Agents | Description |
|-------------|---------|--------|-------------|
| `local-maf` | Local | Single | MAF running locally, accessing tools via API and MCP from local runtime |
| `maf-with-fas` | Cloud | Single | MAF leveraging FAS, accessing tools via API and MCP from FAS in cloud |
| `local-maf-multiagent` | Local | Multi | MAF with Magentic orchestration of two local agents |
| `maf-with-fas-multiagent` | Cloud | Multi | MAF leveraging FAS with connected agents, both in FAS (cloud) |
| `local-maf-with-fas-multiagent` | Hybrid | Multi | MAF hosting one agent communicating with second agent running in FAS |
| `local-maf-multiagent-a2a` | Hybrid | Multi (via A2A) | MAF hosting one agent communicating with generic A2A agent running outside of MAF |
| `maf-with-fas-multiagent-a2a` | Cloud | Multi (via A2A) | MAF leveraging FAS for agents where one agent is generic A2A agent running outside of FAS/MAF |

### Scenario Details

#### Single-Agent Scenarios

**`local-maf`** - Local MAF with Direct Azure OpenAI Access
- Agent running locally using AzureOpenAIResponsesClient
- Direct Azure OpenAI endpoint access
- Tool integration: API server (HTTP) and MCP server
- Full control over agent orchestration
- Use case: Development, testing, custom orchestration logic

**`maf-with-fas`** - MAF with Foundry Agent Service
- Agent leveraging Azure AI Foundry Agent Service via AzureAIAgentClient
- Managed agent lifecycle (create, threads, messages, runs)
- Same tool integration: API server and MCP server
- Foundry handles orchestration, state management, scaling
- Use case: Production deployments, enterprise scenarios, managed infrastructure

#### Multi-Agent Scenarios

**Architecture Pattern**: Magentic Orchestration
- **Orchestrator/Manager**: Built-in Magentic manager coordinates specialized agents
- **Worker Agent(s)**: Specialized agents with specific tools and capabilities (e.g., product queries, stock lookup)
- **Communication**: Manager dynamically plans, delegates, tracks progress, and synthesizes final results
- **Pattern Benefits**: Adaptive task decomposition, iterative refinement, automatic agent selection

**`local-maf-multiagent`** - Local MAF with Magentic Orchestration ✅
- Magentic orchestrator and worker agent both running locally
- Built-in Magentic orchestration pattern from Agent Framework
- Both use AzureOpenAIResponsesClient
- Use case: Development, testing multi-agent patterns with intelligent coordination

**`maf-with-fas-multiagent`** - Cloud-Hosted Multi-Agent ⏳
- Magentic orchestrator hosted in Foundry Agent Service
- Worker agent(s) also in FAS
- All agents managed by Foundry
- Use case: Production multi-agent with fully managed infrastructure

**`local-maf-with-fas-multiagent`** - Hybrid Multi-Agent ⏳
- Orchestrator running locally
- Worker agent running in Foundry Agent Service
- Cross-boundary agent coordination
- Use case: Hybrid scenarios, gradual cloud migration

**`local-maf-multiagent-a2a`** - Local MAF with A2A Worker ⏳
- Orchestrator running locally
- Worker packaged as generic A2A service (HTTP/REST interface)
- Standardized agent communication via A2A protocol
- Use case: Testing production-ready agent interfaces, interoperability

**`maf-with-fas-multiagent-a2a`** - Cloud MAF with A2A Worker ⏳
- Orchestrator hosted in Foundry Agent Service
- Worker as external A2A service
- FAS manages orchestrator lifecycle
- Use case: Production deployment with managed orchestrator, independent worker services

### Telemetry Collection Strategy
- **Traces**: Request flows, agent interactions, tool executions, service calls
- **Metrics**: Performance counters, success rates, latency distributions, custom business metrics
- **Logs**: Structured application logs, error details, debug information

All telemetry collected via **OpenTelemetry (OTEL)** standards for vendor-neutral observability.

## Architecture Overview

### Infrastructure Components
- **Azure Kubernetes Service (AKS)** - Container orchestration platform
- **Azure Container Registry (ACR)** - Container image storage
- **Azure AI Foundry v2** - AI services and model deployments
- **OTEL Collector** - Centralized telemetry collection and routing
- **Custom VNET** - Isolated networking with NAT gateway

### Observability Stack
- **Application Insights** - Azure-native APM with Foundry visualization
- **LangFuse** - AI-specific observability (deployed in AKS)
- **Azure Monitor for Prometheus** - Metrics collection and storage
- **Azure Managed Grafana** - Metrics visualization and dashboards

### Demo User Structure
Mock user data for realistic observability scenarios:

| User ID | VIP Status | Department |
|---------|------------|------------|
| user_001 | Yes | Engineering |
| user_002 | Yes | Marketing |
| user_003 | Yes | Engineering |
| user_004 | No | Marketing |
| user_005 | No | Engineering |

**Telemetry Dimensions**:
- `user_id`: Randomly selected from 5 users
- `is_vip`: Boolean (3 VIP users, 2 regular)
- `thread_id`: Conversation thread identifier
- `department`: Engineering or Marketing
- `scenario_id`: Which observability scenario is being demonstrated (local-maf, maf-with-fas, etc.)
- `scenario_type`: Scenario category (single-agent, multi-agent, hybrid)

## Deployment Pipeline

### Image Management
1. **ACR Remote Build** - Automated container image builds
2. **Version Management** - Semantic versioning stored in configuration file
3. **Helm Deployment** - Automated AKS deployment with new image versions

### Infrastructure as Code
- **Terraform** - Complete infrastructure provisioning
- **Modular Design** - Segmented resource files (networking, monitoring, AI services)
- **Rich Documentation** - Comprehensive variable descriptions and examples

## Development Approach

### Phase 1: Foundation (Completed)
- Basic MAF agent with OTEL instrumentation ✅
- Core infrastructure deployment ✅
- Single-agent scenarios:
  - `local-maf`: Local MAF with Azure OpenAI Responses API ✅
  - `maf-with-fas`: MAF with Foundry Agent Service ✅
- MCP tool integration with dynamic parameter handling ✅
- Conditional observability (OTEL on/off) ✅

### Phase 2: Multi-Agent Patterns (In Progress)
- ✅ `local-maf-multiagent`: Magentic orchestration with local agents
- ⏳ `maf-with-fas-multiagent`: Cloud-hosted multi-agent with FAS
- ⏳ `local-maf-with-fas-multiagent`: Hybrid multi-agent (local orchestrator, FAS worker)
- ⏳ `local-maf-multiagent-a2a`: Local orchestrator with A2A worker
- ⏳ `maf-with-fas-multiagent-a2a`: FAS orchestrator with A2A worker
- Enhanced telemetry for multi-agent scenarios
- Agent collaboration patterns and metrics

### Phase 3: Advanced Observability (Planned)
- Custom metrics and dashboards per scenario
- Performance comparison across scenarios
- Cost analysis and optimization insights
- Best practices documentation

## Technology Stack

- **Runtime**: Python 3.12+ with Microsoft Agent Framework
- **Agent Clients**:
  - `AzureOpenAIResponsesClient`: For local-maf scenarios
  - `AzureAIAgentClient`: For maf-with-fas scenarios
- **Instrumentation**: OpenTelemetry Python SDK
- **Infrastructure**: Terraform + Azure
- **Containerization**: Docker + Kubernetes (AKS)
- **Package Management**: uv with pyproject.toml
- **API Framework**: FastAPI
- **Data Validation**: Pydantic models
- **Tool Protocol**: MCP (Model Context Protocol) via FastMCP

## OpenTelemetry Implementation

### Components
- **OTEL Collector** (`otel/opentelemetry-collector-contrib:0.115.1`)
  - Receives: OTLP gRPC (4317), OTLP HTTP (4318)
  - Exports: Console (debug) + Aspire Dashboard (18889)
  - Pipelines: Separate for traces, metrics, logs
  
- **Aspire Dashboard** (`mcr.microsoft.com/dotnet/aspire-dashboard:9.0`)
  - Web UI: `https://aspire.{domain}`
  - Features: Trace visualization, metrics, logs
  - Access: Anonymous (demo configuration)

### Service Instrumentation

**Agent** - Manual OTEL SDK with custom spans and scenario tracking:
- Scenario identification (local-maf, maf-with-fas, etc.)
- Tool registry operations with connection status
- Function calls with arguments and results
- Exception recording
- Conditional observability (enabled only when OTEL_EXPORTER_OTLP_ENDPOINT is set)

**API Server** - Automatic FastAPI instrumentation:
- All HTTP endpoints traced automatically
- Standard HTTP metadata captured

**MCP Server** - Hybrid (auto + manual):
- FastAPI auto-instrumentation for HTTP
- Manual spans for MCP tool execution
- Dynamic parameter handling via MCP protocol

### Configuration
All services use standard OTEL environment variables:
```yaml
OTEL_EXPORTER_OTLP_ENDPOINT: http://maf-demo-otel-collector:4317
OTEL_SERVICE_NAME: <service-name>
OTEL_RESOURCE_ATTRIBUTES: service.name=<service>,service.namespace=maf-demo
```

### Agent Azure Authentication
The agent uses Azure Workload Identity (federated identity) to authenticate with Azure AI Services:
- Service account: `maf-demo-agent` in `maf-demo` namespace
- Managed identity with federated credential linked to AKS OIDC issuer
- RBAC: Cognitive Services User + Cognitive Services OpenAI User roles
- No API keys required - authentication via Azure AD token exchange

### Architecture Flow
```
Agent/API/MCP → OTEL Collector (4317) → Aspire Dashboard (18889)
                      ↓
                Console (debug logs)

Agent Pod → Workload Identity → Azure AI Services (authenticated)
```

## Success Metrics

- **Scenario Coverage**: 7 scenarios planned across hosting and agent patterns
  - ✅ `local-maf`: Local, single-agent
  - ✅ `maf-with-fas`: Cloud, single-agent
  - ✅ `local-maf-multiagent`: Local, multi-agent with Magentic
  - ⏳ `maf-with-fas-multiagent`: Cloud, multi-agent
  - ⏳ `local-maf-with-fas-multiagent`: Hybrid, multi-agent
  - ⏳ `local-maf-multiagent-a2a`: Hybrid, multi-agent via A2A
  - ⏳ `maf-with-fas-multiagent-a2a`: Cloud, multi-agent via A2A
- **Trace Coverage**: Complete request flow visibility across all scenarios
- **Metric Richness**: Business and technical KPIs captured per scenario
- **Dashboard Utility**: Actionable insights comparing scenarios
- **Performance Impact**: Minimal overhead from observability instrumentation
- **Developer Experience**: Easy to understand, extend, and switch between scenarios
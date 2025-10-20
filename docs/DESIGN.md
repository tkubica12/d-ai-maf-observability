# Microsoft Agent Framework Observability Demo

## Purpose

Demonstrate comprehensive observability capabilities for Microsoft Agent Framework (MAF) applications across different deployment scenarios and interaction patterns. This project showcases how to instrument, collect, and visualize telemetry data from AI agents using OpenTelemetry standards.

## Observability Scenarios

### Agent Execution Patterns
1. **Native MAF Agent** - Agent running directly within MAF runtime
2. **Foundry Agent Service Integration** - MAF agent leveraging Azure AI Foundry Agent Service
3. **MCP Tool Integration** - Tool usage through Model Context Protocol (MCP)
4. **Foundry + MCP Hybrid** - Foundry Agent Service with MCP tool capabilities
5. **Function Calling Bridge** - Function calling as bridge to standard APIs
6. **Code Interpreter Tool** - Code execution and interpretation scenarios

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
- `scenario_type`: Which observability scenario is being demonstrated

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

### Phase 1: Foundation
- Basic MAF agent with OTEL instrumentation
- Core infrastructure deployment
- Simple observability scenario

### Phase 2: Integration
- Multiple agent execution patterns
- MCP tool integration
- Enhanced telemetry collection

### Phase 3: Advanced Scenarios
- Complex agent workflows
- Custom metrics and dashboards
- Performance optimization insights

## Technology Stack

- **Runtime**: Python with Microsoft Agent Framework
- **Instrumentation**: OpenTelemetry Python SDK
- **Infrastructure**: Terraform + Azure
- **Containerization**: Docker + Kubernetes
- **Package Management**: uv with pyproject.toml
- **API Framework**: FastAPI
- **Data Validation**: Pydantic models

## Success Metrics

- **Trace Coverage**: Complete request flow visibility across all scenarios
- **Metric Richness**: Business and technical KPIs captured
- **Dashboard Utility**: Actionable insights for different stakeholders
- **Performance Impact**: Minimal overhead from observability instrumentation
- **Developer Experience**: Easy to understand and extend telemetry collection
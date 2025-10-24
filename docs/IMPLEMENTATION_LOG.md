# Implementation Log

## 2025-10-20: Basic Service Implementation

### Objective
Create basic implementation for source services (Agent, MCP Server, API Server) with MAF integration, MCP function calling, and FastAPI endpoints.

### Architecture Implemented

```
┌─────────────────┐
│   MAF Agent     │  - Uses Microsoft Agent Framework
│                 │  - Sends user messages
│                 │  - Mandatory tool usage
└────────┬────────┘
         │ MCP Protocol
         │ (stdio)
         ▼
┌─────────────────┐
│  MCP Server     │  - FastMCP SDK
│                 │  - Exposes function calling tools
│                 │  - Bridges to API Server
└────────┬────────┘
         │ HTTP/REST
         │
         ▼
┌─────────────────┐
│  API Server     │  - FastAPI
│                 │  - Processes data
│                 │  - Returns results
└─────────────────┘
```

### Components Implemented

#### 1. API Server (`src/api_server/`)
**Purpose**: FastAPI-based REST API that processes function calls from MCP server.

**Key Features**:
- FastAPI framework with Pydantic models
- `/process` endpoint for data processing
- `/health` endpoint for health checks
- Environment-based configuration (.env)
- Docker support with Python 3.12

**Technologies**:
- FastAPI 0.115.0+
- Uvicorn 0.32.0+
- Pydantic 2.9.0+
- python-dotenv 1.0.0+

**Configuration**:
- `API_HOST`: Server host (default: 0.0.0.0)
- `API_PORT`: Server port (default: 8000)

#### 2. MCP Server (`src/mcp_server/`)
**Purpose**: MCP server using FastMCP SDK that exposes tools for agent function calling.

**Key Features**:
- FastMCP 2.0 implementation
- Two tools exposed:
  - `process_data`: Mandatory tool for processing user data (calls API server)
  - `get_status`: Health check tool (calls API server)
- STDIO transport for agent communication
- Environment-based configuration
- Docker support

**Technologies**:
- FastMCP 0.4.0+
- httpx 0.28.0+ (for async HTTP calls)
- python-dotenv 1.0.0+

**Configuration**:
- `API_SERVER_URL`: URL of API server (default: http://localhost:8000)

#### 3. Agent (`src/agent/`)
**Purpose**: Microsoft Agent Framework agent that uses MCP tools for processing user messages.

**Key Features**:
- MAF integration with Azure AI Project
- MCP client integration (stdio transport)
- Simple demo mode (works without Azure credentials)
- Full Azure mode (requires Azure AI Project)
- Mandatory tool usage pattern
- Environment-based configuration
- Docker support

**Technologies**:
- azure-ai-projects 1.0.0b7+
- azure-identity 1.21.1+
- mcp 1.12.0+
- python-dotenv 1.0.0+

**Configuration**:
- `PROJECT_CONNECTION_STRING`: Azure AI Project connection (optional for demo)
- `MODEL_DEPLOYMENT`: Model deployment name (default: gpt-4o)
- `MCP_SERVER_PATH`: Path to MCP server main.py
- `API_SERVER_URL`: API server URL for MCP

**Modes**:
1. **Simple Demo Mode**: Simulates agent behavior without Azure (for testing)
2. **Full Mode**: Complete MAF integration with Azure AI Project

### Design Decisions

1. **FastMCP SDK**: Chosen for MCP server due to simplicity and native Python async support
2. **FastAPI**: Selected for API server for modern Python REST API development with automatic OpenAPI docs
3. **STDIO Transport**: Used for MCP communication as it's the standard for agent-MCP integration
4. **Mandatory Tool Usage**: Implemented through agent instructions to ensure all data passes through API
5. **Demo Mode**: Added fallback mode to enable testing without Azure credentials
6. **Environment Configuration**: All services use .env files for configuration flexibility
7. **Docker Support**: All services have Dockerfiles using Python 3.12-slim base image

### Testing Results

✅ **API Server**: All endpoints tested and working
- GET `/` returns service info
- GET `/health` returns healthy status
- POST `/process` successfully processes data

✅ **MCP Server**: Both tools tested and working
- `process_data` tool successfully calls API server
- `get_status` tool successfully retrieves API health

✅ **Agent**: Both modes tested and working
- Simple demo mode runs without Azure
- MCP client integration verified
- Tool calling flow demonstrated

✅ **Integration**: Full stack tested
- API → MCP → Agent communication verified
- Data flows correctly through all layers
- Function calling pattern works as expected

### File Structure Created

```
src/
├── agent/
│   ├── .env.example
│   ├── Dockerfile
│   ├── README.md
│   ├── main.py
│   └── pyproject.toml
├── mcp_server/
│   ├── .env.example
│   ├── Dockerfile
│   ├── README.md
│   ├── main.py
│   └── pyproject.toml
└── api_server/
    ├── .env.example
    ├── Dockerfile
    ├── README.md
    ├── main.py
    └── pyproject.toml
```

### Dependencies Added

Each service has been configured with minimal, focused dependencies through pyproject.toml files. No requirements.txt files were created, following the uv package manager convention.

### Next Steps (Future Work)

1. Add OpenTelemetry instrumentation to all services
2. Implement user context and telemetry dimensions
3. Add more sophisticated agent workflows
4. Integrate with Azure Monitor and LangFuse
5. Add comprehensive unit and integration tests
6. Implement CI/CD pipeline for container builds
7. Add Kubernetes deployment configurations

## 2025-10-20: Azure Integration and RBAC Configuration

### Objective
Updated services for Azure integration with DefaultAzureCredential authentication, HTTP-based MCP server, and proper RBAC configuration.

### Changes Implemented

#### Service Updates
1. **MCP Server**: Converted from stdio to HTTP server with CORS support
2. **Agent**: Created two variants - Foundry Agent Service and Direct Model Access
3. **All Services**: Added DefaultAzureCredential authentication and configurable ports
4. **RBAC**: Added proper role assignments in Terraform

#### Terraform Issues Fixed
**Problem**: `uuidv4()` function error in Terraform role assignments
```
Error: Call to unknown function "uuidv4()"
```

**Root Cause**: Terraform doesn't have a built-in `uuidv4()` function

**Solution**: Used `random_uuid` resource instead:
```terraform
resource "random_uuid" "role_assignment_id" {}
resource "azapi_resource" "role_assignment" {
  name = random_uuid.role_assignment_id.result
  # ...
}
```

**Files Changed**:
- `infra/rbac.tf` - Fixed UUID generation and removed azurerm dependencies
- `infra/providers.tf` - Maintains azapi-only approach (no azurerm provider)
- `infra/variables.tf` - Added current_user_object_id variable for development RBAC
- `docs/COMMON_ERRORS.md` - Documented UUID fix and azapi-only requirement

**Important Architecture Decision**: This project uses **only azapi provider** - never add azurerm provider. All Azure resources and data sources must use azapi equivalents.

### Architectural Changes
- MCP Server now runs as HTTP server (port 8001) instead of stdio
- All services support configurable hosts/ports via environment variables
- Two agent variants: Foundry-based and direct model access
- Complete DefaultAzureCredential authentication chain


## 2025-10-24: Azure AI Agents SDK API Fixes

Fixed Azure AI Agents SDK API compatibility issues in the Foundry Agent Service approach.

# Helm Charts

This directory contains Helm charts for deploying the MAF Observability Demo application.

## maf_demo

The main chart that deploys both API and MCP tools with the following features:

- **API Tool**: FastAPI server providing REST endpoints
- **MCP Tool**: MCP server providing function calling capabilities  
- **Ingress**: NGINX ingress controller with Let's Encrypt SSL certificates
- **Service Discovery**: Kubernetes services for internal communication

### Hostnames

- API Tool: `api-tool.{base_domain}`
- MCP Tool: `mcp-tool.{base_domain}`

### Manual Deployment

If you need to deploy the chart manually:

```bash
helm install maf-demo ./maf_demo \
  --namespace maf-demo \
  --create-namespace \
  --set apiTool.image.repository=your-acr.azurecr.io/api-tool \
  --set apiTool.image.tag=v1 \
  --set mcpTool.image.repository=your-acr.azurecr.io/mcp-tool \
  --set mcpTool.image.tag=v1 \
  --set ingress.hosts.api.host=api-tool.yourdomain.com \
  --set ingress.hosts.mcp.host=mcp-tool.yourdomain.com
```
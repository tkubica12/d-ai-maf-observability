output "resource_group_name" {
  description = "Name of the created resource group"
  value       = azapi_resource.rg.name
}

output "aks_cluster_name" {
  description = "Name of the AKS cluster"
  value       = azapi_resource.aks.name
}

output "aks_cluster_id" {
  description = "Resource ID of the AKS cluster"
  value       = azapi_resource.aks.id
}

output "aks_oidc_issuer_url" {
  description = "OIDC issuer URL for workload identity federation"
  value       = azapi_resource.aks.output.properties.oidcIssuerProfile.issuerURL
}

output "acr_name" {
  description = "Name of the Azure Container Registry"
  value       = azapi_resource.acr.name
}

output "acr_login_server" {
  description = "Login server URL for the Azure Container Registry"
  value       = azapi_resource.acr.output.properties.loginServer
}

output "ai_services_endpoint" {
  description = "Endpoint URL for Azure AI Services"
  value       = azapi_resource.ai_services.output.properties.endpoint
}

output "ai_foundry_endpoint" {
  description = "Azure AI Foundry API endpoint for model inference"
  value       = azapi_resource.ai_services.output.properties.endpoints["AI Foundry API"]
}

output "ai_project_endpoint" {
  description = "Azure AI Project endpoint for Foundry Agent Service"
  value       = azapi_resource.ai_project.output.properties.endpoints["AI Foundry API"]
}

output "ai_services_name" {
  description = "Name of the Azure AI Services account"
  value       = azapi_resource.ai_services.name
}

output "app_insights_instrumentation_key" {
  description = "Application Insights instrumentation key"
  value       = azapi_resource.app_insights.output.properties.InstrumentationKey
  sensitive   = true
}

output "app_insights_connection_string" {
  description = "Application Insights connection string"
  value       = azapi_resource.app_insights.output.properties.ConnectionString
  sensitive   = true
}

output "grafana_endpoint" {
  description = "Azure Managed Grafana endpoint URL"
  value       = azapi_resource.grafana.output.properties.endpoint
}

output "prometheus_query_endpoint" {
  description = "Azure Monitor Prometheus query endpoint"
  value       = azapi_resource.prometheus.output.properties.metrics.prometheusQueryEndpoint
}

output "prometheus_remote_write_endpoint" {
  description = "Azure Monitor Prometheus remote write ingestion endpoint (full URL with DCR path)"
  value       = "${azapi_resource.prometheus_data_collection_endpoint.output.properties.metricsIngestion.endpoint}/dataCollectionRules/${azapi_resource.prometheus_data_collection_rule.output.properties.immutableId}/streams/Microsoft-PrometheusMetrics/api/v1/write?api-version=2023-04-24"
}

output "vnet_id" {
  description = "Resource ID of the virtual network"
  value       = azapi_resource.vnet.id
}

output "aks_subnet_id" {
  description = "Resource ID of the AKS subnet"
  value       = azapi_resource.aks_subnet.id
}

output "user_assigned_identity_id" {
  description = "Resource ID of the user-assigned managed identity"
  value       = azapi_resource.user_assigned_identity.id
}

output "user_assigned_identity_client_id" {
  description = "Client ID of the user-assigned managed identity"
  value       = azapi_resource.user_assigned_identity.output.properties.clientId
}

output "user_assigned_identity_principal_id" {
  description = "Principal ID of the user-assigned managed identity"
  value       = azapi_resource.user_assigned_identity.output.properties.principalId
}

output "ai_models_endpoint" {
  description = "Direct endpoint URL for Azure AI models (for inference)"
  value       = "${azapi_resource.ai_services.output.properties.endpoint}models"
}

output "ingress_public_ip_address" {
  description = "Public IP address for the ingress controller"
  value       = azapi_resource.ingress_public_ip.output.properties.ipAddress
}

output "ingress_public_ip_name" {
  description = "Name of the public IP for the ingress controller"
  value       = azapi_resource.ingress_public_ip.name
}

output "ingress_public_ip_fqdn" {
  description = "Fully qualified domain name for the ingress public IP"
  value       = azapi_resource.ingress_public_ip.output.properties.dnsSettings.fqdn
}

output "api_tool_url" {
  description = "URL for the API tool service"
  value       = "https://api-tool.${var.base_domain}"
}

output "mcp_tool_url" {
  description = "URL for the MCP tool service"
  value       = "https://mcp-tool.${var.base_domain}"
}

output "aspire_dashboard_url" {
  description = "URL for the Aspire Dashboard (OpenTelemetry UI)"
  value       = "https://aspire.${var.base_domain}"
}

output "grafana_dashboard_folder" {
  description = "Grafana folder name for AI Agent Observability dashboards"
  sensitive   = true
  value       = var.grafana_auth_token != "" ? grafana_folder.ai_agent_observability[0].title : "Not provisioned (grafana_auth_token not set)"
}

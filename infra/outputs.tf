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

output "vnet_id" {
  description = "Resource ID of the virtual network"
  value       = azapi_resource.vnet.id
}

output "aks_subnet_id" {
  description = "Resource ID of the AKS subnet"
  value       = azapi_resource.aks_subnet.id
}

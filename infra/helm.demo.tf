

# MAF Demo Application
resource "helm_release" "maf_demo" {
  name      = "maf-demo"
  chart     = "../charts/maf_demo"
  namespace = "maf-demo"

  create_namespace = true

  values = [
    yamlencode({
      apiTool = {
        image = {
          repository = "${azapi_resource.acr.output.properties.loginServer}/api-tool"
          tag        = var.api_tool_image_tag
        }
      }
      mcpTool = {
        image = {
          repository = "${azapi_resource.acr.output.properties.loginServer}/mcp-tool"
          tag        = var.mcp_tool_image_tag
        }
      }
      agent = {
        image = {
          repository = "${azapi_resource.acr.output.properties.loginServer}/agent"
          tag        = var.agent_image_tag
        }
        clientId = azapi_resource.user_assigned_identity.output.properties.clientId
        tenantId = azapi_resource.user_assigned_identity.output.properties.tenantId
        # AI endpoint for local-maf scenario (Azure OpenAI format)
        aiEndpoint = azapi_resource.ai_services.output.properties.endpoints["Azure OpenAI Legacy API - Latest moniker"]
        # Project endpoint for maf-with-fas scenario (Foundry Agent Service)
        projectEndpoint = azapi_resource.ai_project.output.properties.endpoints["AI Foundry API"]
        modelName       = var.ai_model_name
        modelDeployment = var.ai_model_name
        # API and MCP server URLs from ingress configuration
        apiServerUrl = "https://api-tool.${var.base_domain}"
        mcpServerUrl = "https://mcp-tool.${var.base_domain}"
      }
      appInsights = {
        connectionString = azapi_resource.app_insights.output.properties.ConnectionString
      }
      prometheus = {
        remoteWriteEndpoint = azapi_resource.prometheus_data_collection_endpoint.output.properties.metricsIngestion.endpoint
      }
      clusterName = azapi_resource.aks.name
      ingress = {
        hosts = {
          api = {
            host = "api-tool.${var.base_domain}"
          }
          mcp = {
            host = "mcp-tool.${var.base_domain}"
          }
          aspire = {
            host = "aspire.${var.base_domain}"
          }
        }
        tls = [
          {
            secretName = "api-tool-tls"
            hosts      = ["api-tool.${var.base_domain}"]
          },
          {
            secretName = "mcp-tool-tls"
            hosts      = ["mcp-tool.${var.base_domain}"]
          },
          {
            secretName = "aspire-dashboard-tls"
            hosts      = ["aspire.${var.base_domain}"]
          }
        ]
      }
      letsencrypt = {
        email = var.letsencrypt_email
      }
    })
  ]

  depends_on = [
    helm_release.nginx_ingress,
    helm_release.cert_manager,
    azapi_resource.acr
  ]
}

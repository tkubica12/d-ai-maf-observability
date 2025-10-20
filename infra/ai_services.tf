resource "azapi_resource" "ai_services" {
  type      = "Microsoft.CognitiveServices/accounts@2024-04-01-preview"
  name      = "${var.project_name}-${var.environment}-aiservices"
  location  = var.location
  parent_id = azapi_resource.rg.id

  body = {
    kind = "AIServices"
    sku = {
      name = "S0"
    }
    properties = {
      customSubDomainName = "${var.project_name}${var.environment}ai${random_string.acr_suffix.result}"
      publicNetworkAccess = "Enabled"
      networkAcls = {
        defaultAction = "Allow"
      }
    }
  }
}

resource "azapi_resource" "ai_model_deployment" {
  type      = "Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview"
  name      = var.ai_model_name
  parent_id = azapi_resource.ai_services.id

  body = {
    sku = {
      name     = "GlobalStandard"
      capacity = var.ai_model_capacity
    }
    properties = {
      model = {
        format  = "OpenAI"
        name    = var.ai_model_name
        version = var.ai_model_version
      }
      versionUpgradeOption = "OnceCurrentVersionExpired"
    }
  }
}

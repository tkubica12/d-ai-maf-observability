resource "azapi_resource" "ai_services" {
  type      = "Microsoft.CognitiveServices/accounts@2025-06-01"
  name      = "${var.project_name}-${var.environment}-aiservices"
  location  = var.location
  parent_id = azapi_resource.rg.id

  body = {
    kind = "AIServices"
    identity = {
      type = "SystemAssigned"
    }
    sku = {
      name = "S0"
    }
    properties = {
      allowProjectManagement = true
      customSubDomainName    = "${var.project_name}${var.environment}ai${random_string.acr_suffix.result}"
      publicNetworkAccess    = "Enabled"
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

# TODO: Remove when FAS supports gpt-5-nano with MCP
# Hardcoded gpt-4.1-mini deployment as workaround for FAS + MCP compatibility
resource "azapi_resource" "ai_model_deployment_workaround" {
  type      = "Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview"
  name      = "gpt-4.1-mini"
  parent_id = azapi_resource.ai_services.id

  body = {
    sku = {
      name     = "GlobalStandard"
      capacity = 100
    }
    properties = {
      model = {
        format  = "OpenAI"
        name    = "gpt-4.1-mini"
        version = "2025-04-14"
      }
      versionUpgradeOption = "OnceCurrentVersionExpired"
    }
  }

  depends_on = [azapi_resource.ai_model_deployment]
}

resource "azapi_resource" "ai_project" {
  type      = "Microsoft.CognitiveServices/accounts/projects@2025-07-01-preview"
  name      = "${var.project_name}-project"
  location  = var.location
  parent_id = azapi_resource.ai_services.id

  identity {
    type = "SystemAssigned"
  }

  body = {
    properties = {
      description = "MAF Observability AI Project"
      displayName = "MAF Observability Project"
    }
  }

  schema_validation_enabled = false
  depends_on                = [azapi_resource.ai_services]
}

resource "azapi_resource" "user_assigned_identity" {
  type      = "Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31"
  name      = "${var.project_name}-${var.environment}-identity"
  location  = var.location
  parent_id = azapi_resource.rg.id
}

# Federated credential for agent workload identity in AKS
resource "azapi_resource" "agent_federated_credential" {
  type      = "Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2023-01-31"
  name      = "agent-federated-credential"
  parent_id = azapi_resource.user_assigned_identity.id

  body = {
    properties = {
      audiences = ["api://AzureADTokenExchange"]
      issuer    = azapi_resource.aks.output.properties.oidcIssuerProfile.issuerURL
      subject   = "system:serviceaccount:maf-demo:maf-demo-agent"
    }
  }

  depends_on = [azapi_resource.aks]
}

# Federated credential for OTEL collector workload identity in AKS
# Allows OTEL collector to authenticate with Azure Monitor Prometheus
resource "azapi_resource" "otel_collector_federated_credential" {
  type      = "Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2023-01-31"
  name      = "otel-collector-federated-credential"
  parent_id = azapi_resource.user_assigned_identity.id

  body = {
    properties = {
      audiences = ["api://AzureADTokenExchange"]
      issuer    = azapi_resource.aks.output.properties.oidcIssuerProfile.issuerURL
      subject   = "system:serviceaccount:maf-demo:maf-demo-otel-collector"
    }
  }

  depends_on = [azapi_resource.aks]
}

# Generate UUIDs for role assignments
resource "random_uuid" "cognitive_services_user_role_id" {}
resource "random_uuid" "cognitive_services_openai_user_role_id" {}
resource "random_uuid" "ai_project_contributor_role_id" {}
resource "random_uuid" "current_user_cognitive_services_user_role_id" {}
resource "random_uuid" "current_user_cognitive_services_openai_user_role_id" {}
resource "random_uuid" "current_user_cognitive_services_contributor_role_id" {}
resource "random_uuid" "current_user_grafana_admin_role_id" {}
resource "random_uuid" "aks_network_contributor_role_id" {}
resource "random_uuid" "aks_managed_identity_operator_role_id" {}
resource "random_uuid" "aks_acr_role_id" {}

# Role assignment for Azure AI Services access - Cognitive Services User
resource "azapi_resource" "cognitive_services_user_role_assignment" {
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = random_uuid.cognitive_services_user_role_id.result
  parent_id = azapi_resource.ai_services.id

  body = {
    properties = {
      roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/a97b65f3-24c7-4388-baec-2e87135dc908" # Cognitive Services User
      principalId      = azapi_resource.user_assigned_identity.output.properties.principalId
      principalType    = "ServicePrincipal"
    }
  }

  depends_on = [azapi_resource.user_assigned_identity]
}

# Role assignment for Azure AI Services access - Cognitive Services OpenAI User (for direct model access)
resource "azapi_resource" "cognitive_services_openai_user_role_assignment" {
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = random_uuid.cognitive_services_openai_user_role_id.result
  parent_id = azapi_resource.ai_services.id

  body = {
    properties = {
      roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/5e0bd9bd-7b93-4f28-af87-19fc36ad61bd" # Cognitive Services OpenAI User
      principalId      = azapi_resource.user_assigned_identity.output.properties.principalId
      principalType    = "ServicePrincipal"
    }
  }

  depends_on = [azapi_resource.user_assigned_identity]
}

# Role assignment for Azure AI Project access - Contributor role on the project
resource "azapi_resource" "ai_project_contributor_role_assignment" {
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = random_uuid.ai_project_contributor_role_id.result
  parent_id = azapi_resource.ai_project.id

  body = {
    properties = {
      roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c" # Contributor
      principalId      = azapi_resource.user_assigned_identity.output.properties.principalId
      principalType    = "ServicePrincipal"
    }
  }

  depends_on = [
    azapi_resource.user_assigned_identity,
    azapi_resource.ai_project
  ]
}

# Role assignment for current user - needed for development
# Note: Provide current_user_object_id variable for development access
resource "azapi_resource" "current_user_cognitive_services_user_role" {
  count     = var.current_user_object_id != null ? 1 : 0
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = random_uuid.current_user_cognitive_services_user_role_id.result
  parent_id = azapi_resource.ai_services.id

  body = {
    properties = {
      roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/a97b65f3-24c7-4388-baec-2e87135dc908" # Cognitive Services User
      principalId      = var.current_user_object_id
      principalType    = "User"
    }
  }
}

resource "azapi_resource" "current_user_cognitive_services_openai_user_role" {
  count     = var.current_user_object_id != null ? 1 : 0
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = random_uuid.current_user_cognitive_services_openai_user_role_id.result
  parent_id = azapi_resource.ai_services.id

  body = {
    properties = {
      roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/5e0bd9bd-7b93-4f28-af87-19fc36ad61bd" # Cognitive Services OpenAI User
      principalId      = var.current_user_object_id
      principalType    = "User"
    }
  }
}

# Additional role assignment for MaaS access - Cognitive Services Contributor
resource "azapi_resource" "current_user_cognitive_services_contributor_role" {
  count     = var.current_user_object_id != null ? 1 : 0
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = random_uuid.current_user_cognitive_services_contributor_role_id.result
  parent_id = azapi_resource.ai_services.id

  body = {
    properties = {
      roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/25fbc0a9-bd7c-42a3-aa1a-3b75d497ee68" # Cognitive Services Contributor
      principalId      = var.current_user_object_id
      principalType    = "User"
    }
  }
}

# Role assignment for current user - Grafana Admin
resource "azapi_resource" "current_user_grafana_admin_role" {
  count     = var.current_user_object_id != null ? 1 : 0
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = random_uuid.current_user_grafana_admin_role_id.result
  parent_id = azapi_resource.grafana.id

  body = {
    properties = {
      roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/22926164-76b3-42b3-bc55-97df8dab3e41" # Grafana Admin
      principalId      = var.current_user_object_id
      principalType    = "User"
    }
  }
}

# Role assignment: AKS identity as Network Contributor on resource group
# Allows the AKS identity to read and manage network resources including public IPs
# Required for NGINX ingress controller to use annotated public IP
resource "azapi_resource" "aks_network_contributor_role" {
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = random_uuid.aks_network_contributor_role_id.result
  parent_id = azapi_resource.rg.id

  body = {
    properties = {
      roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/4d97b98b-1d4f-4787-a291-c67834d212e7"
      principalId      = azapi_resource.aks_identity.output.properties.principalId
      principalType    = "ServicePrincipal"
    }
  }

  depends_on = [
    azapi_resource.aks_identity
  ]
}

# Role assignment: AKS identity as Managed Identity Operator on itself
# Allows the AKS control plane to assign the kubelet identity
# Required when using custom kubelet identity
resource "azapi_resource" "aks_managed_identity_operator_role" {
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = random_uuid.aks_managed_identity_operator_role_id.result
  parent_id = azapi_resource.aks_identity.id

  body = {
    properties = {
      roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/f1a07417-d97a-45cb-824c-7a7467783830"
      principalId      = azapi_resource.aks_identity.output.properties.principalId
      principalType    = "ServicePrincipal"
    }
  }

  depends_on = [
    azapi_resource.aks_identity
  ]
}

# RBAC configuration for Azure AI Services access
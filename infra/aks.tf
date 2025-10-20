resource "azapi_resource" "aks_identity" {
  type      = "Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31"
  name      = "${var.project_name}-${var.environment}-aks-identity"
  location  = var.location
  parent_id = azapi_resource.rg.id

  body = {}
}

resource "azapi_resource" "aks" {
  type      = "Microsoft.ContainerService/managedClusters@2024-05-01"
  name      = "${var.project_name}-${var.environment}-aks"
  location  = var.location
  parent_id = azapi_resource.rg.id

  identity {
    type = "UserAssigned"
    identity_ids = [
      azapi_resource.aks_identity.id
    ]
  }

  body = {
    properties = {
      kubernetesVersion = var.aks_kubernetes_version
      dnsPrefix         = "${var.project_name}-${var.environment}"

      networkProfile = {
        networkPlugin = "azure"
        serviceCidr   = "10.1.0.0/16"
        dnsServiceIP  = "10.1.0.10"
      }

      agentPoolProfiles = [
        {
          name              = "default"
          count             = var.aks_node_count
          vmSize            = var.aks_node_vm_size
          mode              = "System"
          osType            = "Linux"
          osSKU             = "Ubuntu"
          type              = "VirtualMachineScaleSets"
          enableAutoScaling = true
          minCount          = var.aks_node_count
          maxCount          = var.aks_node_count + 3
          vnetSubnetID      = azapi_resource.aks_subnet.id
        }
      ]

      oidcIssuerProfile = {
        enabled = true
      }

      securityProfile = {
        workloadIdentity = {
          enabled = true
        }
      }
    }
  }

  depends_on = [
    azapi_update_resource.aks_subnet_nat
  ]
}

resource "azapi_resource" "aks_acr_role" {
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = uuid()
  parent_id = azapi_resource.acr.id

  body = {
    properties = {
      roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/7f951dda-4ed3-4680-a7ca-43fe172d538d"
      principalId      = azapi_resource.aks_identity.output.properties.principalId
      principalType    = "ServicePrincipal"
    }
  }
}

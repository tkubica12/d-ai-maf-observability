resource "azapi_resource" "log_analytics" {
  type      = "Microsoft.OperationalInsights/workspaces@2023-09-01"
  name      = "${var.project_name}-${var.environment}-law"
  location  = var.location
  parent_id = azapi_resource.rg.id

  body = {
    properties = {
      sku = {
        name = "PerGB2018"
      }
      retentionInDays = 30
    }
  }
}

resource "azapi_resource" "app_insights" {
  type      = "Microsoft.Insights/components@2020-02-02"
  name      = "${var.project_name}-${var.environment}-ai"
  location  = var.location
  parent_id = azapi_resource.rg.id

  body = {
    kind = "web"
    properties = {
      Application_Type    = "web"
      WorkspaceResourceId = azapi_resource.log_analytics.id
    }
  }
}

resource "azapi_resource" "prometheus" {
  type      = "Microsoft.Monitor/accounts@2023-04-03"
  name      = "${var.project_name}-${var.environment}-prometheus"
  location  = var.location
  parent_id = azapi_resource.rg.id

  body = {}
}

resource "azapi_resource" "grafana" {
  type      = "Microsoft.Dashboard/grafana@2023-09-01"
  name      = "${var.project_name}-${var.environment}-grafana"
  location  = var.location
  parent_id = azapi_resource.rg.id

  identity {
    type = "SystemAssigned"
  }

  body = {
    sku = {
      name = var.grafana_sku
    }
    properties = {
      grafanaIntegrations = {
        azureMonitorWorkspaceIntegrations = [
          {
            azureMonitorWorkspaceResourceId = azapi_resource.prometheus.id
          }
        ]
      }
      publicNetworkAccess = "Enabled"
      zoneRedundancy      = "Disabled"
    }
  }
}

resource "random_uuid" "grafana_prometheus_reader_role_id" {}

resource "azapi_resource" "grafana_prometheus_reader_role" {
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = random_uuid.grafana_prometheus_reader_role_id.result
  parent_id = azapi_resource.prometheus.id

  body = {
    properties = {
      roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/b0d8363b-8ddd-447d-831f-62ca05bff136"
      principalId      = azapi_resource.grafana.identity[0].principal_id
      principalType    = "ServicePrincipal"
    }
  }
}

resource "random_uuid" "grafana_log_analytics_reader_role_id" {}

resource "azapi_resource" "grafana_log_analytics_reader_role" {
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = random_uuid.grafana_log_analytics_reader_role_id.result
  parent_id = azapi_resource.log_analytics.id

  body = {
    properties = {
      roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/43d0d8ad-25c7-4714-9337-8ba259a9fe05"
      principalId      = azapi_resource.grafana.identity[0].principal_id
      principalType    = "ServicePrincipal"
    }
  }
}

resource "azapi_resource" "prometheus_data_collection_endpoint" {
  type      = "Microsoft.Insights/dataCollectionEndpoints@2023-03-11"
  name      = "${var.project_name}-${var.environment}-dce"
  location  = var.location
  parent_id = azapi_resource.rg.id

  body = {
    properties = {
      networkAcls = {
        publicNetworkAccess = "Enabled"
      }
    }
  }
}

resource "azapi_resource" "prometheus_data_collection_rule" {
  type      = "Microsoft.Insights/dataCollectionRules@2023-03-11"
  name      = "${var.project_name}-${var.environment}-dcr"
  location  = var.location
  parent_id = azapi_resource.rg.id

  body = {
    properties = {
      dataCollectionEndpointId = azapi_resource.prometheus_data_collection_endpoint.id
      dataSources = {
        prometheusForwarder = [
          {
            name    = "PrometheusDataSource"
            streams = ["Microsoft-PrometheusMetrics"]
          }
        ]
      }
      destinations = {
        monitoringAccounts = [
          {
            accountResourceId = azapi_resource.prometheus.id
            name              = "MonitoringAccount"
          }
        ]
      }
      dataFlows = [
        {
          streams      = ["Microsoft-PrometheusMetrics"]
          destinations = ["MonitoringAccount"]
        }
      ]
    }
  }
}

resource "azapi_resource" "prometheus_dcr_association" {
  type      = "Microsoft.Insights/dataCollectionRuleAssociations@2023-03-11"
  name      = "${var.project_name}-${var.environment}-dcra"
  parent_id = azapi_resource.aks.id

  body = {
    properties = {
      dataCollectionRuleId = azapi_resource.prometheus_data_collection_rule.id
    }
  }
}

# Assign Monitoring Metrics Publisher role to user-assigned identity for OTEL collector remote write
resource "random_uuid" "otel_prometheus_publisher_role_id" {}

resource "azapi_resource" "otel_prometheus_publisher_role" {
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = random_uuid.otel_prometheus_publisher_role_id.result
  parent_id = azapi_resource.prometheus_data_collection_rule.id

  body = {
    properties = {
      roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/3913510d-42f4-4e42-8a64-420c390055eb"
      principalId      = azapi_resource.user_assigned_identity.output.properties.principalId
      principalType    = "ServicePrincipal"
    }
  }
}

resource "random_string" "acr_suffix" {
  length  = 6
  special = false
  upper   = false
}

resource "azapi_resource" "acr" {
  type      = "Microsoft.ContainerRegistry/registries@2023-11-01-preview"
  name      = "${var.project_name}${var.environment}acr${random_string.acr_suffix.result}"
  location  = var.location
  parent_id = azapi_resource.rg.id

  body = {
    sku = {
      name = var.acr_sku
    }
    properties = {
      adminUserEnabled    = true
      publicNetworkAccess = "Enabled"
    }
  }
}

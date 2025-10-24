resource "azapi_resource" "ingress_public_ip" {
  type      = "Microsoft.Network/publicIPAddresses@2023-09-01"
  name      = "${var.project_name}-${var.environment}-ingress-pip"
  location  = var.location
  parent_id = azapi_resource.rg.id

  body = {
    sku = {
      name = "Standard"
      tier = "Regional"
    }
    properties = {
      publicIPAllocationMethod = "Static"
      publicIPAddressVersion   = "IPv4"
      dnsSettings = {
        domainNameLabel = "${var.project_name}-${var.environment}-ingress"
      }
    }
  }

  response_export_values = ["properties.ipAddress", "properties.dnsSettings.fqdn"]
}
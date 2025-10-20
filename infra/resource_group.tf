resource "azapi_resource" "rg" {
  type     = "Microsoft.Resources/resourceGroups@2024-03-01"
  name     = var.resource_group_name
  location = var.location
  body     = {}
}

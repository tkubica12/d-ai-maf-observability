resource "azapi_resource" "vnet" {
  type      = "Microsoft.Network/virtualNetworks@2024-01-01"
  name      = "${var.project_name}-${var.environment}-vnet"
  location  = var.location
  parent_id = azapi_resource.rg.id

  body = {
    properties = {
      addressSpace = {
        addressPrefixes = var.vnet_address_space
      }
    }
  }
}

resource "azapi_resource" "aks_subnet" {
  type      = "Microsoft.Network/virtualNetworks/subnets@2024-01-01"
  name      = "aks-subnet"
  parent_id = azapi_resource.vnet.id

  body = {
    properties = {
      addressPrefix = var.aks_subnet_address_prefix
    }
  }
}

resource "azapi_resource" "nat_gateway_public_ip" {
  type      = "Microsoft.Network/publicIPAddresses@2024-01-01"
  name      = "${var.project_name}-${var.environment}-nat-pip"
  location  = var.location
  parent_id = azapi_resource.rg.id

  body = {
    sku = {
      name = "Standard"
    }
    properties = {
      publicIPAllocationMethod = "Static"
      publicIPAddressVersion   = "IPv4"
    }
  }
}

resource "azapi_resource" "nat_gateway" {
  type      = "Microsoft.Network/natGateways@2024-01-01"
  name      = "${var.project_name}-${var.environment}-nat"
  location  = var.location
  parent_id = azapi_resource.rg.id

  body = {
    sku = {
      name = "Standard"
    }
    properties = {
      publicIpAddresses = [
        {
          id = azapi_resource.nat_gateway_public_ip.id
        }
      ]
    }
  }
}

resource "azapi_update_resource" "aks_subnet_nat" {
  type        = "Microsoft.Network/virtualNetworks/subnets@2024-01-01"
  resource_id = azapi_resource.aks_subnet.id

  body = {
    properties = {
      addressPrefix = var.aks_subnet_address_prefix
      natGateway = {
        id = azapi_resource.nat_gateway.id
      }
    }
  }

  depends_on = [
    azapi_resource.aks_subnet,
    azapi_resource.nat_gateway
  ]
}

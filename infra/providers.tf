terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azapi = {
      source  = "azure/azapi"
      version = "2.7.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
    grafana = {
      source  = "grafana/grafana"
      version = "~> 3.0"
    }
  }
}

provider "azapi" {
  subscription_id = var.subscription_id
}

provider "random" {}

provider "helm" {
  kubernetes {
    config_path = local_file.kubeconfig.filename
  }
}

provider "local" {}

provider "grafana" {
  url  = azapi_resource.grafana.output.properties.endpoint
  auth = var.grafana_auth_token
}

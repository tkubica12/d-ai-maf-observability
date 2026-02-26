variable "subscription_id" {
  type        = string
  description = <<-EOT
    Azure subscription ID where resources will be deployed.
    Required for azapi provider configuration.
    Example: "12345678-1234-1234-1234-123456789012"
  EOT
}

variable "location" {
  type        = string
  description = <<-EOT
    Azure region for resource deployment.
    Choose a region that supports all required services (AKS, AI Foundry, etc.).
    Example: "eastus", "westeurope", "westus2"
  EOT
  default     = "swedencentral"
}

variable "resource_group_name" {
  type        = string
  description = <<-EOT
    Name of the Azure Resource Group to create.
    All infrastructure resources will be deployed within this resource group.
    Example: "rg-maf-observability-prod"
  EOT
  default     = "rg-maf-observability"
}

variable "project_name" {
  type        = string
  description = <<-EOT
    Project name used as prefix for resource naming.
    Should be short (3-8 characters) and lowercase for compatibility.
    Example: "mafobs", "aiobs"
  EOT
  default     = "mafobs"
}

variable "environment" {
  type        = string
  description = <<-EOT
    Environment designation for resource naming and configuration.
    Common values: "dev", "test", "staging", "prod"
  EOT
  default     = "dev"
}

variable "vnet_address_space" {
  type        = list(string)
  description = <<-EOT
    CIDR address space for the custom VNET.
    Should be large enough to accommodate AKS node pools and services.
    Example: ["10.0.0.0/16"]
  EOT
  default     = ["10.0.0.0/16"]
}

variable "aks_subnet_address_prefix" {
  type        = string
  description = <<-EOT
    CIDR address prefix for the AKS subnet within the VNET.
    Must be within the vnet_address_space range.
    Size according to expected node count and pod density.
    Example: "10.0.1.0/24"
  EOT
  default     = "10.0.1.0/24"
}

variable "aks_node_count" {
  type        = number
  description = <<-EOT
    Initial number of nodes in the AKS default node pool.
    Consider workload requirements and high availability needs.
    Minimum: 1, Recommended for production: 3
  EOT
  default     = 1
}

variable "aks_node_vm_size" {
  type        = string
  description = <<-EOT
    VM size for AKS nodes.
    Choose based on workload requirements (CPU, memory, GPU).
    Example: "Standard_D4s_v3", "Standard_DS2_v2"
  EOT
  default     = "Standard_B4as_v2"
}

variable "aks_kubernetes_version" {
  type        = string
  description = <<-EOT
    Kubernetes version for AKS cluster.
    Use "automatic" for auto-upgrade or specify version like "1.28".
    Check available versions with: az aks get-versions --location <location>
  EOT
  default     = "1.32"
}

variable "ai_model_name" {
  type        = string
  description = <<-EOT
    Name of the AI model to deploy in Azure AI Foundry.
    Supported models: "gpt-5-nano", "gpt-4o", "gpt-4o-mini", "gpt-35-turbo"
    Example: "gpt-5-nano"
  EOT
  default     = "gpt-5-nano"
}

variable "ai_model_version" {
  type        = string
  description = <<-EOT
    Version of the AI model to deploy.
    Check available versions in Azure AI Foundry portal.
    Example: "2025-08-07", "latest"
  EOT
  default     = "2025-08-07"
}

variable "ai_model_capacity" {
  type        = number
  description = <<-EOT
    Model deployment capacity in units.
    Determines throughput and rate limits.
    Standard range: 1-1000, must be multiple of 10 for some models
  EOT
  default     = 100
}

variable "acr_sku" {
  type        = string
  description = <<-EOT
    Azure Container Registry SKU tier.
    Options: "Basic", "Standard", "Premium"
    Premium required for geo-replication and private endpoints.
  EOT
  default     = "Basic"
}

variable "grafana_sku" {
  type        = string
  description = <<-EOT
    Azure Managed Grafana SKU.
    Options: "Standard" (default and recommended)
  EOT
  default     = "Standard"
}

variable "current_user_object_id" {
  type        = string
  description = <<-EOT
    Object ID of the current user for development RBAC assignments.
    Optional - if not provided, user-specific role assignments will be skipped.
    Get this value with: az ad signed-in-user show --query id --output tsv
    Example: "12345678-1234-1234-1234-123456789012"
  EOT
  default     = null
}

variable "base_domain" {
  type        = string
  description = <<-EOT
    Base domain name for ingress hostnames.
    API service will be available at api-tool.<base_domain>
    MCP service will be available at mcp-tool.<base_domain>
    Example: "example.com", "myproject.dev"
  EOT
}

variable "letsencrypt_email" {
  type        = string
  description = <<-EOT
    Email address for Let's Encrypt certificate registration.
    This email will receive notifications about certificate expiration.
    Required for ACME certificate provisioning.
    Example: "admin@example.com", "certificates@myproject.dev"
  EOT
}

variable "api_tool_image_tag" {
  type        = string
  description = <<-EOT
    Docker image tag for the API tool container.
    Used for versioning and deployment control.
    Example: "v1", "v2", "latest"
  EOT
  default     = "latest"
}

variable "mcp_tool_image_tag" {
  type        = string
  description = <<-EOT
    Docker image tag for the MCP tool container.
    Used for versioning and deployment control.
    Example: "v1", "v2", "latest"
  EOT
  default     = "latest"
}

variable "agent_image_tag" {
  type        = string
  description = <<-EOT
    Docker image tag for the MAF agent container.
    Used for versioning and deployment control.
    Example: "v1", "v2", "latest"
  EOT
  default     = "latest"
}

variable "grafana_auth_token" {
  type        = string
  sensitive   = true
  description = <<-EOT
    Azure AD access token for Grafana API authentication.
    Used by the grafana/grafana Terraform provider to manage dashboards
    in Azure Managed Grafana.

    Obtain with:
      az account get-access-token --resource ce34e7e5-485f-4d76-964f-b3d2b16d1e4f --query accessToken -o tsv

    If not provided, Grafana dashboard provisioning is skipped.
    Example: "eyJ0eXAiOiJKV1Qi..."
  EOT
  default     = ""
}

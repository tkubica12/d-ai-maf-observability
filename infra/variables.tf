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
  default     = "eastus"
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
  default     = 3
}

variable "aks_node_vm_size" {
  type        = string
  description = <<-EOT
    VM size for AKS nodes.
    Choose based on workload requirements (CPU, memory, GPU).
    Example: "Standard_D4s_v3", "Standard_DS2_v2"
  EOT
  default     = "Standard_D4s_v3"
}

variable "aks_kubernetes_version" {
  type        = string
  description = <<-EOT
    Kubernetes version for AKS cluster.
    Use "automatic" for auto-upgrade or specify version like "1.28".
    Check available versions with: az aks get-versions --location <location>
  EOT
  default     = null
}

variable "ai_model_name" {
  type        = string
  description = <<-EOT
    Name of the AI model to deploy in Azure AI Foundry.
    Example: "gpt-5-nano"
  EOT
  default     = "gpt-5-nano"
}

variable "ai_model_version" {
  type        = string
  description = <<-EOT
    Version of the AI model to deploy.
    Check available versions in Azure AI Foundry portal.
    Example: "0301", "latest"
  EOT
  default     = "latest"
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
  default     = "Standard"
}

variable "grafana_sku" {
  type        = string
  description = <<-EOT
    Azure Managed Grafana SKU.
    Options: "Standard" (default and recommended)
  EOT
  default     = "Standard"
}

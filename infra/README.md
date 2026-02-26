# Infrastructure as Code using Terraform

## Overview

This Terraform configuration deploys a complete Azure infrastructure for Microsoft Agent Framework observability demonstrations.

## Prerequisites

- Terraform >= 1.5.0
- Azure CLI with active subscription
- Appropriate Azure permissions to create resources

## Quick Start

1. **Copy the example variables file:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. **Edit terraform.tfvars with your values:**
   - Update `subscription_id` with your Azure subscription ID
   - Adjust other variables as needed (location, resource names, etc.)

3. **Initialize Terraform:**
   ```bash
   terraform init
   ```

4. **Review the deployment plan:**
   ```bash
   terraform plan
   ```

5. **Deploy the infrastructure:**
   ```bash
   terraform apply
   ```

6. **View outputs:**
   ```bash
   terraform output
   ```

## Configuration

All configurable parameters are defined in `variables.tf` with comprehensive descriptions. Key variables include:

- `subscription_id` - **(Required)** Your Azure subscription ID
- `location` - Azure region (default: "eastus")
- `project_name` - Prefix for resource naming (default: "mafobs")
- `environment` - Environment designation (default: "dev")
- `aks_node_count` - AKS node pool size (default: 3)
- `ai_model_capacity` - Model deployment capacity (default: 100)

See `variables.tf` for complete documentation of all available parameters.

## Outputs

Run `terraform output` to see all available outputs including URLs, credentials, and connection strings.

## File Organization

- `providers.tf` - Provider configuration (azapi, random)
- `variables.tf` - Input variable definitions
- `resource_group.tf` - Resource group creation
- `networking.tf` - VNET, subnets, and NAT gateway
- `aks.tf` - Azure Kubernetes Service cluster
- `acr.tf` - Azure Container Registry
- `monitoring.tf` - Application Insights, Prometheus, Grafana
- `ai_services.tf` - Azure AI Foundry and model deployment
- `outputs.tf` - Output values
- `terraform.tfvars.example` - Example variable values

## Cleanup

To destroy all created resources:

```bash
terraform destroy
```

## Notes

- All resources use the **azapi** provider for latest Azure API support
- OIDC and workload identity are enabled for secure pod-to-Azure authentication
- NAT gateway provides consistent outbound IP for AKS egress traffic
- Prometheus data collection is automatically configured for AKS metrics
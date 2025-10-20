# Common Errors and Solutions

This document tracks commonly encountered errors during development and their solutions.

## Terraform Errors

### Error: Call to unknown function "uuidv4()"

**Error Message:**
```
Error: Call to unknown function

  on rbac.tf line 11, in resource "azapi_resource" "cognitive_services_user_role_assignment":
  11:   name      = uuidv4()

There is no function named "uuidv4". Did you mean "uuidv5"?
```

**Root Cause:**
Terraform does not have a built-in `uuidv4()` function. This is a common mistake when trying to generate UUIDs for Azure role assignments.

**Solution:**
Use the `random_uuid` resource instead:

```terraform
# Generate UUID resource
resource "random_uuid" "role_assignment_id" {}

# Use the UUID in role assignment
resource "azapi_resource" "role_assignment" {
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = random_uuid.role_assignment_id.result
  parent_id = azapi_resource.target_resource.id
  # ... rest of configuration
}
```

**Prevention:**
- Always use Terraform's resource-based approach for generating dynamic values
- Common UUID resources: `random_uuid`, `random_id`, `random_string`
- Check Terraform documentation for available functions before using them

**Related Files:**
- `infra/rbac.tf` - Contains role assignment configurations
- `infra/providers.tf` - Must include `random` provider

**Date Added:** October 20, 2025

---

### Error: Invalid index when accessing azapi managed identity properties

**Error Message:**
```
Error: Invalid index

  on rbac.tf line 23, in resource "azapi_resource" "cognitive_services_user_role_assignment":
  23:       principalId      = azapi_resource.user_assigned_identity.identity[0].principal_id
    ├────────────────
    │ azapi_resource.user_assigned_identity.identity is empty list of object

The given key does not identify an element in this collection value: the collection has no elements.
```

**Root Cause:**
When using azapi provider, managed identity resources don't expose an `identity` attribute like azurerm resources do. The azapi resources expose their properties through the `output.properties` structure.

**Incorrect Approach:**
```terraform
# ❌ WRONG - This is azurerm syntax, not azapi
resource "azapi_resource" "role_assignment" {
  body = {
    properties = {
      principalId = azapi_resource.user_assigned_identity.identity[0].principal_id  # ❌ Wrong
    }
  }
}
```

**Correct Approach:**
```terraform
# ✅ Correct azapi syntax
resource "azapi_resource" "role_assignment" {
  body = {
    properties = {
      principalId = azapi_resource.user_assigned_identity.output.properties.principalId  # ✅ Correct
    }
  }
}
```

**Key Differences:**
- **azurerm**: Uses `resource.identity[0].principal_id`
- **azapi**: Uses `resource.output.properties.principalId`

**Common azapi Property Patterns:**
```terraform
# Managed Identity
principalId = azapi_resource.identity.output.properties.principalId
clientId    = azapi_resource.identity.output.properties.clientId

# Storage Account
primaryKey = azapi_resource.storage.output.properties.primaryEndpoints.blob

# Key Vault
vaultUri = azapi_resource.keyvault.output.properties.vaultUri
```

**Prevention:**
- Always use `output.properties.{propertyName}` for azapi resource properties
- Check Azure REST API documentation for correct property names
- Test with `terraform plan` to verify property access
- Never assume azurerm attribute patterns work with azapi

**Related Files:**
- `infra/rbac.tf` - Role assignments using managed identity principal ID
- `infra/outputs.tf` - Output values from azapi resources

**Date Added:** October 20, 2025

---

### Error: Adding azurerm Provider When Only azapi Should Be Used

**Error Context:**
When encountering authentication or data source issues, there might be a temptation to add the azurerm provider alongside azapi.

**Incorrect Approach:**
```terraform
terraform {
  required_providers {
    azapi = {
      source  = "azure/azapi"
      version = "~> 2.0"
    }
    azurerm = {  # ❌ WRONG - Do not add this
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {  # ❌ WRONG - Do not add this
  features {}
  subscription_id = var.subscription_id
}
```

**Root Cause:**
This project is designed to use **only azapi provider** for all Azure resource management. The azapi provider is the next-generation Azure provider that directly uses Azure REST APIs and supports all Azure resources without waiting for azurerm provider updates.

**Correct Approach:**
```terraform
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azapi = {
      source  = "azure/azapi"
      version = "~> 2.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    # ✅ No azurerm provider - only azapi
  }
}

provider "azapi" {
  subscription_id = var.subscription_id
}

provider "random" {}
```

**Solutions for Common azurerm Dependencies:**

1. **Data Sources**: Use azapi data sources instead
   ```terraform
   # ❌ Don't use azurerm data sources
   data "azurerm_client_config" "current" {}

   # ✅ Use azapi equivalent or alternative approach
   # For current user info, use variables or outputs from other resources
   ```

2. **Role Assignments**: Use azapi resources
   ```terraform
   # ✅ Correct azapi approach
   resource "azapi_resource" "role_assignment" {
     type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
     name      = random_uuid.role_id.result
     parent_id = azapi_resource.target_resource.id
     body = {
       properties = {
         roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/${var.role_definition_id}"
         principalId      = var.principal_id
         principalType    = "ServicePrincipal"
       }
     }
   }
   ```

3. **Current User Context**: Use variables or alternative approaches
   ```terraform
   # Instead of data.azurerm_client_config.current.object_id
   # Use a variable for the current user's object ID
   variable "current_user_object_id" {
     type        = string
     description = "Object ID of the current user for RBAC assignments"
     default     = null  # Optional - skip user assignments if not provided
   }

   # Get the current user's object ID with Azure CLI:
   # az ad signed-in-user show --query id --output tsv
   ```

**Why azapi Only:**
- **Future-proof**: azapi gets new Azure features immediately
- **Consistency**: Single provider reduces complexity
- **Performance**: Direct REST API calls are often faster
- **Completeness**: azapi supports all Azure resources, including preview features

**Prevention:**
- Always check if an azapi equivalent exists before considering azurerm
- Use Azure CLI or Azure Portal to get required IDs instead of azurerm data sources
- Pass user/service principal IDs as variables rather than querying them
- Consult azapi documentation for resource syntax

**Related Files:**
- `infra/providers.tf` - Should only contain azapi and random providers
- `infra/*.tf` - All resources should use azapi_resource or azapi_data_source

**Date Added:** October 20, 2025
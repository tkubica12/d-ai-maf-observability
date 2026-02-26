# Common Errors and Solutions

## Terraform Errors

### Call to unknown function `uuidv4()`

**Error**: `There is no function named "uuidv4". Did you mean "uuidv5"?`
**Cause**: Terraform has no built-in `uuidv4()` function.
**Fix**: Use a `random_uuid` resource:
```terraform
resource "random_uuid" "role_assignment_id" {}

resource "azapi_resource" "role_assignment" {
  name = random_uuid.role_assignment_id.result
  # ...
}
```

---

### Invalid index on azapi managed identity

**Error**: `azapi_resource.user_assigned_identity.identity is empty list of object`
**Cause**: azapi resources don't expose `.identity[0].principal_id` — that's azurerm syntax.
**Fix**: Use `output.properties` instead:
```terraform
# ❌ Wrong
azapi_resource.user_assigned_identity.identity[0].principal_id

# ✅ Correct
azapi_resource.user_assigned_identity.output.properties.principalId
```

---

### Don't add the azurerm provider

**Error**: Adding `hashicorp/azurerm` to `required_providers`.
**Cause**: This project uses **azapi only** for all Azure resources.
**Fix**: Use `azapi_resource` / `azapi_data_source` for everything. For current user context, pass IDs as variables instead of using `data "azurerm_client_config"`.
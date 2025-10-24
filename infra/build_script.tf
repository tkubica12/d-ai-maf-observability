# Generate .env file for build script
resource "local_file" "build_script_env" {
  filename = "${path.root}/../scripts/.env"
  content = templatefile("${path.module}/templates/build_script.env.tpl", {
    resource_group_name = azapi_resource.rg.name
    acr_name           = azapi_resource.acr.name
    acr_login_server   = azapi_resource.acr.output.properties.loginServer
  })

  depends_on = [
    azapi_resource.rg,
    azapi_resource.acr
  ]
}


# MAF Demo Application
resource "helm_release" "maf_demo" {
  name      = "maf-demo"
  chart     = "../charts/maf_demo"
  namespace = "maf-demo"

  create_namespace = true

  values = [
    yamlencode({
      apiTool = {
        image = {
          repository = "${azapi_resource.acr.output.properties.loginServer}/api-tool"
          tag        = var.api_tool_image_tag
        }
      }
      mcpTool = {
        image = {
          repository = "${azapi_resource.acr.output.properties.loginServer}/mcp-tool"
          tag        = var.mcp_tool_image_tag
        }
      }
      ingress = {
        hosts = {
          api = {
            host = "api-tool.${var.base_domain}"
          }
          mcp = {
            host = "mcp-tool.${var.base_domain}"
          }
        }
        tls = [
          {
            secretName = "api-tool-tls"
            hosts      = ["api-tool.${var.base_domain}"]
          },
          {
            secretName = "mcp-tool-tls"
            hosts      = ["mcp-tool.${var.base_domain}"]
          }
        ]
      }
      letsencrypt = {
        email = var.letsencrypt_email
      }
    })
  ]

  depends_on = [
    helm_release.nginx_ingress,
    helm_release.cert_manager,
    azapi_resource.acr
  ]
}

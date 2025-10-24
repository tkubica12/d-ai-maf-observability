# NGINX Ingress Controller
resource "helm_release" "nginx_ingress" {
  name       = "nginx-ingress"
  repository = "https://kubernetes.github.io/ingress-nginx"
  chart      = "ingress-nginx"
  namespace  = "ingress-nginx"
  version    = "4.11.3"

  create_namespace = true

  values = [
    yamlencode({
      controller = {
        service = {
          type = "LoadBalancer"
          annotations = {
            "service.beta.kubernetes.io/azure-load-balancer-resource-group"            = azapi_resource.rg.name
            "service.beta.kubernetes.io/azure-pip-name"                                = azapi_resource.ingress_public_ip.name
            "service.beta.kubernetes.io/azure-load-balancer-health-probe-request-path" = "/healthz"
          }
        }
        replicaCount = 2
        resources = {
          requests = {
            cpu    = "100m"
            memory = "128Mi"
          }
          limits = {
            cpu    = "200m"
            memory = "256Mi"
          }
        }
      }
    })
  ]

  depends_on = [
    azapi_resource.aks,
    azapi_resource.ingress_public_ip
  ]
}

# cert-manager
resource "helm_release" "cert_manager" {
  name       = "cert-manager"
  repository = "https://charts.jetstack.io"
  chart      = "cert-manager"
  namespace  = "cert-manager"
  version    = "v1.16.1"

  create_namespace = true

  values = [
    yamlencode({
      crds = {
        enabled = true
      }
      global = {
        leaderElection = {
          namespace = "cert-manager"
        }
      }
    })
  ]

  depends_on = [
    azapi_resource.aks
  ]
}


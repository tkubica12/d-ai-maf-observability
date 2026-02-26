resource "grafana_folder" "ai_agent_observability" {
  count = var.grafana_auth_token != "" ? 1 : 0
  title = "AI Agent Observability"
}

resource "grafana_dashboard" "prometheus_agent_metrics" {
  count       = var.grafana_auth_token != "" ? 1 : 0
  folder      = grafana_folder.ai_agent_observability[0].id
  config_json = file("${path.module}/../dashboards/prometheus-agent-metrics.json")
  overwrite   = true
}

resource "grafana_dashboard" "appinsights_agent_traces" {
  count       = var.grafana_auth_token != "" ? 1 : 0
  folder      = grafana_folder.ai_agent_observability[0].id
  config_json = file("${path.module}/../dashboards/appinsights-agent-traces.json")
  overwrite   = true
}

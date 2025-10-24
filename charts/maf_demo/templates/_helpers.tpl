{{/*
Expand the name of the chart.
*/}}
{{- define "maf-demo.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "maf-demo.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "maf-demo.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "maf-demo.labels" -}}
helm.sh/chart: {{ include "maf-demo.chart" . }}
{{ include "maf-demo.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "maf-demo.selectorLabels" -}}
app.kubernetes.io/name: {{ include "maf-demo.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
API Tool labels
*/}}
{{- define "maf-demo.apiToolSelectorLabels" -}}
{{ include "maf-demo.selectorLabels" . }}
app.kubernetes.io/component: api-tool
{{- end }}

{{/*
MCP Tool labels
*/}}
{{- define "maf-demo.mcpToolSelectorLabels" -}}
{{ include "maf-demo.selectorLabels" . }}
app.kubernetes.io/component: mcp-tool
{{- end }}

{{/*
OTEL Collector labels
*/}}
{{- define "maf-demo.otelCollectorSelectorLabels" -}}
{{ include "maf-demo.selectorLabels" . }}
app.kubernetes.io/component: otel-collector
{{- end }}

{{/*
Aspire Dashboard labels
*/}}
{{- define "maf-demo.aspireDashboardSelectorLabels" -}}
{{ include "maf-demo.selectorLabels" . }}
app.kubernetes.io/component: aspire-dashboard
{{- end }}

{{/*
Agent labels
*/}}
{{- define "maf-demo.agentSelectorLabels" -}}
{{ include "maf-demo.selectorLabels" . }}
app.kubernetes.io/component: agent
{{- end }}
# MAF Observability Demo — Design Decisions

Design decisions and architectural rationale for the MAF observability demo.

## Scenario Matrix

| Scenario ID | Hosting | Agents | Description |
|-------------|---------|--------|-------------|
| `local-maf` | Local | Single | MAF running locally, accessing tools via API and MCP from local runtime |
| `maf-with-fas` | Cloud | Single | MAF leveraging FAS, accessing tools via API and MCP from FAS in cloud |
| `local-maf-multiagent` | Local | Multi | MAF with Magentic orchestration of two local agents |
| `maf-with-fas-multiagent` | Cloud | Multi | MAF leveraging FAS with connected agents, both in FAS (cloud) |
| `local-maf-with-fas-multiagent` | Hybrid | Multi | MAF hosting one agent communicating with second agent running in FAS |
| `local-maf-multiagent-a2a` | Hybrid | Multi (via A2A) | MAF hosting one agent communicating with generic A2A agent running outside of MAF |
| `maf-with-fas-multiagent-a2a` | Cloud | Multi (via A2A) | MAF leveraging FAS for agents where one agent is generic A2A agent running outside of FAS/MAF |

## Architecture Decisions

**OTEL Collector as central hub** — All services emit OTLP to the collector rather than directly to backends. This decouples instrumentation from export destinations, lets us add/remove backends (Aspire, Langfuse, Azure Monitor) without touching application code, and keeps a single place to filter, sample, or enrich telemetry.

**Multi-backend observability (Aspire + Langfuse + Azure Monitor)** — Each backend serves a distinct purpose: Aspire Dashboard for real-time dev-loop trace/metric/log viewing, Langfuse for AI-specific evaluation and prompt analytics, Azure Monitor (App Insights + Prometheus + Grafana) for production-grade alerting and long-term retention. The collector fans out to all three simultaneously.

**Workload Identity (no API keys)** — Agent pods authenticate to Azure AI Services via AKS Workload Identity (federated credentials + OIDC). This eliminates secret rotation, reduces blast radius, and follows Azure RBAC best practices (Cognitive Services User / OpenAI User roles only).

**azapi-only Terraform (no azurerm)** — The `azapi` provider maps 1-to-1 with the Azure Resource Manager API surface. It supports day-zero resources (e.g., AI Foundry v2) without waiting for upstream provider releases, gives deterministic JSON payloads, and avoids the behavioral quirks of the higher-level `azurerm` abstractions.

**Magentic pattern for multi-agent** — MAF's built-in Magentic orchestration (manager + worker agents) was chosen over custom routing because it provides adaptive task decomposition, iterative refinement, and automatic agent selection out of the box, while still emitting standard OTEL spans for each delegation step.

## Telemetry Strategy

- **Traces** — End-to-end request flows across agent → tool → backend boundaries; each scenario is tagged with `scenario_id` and `scenario_type` for filtering.
- **Metrics** — Latency distributions, success/error rates, and custom business counters; collected via OTEL SDK and scraped by Prometheus.
- **Logs** — Structured JSON logs correlated to trace context; routed through the collector alongside traces and metrics.
- **Baggage / Resource Attributes** — `user_id`, `is_vip`, `department`, and `thread_id` propagated as OTEL resource attributes and baggage so every signal carries user context without manual plumbing.

## Mock Users

Canonical mock user data used across all scenarios for realistic telemetry segmentation.

| User ID | VIP | Department |
|---------|-----|------------|
| user_001 | Yes | Engineering |
| user_002 | Yes | Marketing |
| user_003 | Yes | Engineering |
| user_004 | No | Marketing |
| user_005 | No | Engineering |
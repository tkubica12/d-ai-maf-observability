# Anonymized Observability

Two Aspire Dashboards run in parallel: one receives full telemetry, the other receives telemetry anonymized by the OTEL Collector's `transform/anonymize` processor which strips PII before export.

## Architecture

```
┌─────────────┐
│  Services   │──► OTLP ──► ┌──────────────────┐
└─────────────┘              │  OTEL Collector  │
                             └────────┬─────────┘
                          ┌───────────┴───────────┐
                          ▼                       ▼
                ┌────────────────┐     ┌─────────────────────┐
                │ Aspire Dashboard│     │ Aspire Dashboard    │
                │ (Original)     │     │ (Anonymized)        │
                └────────────────┘     └─────────────────────┘
```

## Anonymization Strategy

| Type | Fields | Action |
|------|--------|--------|
| Pseudonymize | `user.id`, `organization.department`, `session.id`, `thread.id` | SHA256 hash |
| Remove | `user.is_vip`, `user.roles`, `tool.arguments`, `tool.result`, `gen_ai.*.content` | Deleted |
| Redact | emails, phones, credit cards | Regex → `*_REDACTED` |

## OTEL Collector Config

The `transform/anonymize` processor uses OTTL:

```yaml
processors:
  transform/anonymize:
    error_mode: ignore
    trace_statements:
      - set(span.attributes["user.id"], SHA256(span.attributes["user.id"])) where span.attributes["user.id"] != nil
      - delete_key(span.attributes, "user.is_vip")
      - delete_key(span.attributes, "tool.arguments")
      - delete_key(span.attributes, "tool.result")
      - replace_all_patterns(span.attributes, "value",
          "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b", "EMAIL_REDACTED")
```

## Access URLs

- **Original**: `https://aspire.{base_domain}` — full telemetry, restricted access
- **Anonymized**: `https://aspire-anon.{base_domain}` — PII stripped, wider team access

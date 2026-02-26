# Anonymized Observability Dashboard

## Overview

This implementation provides a **privacy-preserving observability solution** by creating a second Aspire Dashboard that receives anonymized telemetry. The OpenTelemetry Collector processes all telemetry through a transform processor that strips PII, pseudonymizes identifiers, and removes sensitive content before routing to the anonymized dashboard.

## Architecture

```
┌─────────────┐
│   Agent     │
│  API Tool   │───► OTLP ──┐
│  MCP Tool   │            │
└─────────────┘            ▼
                    ┌──────────────────┐
                    │ OTEL Collector   │
                    └──────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
    ┌──────────────────┐      ┌──────────────────────┐
    │ Original Pipeline│      │ Anonymized Pipeline  │
    │  - batch         │      │  - transform/anonymize│
    │  - memory_limiter│      │  - batch              │
    └──────────────────┘      │  - memory_limiter     │
              │               └──────────────────────┘
              │                         │
              ▼                         ▼
    ┌──────────────────┐      ┌────────────────────────┐
    │ Aspire Dashboard │      │ Aspire Dashboard (Anon)│
    │ aspire.domain.com│      │ aspire-anon.domain.com │
    │ - Full telemetry │      │ - PII stripped         │
    │ - User IDs       │      │ - Pseudonymized IDs    │
    │ - Tool content   │      │ - No tool content      │
    └──────────────────┘      └────────────────────────┘
```

## Anonymization Strategy

### 1. **Pseudonymization (SHA256 Hashing)**
Maintains correlation while protecting identity:
- `user.id` → SHA256 hash
- `organization.department` → SHA256 hash  
- `session.id` → SHA256 hash
- `thread.id` → SHA256 hash

**Benefit**: Same user = same hash across all traces, enabling correlation without revealing identity.

### 2. **Complete Removal**
Sensitive attributes deleted entirely:
- `user.is_vip` - Boolean flag considered PII
- `user.roles` - Role information
- `tool.arguments` - May contain sensitive input
- `tool.result` - May contain sensitive output
- `gen_ai.*.content` - LLM prompts and completions
- `user_message` (logs) - User queries
- `response` (logs) - Agent responses

### 3. **Pattern-Based Redaction**
Regex patterns detect and redact common PII:
- Email addresses → `EMAIL_REDACTED`
- Phone numbers → `PHONE_REDACTED`
- Credit card numbers → `CARD_REDACTED`

## Implementation Details

### OTEL Collector Configuration

The `transform/anonymize` processor uses OTTL (OpenTelemetry Transformation Language):

```yaml
processors:
  transform/anonymize:
    error_mode: ignore
    trace_statements:
      # Pseudonymize user identifiers
      - set(span.attributes["user.id"], SHA256(span.attributes["user.id"])) where span.attributes["user.id"] != nil
      
      # Remove sensitive flags
      - delete_key(span.attributes, "user.is_vip")
      
      # Strip tool content
      - delete_key(span.attributes, "tool.arguments")
      - delete_key(span.attributes, "tool.result")
      
      # Redact PII patterns
      - replace_all_patterns(span.attributes, "value", "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b", "EMAIL_REDACTED")
```

### Separate Pipelines

Two parallel pipelines process the same telemetry:

1. **Original Pipeline**: Full visibility for authorized users
   - `traces` → `otlp` → Aspire Dashboard
   - `logs` → `otlp` → Aspire Dashboard
   - `metrics` → `otlp` → Aspire Dashboard

2. **Anonymized Pipeline**: Privacy-preserving for wider access
   - `traces/anonymized` → `transform/anonymize` → `otlp/anonymized` → Aspire Dashboard (Anon)
   - `logs/anonymized` → `transform/anonymize` → `otlp/anonymized` → Aspire Dashboard (Anon)
   - `metrics/anonymized` → `transform/anonymize` → `otlp/anonymized` → Aspire Dashboard (Anon)

## Access URLs

After deployment via Terraform/Helm:

- **Original Dashboard**: `https://aspire.{base_domain}`
  - Full telemetry with PII
  - Restricted access recommended

- **Anonymized Dashboard**: `https://aspire-anon.{base_domain}`
  - PII stripped/pseudonymized
  - Safe for wider team access

## Configuration

### Enabling/Disabling

Control the anonymized dashboard via `values.yaml`:

```yaml
aspireDashboardAnon:
  enabled: true  # Set to false to disable
  tag: "9.0"
  resources:
    requests:
      memory: "256Mi"
      cpu: "200m"
```

### Terraform Variables

The Terraform configuration automatically sets up:
- Ingress host: `aspire-anon.{base_domain}`
- TLS certificate via Let's Encrypt
- Service endpoints

## Performance Impact

**Moderate overhead** (~15-30% increase in processing time):
- Telemetry is processed **twice** (original + anonymized pipelines)
- SHA256 hashing adds computational cost
- Regex pattern matching for PII detection

**Mitigation strategies**:
- Batch processor groups telemetry before transformation
- Memory limiter prevents resource exhaustion
- Transform processor is optimized (Beta stability)

## Security Considerations

### ✅ What This Protects

- User identity exposure
- VIP/role information leakage
- Sensitive tool input/output content
- LLM prompt/completion disclosure
- Common PII patterns (email, phone, credit cards)

### ⚠️ Limitations

1. **SHA256 is deterministic**: Same input always produces same hash
   - Enables correlation but vulnerable to rainbow table attacks
   - Not cryptographically secure pseudonymization (GDPR Article 4(5))

2. **Cannot detect all PII**: Regex patterns miss uncommon formats
   - Consider Azure AI Language PII service for advanced detection

3. **Nested JSON limitations**: Complex nested structures may contain undetected PII

4. **No format-preserving encryption**: Hashes don't look like original data

## GDPR Compliance Notes

This implementation provides **data minimization** (GDPR Article 5(1)(c)) and supports **privacy by design** (Article 25), but:

- SHA256 pseudonymization may not meet strict GDPR pseudonymization requirements
- Consider using keyed hashing (HMAC) with a secret key for stronger protection
- Document this as a "Technical and Organizational Measure" (TOM)
- Maintain clear data processing documentation

## Testing

Verify anonymization is working:

1. **Check user.id is hashed**:
   ```bash
   # Original dashboard should show: user_001
   # Anonymized dashboard should show: a3d2f1... (SHA256 hash)
   ```

2. **Verify PII removal**:
   ```bash
   # user.is_vip should not appear in anonymized dashboard
   # tool.arguments and tool.result should be missing
   ```

3. **Test pattern redaction**:
   ```bash
   # If email "user@example.com" appears in span, should show "EMAIL_REDACTED"
   ```

## Troubleshooting

### Dashboard shows no data

Check OTEL Collector logs:
```bash
kubectl logs -n maf-demo deployment/maf-demo-otel-collector
```

Look for transform processor errors.

### Anonymization not working

1. Verify processor is configured:
   ```bash
   kubectl get configmap -n maf-demo maf-demo-otel-collector-config -o yaml
   ```

2. Check for OTTL syntax errors in logs

3. Confirm pipeline routing:
   ```yaml
   traces/anonymized:
     receivers: [otlp]
     processors: [memory_limiter, transform/anonymize, batch]
     exporters: [otlp/anonymized]
   ```

### Performance degradation

Monitor collector metrics:
```bash
kubectl top pods -n maf-demo | grep otel-collector
```

If memory/CPU usage is high:
- Increase collector resources
- Reduce batch size
- Consider disabling anonymized pipeline if not needed

## Future Enhancements

Potential improvements:

1. **HMAC-based pseudonymization**: Use secret key for stronger hashing
2. **Azure AI Language PII integration**: AI-powered PII detection
3. **Configurable anonymization rules**: User-defined patterns
4. **Sampling for anonymized pipeline**: Process only subset of data
5. **Format-preserving encryption**: Maintain data format while encrypting

## References

- [OpenTelemetry Transform Processor](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/transformprocessor)
- [OTTL Language Specification](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/pkg/ottl)
- [Azure Monitor PII Filtering](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-filter)
- [GDPR Pseudonymization Guidelines](https://gdpr.eu/recital-26-not-applicable-to-anonymous-data/)

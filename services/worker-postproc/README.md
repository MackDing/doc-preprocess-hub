# worker-postproc

PII redaction + chunking, applied after a parser produces markdown/JSON.

**Status:** scaffold. Presidio and LangChain integrations are stubs.

## Pipeline

```
parsed markdown/JSON
   │
   ▼
Presidio analyzer  ──►  per-scene whitelist filter  ──►  Presidio anonymizer
   │
   ▼
LangChain text splitter (table-aware)
   │
   ▼
chunks.json → MinIO
```

## Whitelist

The per-scene whitelist is the most important policy knob. Your compliance team owns it. See `app/tasks.py` for the schema.

Default entities: `CREDIT_CARD`, `US_SSN`, `PHONE_NUMBER`, `EMAIL_ADDRESS`, `IP_ADDRESS`. Chinese entities (`CN_MOBILE`, `CN_ID_CARD`) require custom recognizers, contributions welcome.

## What to implement

- `_redact_pii()` — wire up Presidio analyzer + anonymizer, apply whitelist
- `_chunk()` — wire up LangChain `MarkdownTextSplitter`, preserve table rows

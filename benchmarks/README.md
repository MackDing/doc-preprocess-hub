# Benchmarks

Evaluation harness for doc-preprocess-hub. Three suites:

1. **`parsing_eval.py`** — document parsing accuracy (field extraction, table structure)
2. **`pii_eval.py`** — PII redaction recall / precision / whitelist accuracy
3. **`sla_eval.py`** — end-to-end SLA under mixed load

These are placeholders. Real datasets and harness implementations are pending.

## Contributing a dataset

Open an issue with the `benchmark` label. Describe:
- Source and licensing (can you legally contribute this?)
- Document count and types
- Language(s)
- Ground-truth format
- How you'd like attribution

Anonymized, synthetic, or fully-public datasets are ideal. We do not accept data that could contain real personal information.

## Running

```bash
cd benchmarks
pip install -r requirements.txt    # once added
python parsing_eval.py --suite sample --engine mineru
python pii_eval.py    --suite synthetic
python sla_eval.py    --load mixed --duration 600
```

All three suites emit JSON reports to `./reports/`.

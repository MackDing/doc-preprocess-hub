# Operator console (placeholder)

This directory will hold the Ant Design Pro v6 scaffold for the operator console.

**Status:** not yet initialized. Run this when you're ready to bootstrap:

```bash
cd services/console
pnpm create umi@latest
# choose "Ant Design Pro" template
```

Then implement:
- Jobs list page (`/jobs`) with ProTable + Drawer detail
- DLQ management (`/dlq`) with replay / discard + two-step confirm
- SLA dashboard (`/sla`) via iframe to your Grafana
- Audit query (`/audit`) with CSV export

See [`ARCHITECTURE.md`](../../ARCHITECTURE.md) and the bank Console decisions in the project plan for the full spec.

## Design decisions (locked)

- **Framework**: Ant Design Pro v6
- **Density**: `compact`
- **Theme**: light default + dark toggle
- **Font**: HarmonyOS Sans / PingFang SC
- **i18n**: Chinese primary, English switch
- **Charts**: iframe Grafana (don't self-build)
- **Break-glass actions**: two-step confirmation with last-4-digit jobId verification

## TODO

- [ ] Bootstrap Ant Design Pro scaffold
- [ ] Hook up orchestrator API client
- [ ] IAM / OIDC login flow
- [ ] Jobs list + Drawer detail
- [ ] DLQ page
- [ ] Audit query page with CSV export
- [ ] Dark mode toggle

# Contributing to doc-preprocess-hub

Thanks for considering a contribution. This document covers the things you'll want to know before opening a PR.

---

## Ground rules

1. **Be kind.** This is an open project. Code reviews critique the code, not the person.
2. **Small, focused PRs.** One change per PR. Easier to review, easier to revert.
3. **Tests required.** New code paths need tests. Bug fixes need regression tests.
4. **Don't break the API contract.** `orchestrator-api` is versioned under `/v1/`. Breaking changes go in `/v2/`.
5. **No secrets.** Never commit API keys, tokens, passwords, or customer data. Pre-commit hooks are in place; please run them locally.

---

## What we're looking for

### High-leverage contributions

- **Real engine integration** — the current `worker-mineru` and `worker-docling` services are stubs. Wiring them up to the real engines is the biggest unblocker.
- **Presidio recognizers** — especially non-English ones (Chinese, Japanese, Korean, Arabic, etc.). Each new language recognizer is a distinct PR.
- **Benchmark datasets** — anonymized parsing / PII / SLA evals. If your organization has a document set you can share, open an issue first to discuss data licensing.
- **Operator console features** — DLQ replay UX, audit query improvements, trace visualization.
- **Chart / formula understanding** — integrating DePlot or similar for chart-to-data extraction.

### Also welcome

- Docs improvements (typos, clarity, missing diagrams)
- Deployment guides for specific environments (k8s, nomad, docker swarm)
- Language SDKs beyond Python (Java, Go, TypeScript)
- Performance improvements with benchmarks showing the delta

### Please discuss before opening a PR

- Changes to the API contract (even additions)
- New top-level services
- Dependency upgrades that change major versions of Celery, FastAPI, SQLAlchemy, or AntD Pro
- Licensing changes

Open an issue with the `rfc` label and let's chat first.

---

## Development setup

```bash
# Clone and set up
git clone https://github.com/MackDing/doc-preprocess-hub.git
cd doc-preprocess-hub
cp .env.example .env

# Infrastructure services
docker compose up -d postgres redis rabbitmq minio

# Python services (use one terminal per service while developing)
cd services/orchestrator
pip install -e .
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Run tests
pytest
```

See `services/*/README.md` for service-specific dev notes.

---

## Code style

- **Python**: `ruff` + `black`, line length 100. Type hints where they add clarity.
- **TypeScript**: `eslint` + `prettier` defaults (from AntD Pro).
- **Commits**: present-tense imperative. "add PII whitelist config" not "added" or "adding".
- **No trailing whitespace.** Use `.editorconfig`.

---

## PR checklist

Before marking a PR ready for review:

- [ ] Tests pass locally (`pytest` for Python, `pnpm test` for console)
- [ ] New code has tests
- [ ] Changed behavior is documented (README / ARCHITECTURE / relevant docs)
- [ ] No new linter warnings
- [ ] No secrets committed
- [ ] PR description explains the **why**, not just the what
- [ ] Linked to an issue if one exists

---

## Reporting bugs

Open a GitHub issue. Include:

- What you did (ideally a minimal repro)
- What you expected
- What actually happened
- Environment (OS, Python version, engine versions)
- Logs, if relevant, redacted of any sensitive content

---

## Reporting security issues

**Do not open a public issue for security vulnerabilities.** Email the maintainer directly or use GitHub's private vulnerability reporting (Security tab → Report a vulnerability).

Give us a reasonable window to fix the issue before public disclosure. We'll credit you in the release notes if you want.

---

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0 (see [LICENSE](./LICENSE)).

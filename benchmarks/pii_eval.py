"""PII redaction eval.

PLACEHOLDER. Real implementation should:
  1. Load synthetic + anonymized corpus with ground-truth PII annotations.
  2. Run worker-postproc with each scene's whitelist.
  3. Compute recall (PII caught), precision (no false positives on body text),
     and whitelist accuracy (legitimate fields not redacted).
  4. Emit JSON report.

Thresholds (defaults, override via flags):
  recall       >= 0.99
  precision    >= 0.98
  whitelist_ok >= 0.99
"""

from __future__ import annotations

import sys


def main() -> int:
    print("pii_eval.py is a placeholder. See benchmarks/README.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

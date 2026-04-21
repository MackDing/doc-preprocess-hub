"""Parsing accuracy eval.

PLACEHOLDER. Real implementation should:
  1. Load a document corpus with ground-truth field annotations.
  2. Submit each document via the SDK.
  3. Compare extracted fields against ground truth.
  4. Emit JSON report: per-field accuracy, per-doc-type accuracy,
     confusion matrix for table structure, LaTeX correctness for formulas.

Exit codes:
  0: all thresholds met
  1: one or more thresholds missed (for CI gate)
"""

from __future__ import annotations

import sys


def main() -> int:
    print("parsing_eval.py is a placeholder. See benchmarks/README.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

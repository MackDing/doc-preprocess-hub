"""End-to-end SLA eval (load test).

PLACEHOLDER. Real implementation should submit a mixed load (scans / native
PDFs / Office) at target QPS via the SDK and measure:

  * throughput (docs/minute)
  * parse latency P50/P95/P99
  * failure rate by error_code
  * queue depth over time

Default target:
  1000 docs/day mixed, P95 < 5min, failure rate < 2%
"""

from __future__ import annotations

import sys


def main() -> int:
    print("sla_eval.py is a placeholder. See benchmarks/README.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

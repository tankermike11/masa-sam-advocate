"""
MASA SAM Eval Harness CLI.

Usage:
  python eval/run_eval.py
  python eval/run_eval.py --output eval/report.md
  python eval/run_eval.py --json eval/report.json
  python eval/run_eval.py --limit 20        # run first 20 fixtures only

Exits 0 if all key metrics meet targets; exits 1 if any miss.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

# Ensure repo root is in sys.path so backend + eval modules are importable
sys.path.insert(0, str(Path(__file__).parent.parent))

# Force UTF-8 stdout so non-ASCII report characters render on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from eval.golden_set import GOLDEN_FIXTURES, DATASET_PATH
from eval.harness import run_harness
from eval.report import generate_report, generate_json_report

_TARGETS = {
    "metric_triage_accuracy":    0.85,
    "metric_citation_validity":  1.00,
    "metric_concrete_next_step": 0.95,
    "metric_no_false_answer":    1.00,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="MASA SAM Eval Harness")
    parser.add_argument("--output", metavar="FILE", help="Save Markdown report to file")
    parser.add_argument("--json",   metavar="FILE", help="Save JSON report to file")
    parser.add_argument("--limit",  type=int,       help="Limit number of fixtures")
    args = parser.parse_args()

    if not GOLDEN_FIXTURES:
        print(
            f"ERROR: No fixtures loaded.\n"
            f"Check that the dataset exists at:\n  {DATASET_PATH}\n",
            file=sys.stderr,
        )
        sys.exit(1)

    fixtures = GOLDEN_FIXTURES[:args.limit] if args.limit else GOLDEN_FIXTURES
    print(f"Running eval harness on {len(fixtures)} fixtures...", flush=True)

    results = run_harness(fixtures)
    report = generate_report(results)

    print(report)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"\nMarkdown report saved to: {args.output}")

    if args.json:
        json_data = generate_json_report(results)
        Path(args.json).write_text(json.dumps(json_data, indent=2), encoding="utf-8")
        print(f"JSON report saved to: {args.json}")

    # Exit with non-zero if any key metric misses its target
    failed = [
        name for name, target in _TARGETS.items()
        if getattr(results, name) < target
    ]
    if failed:
        print(f"\nFAILED metrics: {', '.join(failed)}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()

"""Command-line entry point for gcdoctor experiment plan audit.

Usage::

    python -m gcdoctor.plan EXPERIMENT_ROOT [--output plan_report.md] [--strict]
    python -m gcdoctor.plan EXPERIMENT_ROOT --base BASE_CEDS --strict
"""

import argparse
from pathlib import Path
import sys

from utils.plan_utils import detect_experiment_plan
from utils.compare_utils import compare_run_directories
from utils.plan_report import write_plan_report


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gcdoctor-plan",
        description="Audit a GEOS-Chem experiment plan (BASE + multiple TEST directories).",
    )
    parser.add_argument(
        "experiment_root",
        help="Path to the experiment plan root directory containing BASE and TEST subdirectories.",
    )
    parser.add_argument(
        "--output",
        default="gcdoctor_plan_report.md",
        help="Path for the Markdown plan report (default: gcdoctor_plan_report.md).",
    )
    parser.add_argument(
        "--base",
        default=None,
        help="Explicit BASE directory name (relative to experiment_root). Auto-detected if omitted.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Treat WARN as an error for exit code purposes.",
    )
    return parser


def print_header() -> None:
    print("=" * 60)
    print("gcdoctor plan - GEOS-Chem Experiment Matrix Audit Tool")
    print("=" * 60)


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()

    experiment_root = Path(args.experiment_root).expanduser().resolve()

    print_header()

    # 1. Detect plan
    plan = detect_experiment_plan(experiment_root, base_name=args.base)

    for issue in plan["issues"]:
        print(f"[{issue['level']}] {issue['message']}")

    # Check for fatal detection issues
    has_error = any(i["level"] == "ERROR" for i in plan["issues"])
    has_warn = any(i["level"] == "WARN" for i in plan["issues"])

    base_dir = plan.get("base_dir")
    tests = plan.get("tests", [])

    if not base_dir or not tests:
        if not base_dir:
            print("[ERROR] No BASE directory found. Aborting plan audit.")
        if not tests:
            print("[ERROR] No TEST directories detected. Aborting plan audit.")
        sys.exit(1)

    # 2. Audit each TEST against BASE
    print(f"\nDetected BASE: {base_dir.name}")
    print(f"Detected TEST experiments: {len(tests)}")

    audit_results = []
    for t in tests:
        compare_results = compare_run_directories(base_dir, t["path"], intent=t["intent"])
        ok_count = sum(1 for r in compare_results if r["level"] == "OK")
        warn_count = sum(1 for r in compare_results if r["level"] == "WARN")
        error_count = sum(1 for r in compare_results if r["level"] == "ERROR")

        if error_count > 0:
            status = "ERROR"
            has_error = True
        elif warn_count > 0:
            status = "WARN"
            has_warn = True
        else:
            status = "OK"

        audit_results.append(
            {
                "name": t["name"],
                "intent": t["intent"],
                "path": t["path"],
                "status": status,
                "ok_count": ok_count,
                "warn_count": warn_count,
                "error_count": error_count,
                "results": compare_results,
            }
        )
        print(f"- {t['name']} [{t['intent']}]: {status}")

    # 3. Write report
    report_path = Path(args.output).resolve()
    write_plan_report(plan, audit_results, report_path, strict=args.strict)
    print(f"\n[OK] Plan report written: {report_path}")

    # 4. Exit code
    exit_code = 0
    if has_error:
        exit_code = 1
    elif args.strict and has_warn:
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

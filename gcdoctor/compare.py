"""Command-line entry point for gcdoctor compare tool.

Usage::

    python -m gcdoctor.compare BASE_DIR TEST_DIR [--output compare_report.md]
"""

import argparse
from pathlib import Path
import sys

from utils.compare_utils import compare_run_directories
from utils.compare_report import write_compare_report


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gcdoctor-compare",
        description="Compare two GEOS-Chem run directories (BASE vs TEST).",
    )
    parser.add_argument(
        "base_dir",
        help="Path to the BASE run directory.",
    )
    parser.add_argument(
        "test_dir",
        help="Path to the TEST run directory.",
    )
    parser.add_argument(
        "--output",
        default="gcdoctor_compare_report.md",
        help="Path for the Markdown compare report (default: gcdoctor_compare_report.md).",
    )
    return parser


def print_header() -> None:
    print("=" * 60)
    print("gcdoctor compare - GEOS-Chem Run Directory Comparison Tool")
    print("=" * 60)


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()

    base_dir = Path(args.base_dir).expanduser().resolve()
    test_dir = Path(args.test_dir).expanduser().resolve()

    print_header()

    results = compare_run_directories(base_dir, test_dir)

    has_error = False
    for result in results:
        level = result["level"]
        message = result["message"]
        print(f"[{level}] {message}")
        if level == "ERROR":
            has_error = True

    report_path = Path(args.output).resolve()
    write_compare_report(results, base_dir, test_dir, report_path)
    print(f"[OK] Compare report written: {report_path}")

    if has_error:
        sys.exit(1)


if __name__ == "__main__":
    main()

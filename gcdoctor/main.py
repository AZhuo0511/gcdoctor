"""Command-line entry point for gcdoctor."""

import argparse
from pathlib import Path
import sys

from checks.check_basic import check_basic_files
from checks.check_config import check_geoschem_config
from checks.check_hemco import check_hemco_config
from checks.check_logs import check_logs
from checks.check_restart import check_restart_files
from checks.check_run_dir import check_run_directory_safety
from utils.report import write_markdown_report


def _build_arg_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="gcdoctor",
        description="A lightweight diagnostic tool for GEOS-Chem run directories.",
    )
    parser.add_argument(
        "run_dir",
        help="Path to the GEOS-Chem run directory to diagnose.",
    )
    parser.add_argument(
        "--output",
        default="gcdoctor_report.md",
        help="Path for the Markdown report (default: gcdoctor_report.md).",
    )
    return parser


def print_header() -> None:
    """Print the gcdoctor command-line banner."""
    print("=" * 60)
    print("gcdoctor - GEOS-Chem Run Directory Diagnostic Tool")
    print("=" * 60)


def main() -> None:
    """Run gcdoctor from the command line."""
    parser = _build_arg_parser()
    args = parser.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()

    print_header()

    results = []
    results.extend(check_run_directory_safety(run_dir))
    results.extend(check_basic_files(run_dir))
    results.extend(check_geoschem_config(run_dir))
    results.extend(check_hemco_config(run_dir))
    results.extend(check_restart_files(run_dir))
    results.extend(check_logs(run_dir))

    has_error = False
    for result in results:
        level = result["level"]
        message = result["message"]
        print(f"[{level}] {message}")
        if level == "ERROR":
            has_error = True

    report_path = Path(args.output).resolve()
    write_markdown_report(results, run_dir, report_path)
    print(f"[OK] Markdown report written: {report_path}")

    if has_error:
        sys.exit(1)


if __name__ == "__main__":
    main()

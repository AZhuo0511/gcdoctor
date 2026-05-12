"""Command-line entry point for gcdoctor."""

from pathlib import Path
import sys

from checks.check_basic import check_basic_files
from checks.check_hemco import check_hemco_config
from checks.check_logs import check_logs
from checks.check_restart import check_restart_files


def print_header() -> None:
    """Print the gcdoctor command-line banner."""
    print("=" * 60)
    print("gcdoctor - GEOS-Chem Run Directory Diagnostic Tool")
    print("=" * 60)


def main() -> None:
    """Run gcdoctor from the command line."""
    if len(sys.argv) < 2:
        print("Usage: python -m gcdoctor.main /path/to/run_directory")
        sys.exit(1)

    run_dir = Path(sys.argv[1]).expanduser().resolve()

    print_header()

    results = []
    results.extend(check_basic_files(run_dir))
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

    if has_error:
        sys.exit(1)


if __name__ == "__main__":
    main()

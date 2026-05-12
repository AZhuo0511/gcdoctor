from pathlib import Path
import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m gcdoctor.main /path/to/run_directory")
        sys.exit(1)

    run_dir = Path(sys.argv[1])

    print("=" * 60)
    print("gcdoctor - GEOS-Chem Run Directory Diagnostic Tool")
    print("=" * 60)

    if not run_dir.exists():
        print(f"[ERROR] Run directory does not exist: {run_dir}")
        sys.exit(1)

    print(f"[OK] Run directory found: {run_dir}")


if __name__ == "__main__":
    main()
"""Log-file checks for gcdoctor.

This module scans GEOS-Chem run-directory log files for common runtime
errors and warning patterns. It is read-only and does not modify files.
"""

from pathlib import Path


LOG_FILE_PATTERNS = [
    "*.log",
    "*.out",
    "GC.log",
    "geoschem.log",
    "slurm-*.out",
]


ERROR_PATTERNS = [
    "HEMCO ERROR",
    "ERROR",
    "Cannot find field",
    "Cannot get pointer",
    "file not found",
    "No such file or directory",
    "netCDF",
    "NetCDF",
    "Segmentation fault",
    "Floating point exception",
    "MAPL ERROR",
    "GEOS-Chem ERROR",
]


def _find_log_files(run_dir: Path) -> list[Path]:
    """Find likely GEOS-Chem log files in a run directory."""
    log_files: list[Path] = []

    for pattern in LOG_FILE_PATTERNS:
        log_files.extend(run_dir.glob(pattern))

    unique_files = sorted(set(path for path in log_files if path.is_file()))
    return unique_files


def _scan_one_log_file(log_path: Path, max_matches: int = 30) -> list[dict]:
    """Scan one log file and return matched error records."""
    matches: list[dict] = []

    try:
        lines = log_path.read_text(errors="ignore").splitlines()
    except OSError as exc:
        return [
            {
                "level": "WARN",
                "item": "log file",
                "message": f"Could not read log file {log_path.name}: {exc}",
            }
        ]

    for line_number, line in enumerate(lines, start=1):
        for pattern in ERROR_PATTERNS:
            if pattern in line:
                matches.append(
                    {
                        "level": "ERROR",
                        "item": "log error",
                        "message": f"{log_path.name}:{line_number}: {line.strip()}",
                    }
                )
                break

        if len(matches) >= max_matches:
            matches.append(
                {
                    "level": "WARN",
                    "item": "log scan",
                    "message": f"Stopped scanning {log_path.name} after {max_matches} matched lines.",
                }
            )
            break

    return matches


def check_logs(run_dir: Path) -> list[dict]:
    """Scan GEOS-Chem log files for common error patterns."""
    results: list[dict] = []

    if not run_dir.exists() or not run_dir.is_dir():
        results.append(
            {
                "level": "ERROR",
                "item": "log scan",
                "message": f"Cannot scan logs because run directory is invalid: {run_dir}",
            }
        )
        return results

    log_files = _find_log_files(run_dir)
    if not log_files:
        results.append(
            {
                "level": "WARN",
                "item": "log scan",
                "message": "No log files found with patterns: *.log, *.out, GC.log, geoschem.log, slurm-*.out.",
            }
        )
        return results

    results.append(
        {
            "level": "OK",
            "item": "log scan",
            "message": f"Found {len(log_files)} candidate log file(s).",
        }
    )

    total_matches = 0
    for log_file in log_files:
        matches = _scan_one_log_file(log_file)
        total_matches += sum(1 for item in matches if item["level"] == "ERROR")
        results.extend(matches)

    if total_matches == 0:
        results.append(
            {
                "level": "OK",
                "item": "log scan",
                "message": "No known GEOS-Chem / HEMCO error patterns found in log files.",
            }
        )

    return results
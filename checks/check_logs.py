"""Log-file checks for gcdoctor.

This module scans GEOS-Chem run-directory log files for common runtime
errors and warning patterns. It is read-only and does not modify files.
"""

from pathlib import Path
import re

from utils.log_patterns import diagnose_log_line


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

BC_MISSING_FIELD_PATTERN = re.compile(r"Cannot find field\s+BC_([A-Za-z0-9_]+)")


def _find_log_files(run_dir: Path) -> list[Path]:
    """Find likely GEOS-Chem log files in a run directory."""
    log_files: list[Path] = []

    for pattern in LOG_FILE_PATTERNS:
        log_files.extend(run_dir.glob(pattern))

    unique_files = sorted(set(path for path in log_files if path.is_file()))
    return unique_files


def _extract_missing_bc_species(line: str) -> str | None:
    """Extract missing BoundaryConditions species from a log line.

    Example
    -------
    ``HEMCO ERROR: Cannot find field BC_ACR`` becomes ``ACR``.
    """
    match = BC_MISSING_FIELD_PATTERN.search(line)
    if match:
        return match.group(1)
    return None


def _scan_one_log_file(log_path: Path, max_matches: int = 30) -> list[dict]:
    """Scan one log file and return matched error records."""
    matches: list[dict] = []
    missing_bc_species: set[str] = set()
    seen_diagnosis_messages: set[str] = set()

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
        species = _extract_missing_bc_species(line)
        if species:
            missing_bc_species.add(species)

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

        # Structured log pattern diagnostics
        for diag in diagnose_log_line(line):
            if diag["message"] not in seen_diagnosis_messages:
                matches.append(diag)
                seen_diagnosis_messages.add(diag["message"])

        if len(matches) >= max_matches:
            matches.append(
                {
                    "level": "WARN",
                    "item": "log scan",
                    "message": f"Stopped scanning {log_path.name} after {max_matches} matched lines.",
                }
            )
            break

    if missing_bc_species:
        species_list = ", ".join(sorted(missing_bc_species))
        matches.append(
            {
                "level": "ERROR",
                "item": "BoundaryConditions species compatibility",
                "message": f"Missing BoundaryConditions species detected in {log_path.name}: {species_list}",
            }
        )
        matches.append(
            {
                "level": "WARN",
                "item": "BoundaryConditions species compatibility",
                "message": "Possible cause: BoundaryConditions files may not match the current GEOS-Chem chemical mechanism. For nested fullchem runs, avoid using old SAMPLE_BCs blindly; generate BC files from a matching global fullchem simulation.",
            }
        )

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
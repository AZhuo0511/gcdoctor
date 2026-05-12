"""Restart-file checks for gcdoctor.

This module performs read-only checks for GEOS-Chem restart files in a
run directory. It does not validate chemical species yet; it only checks
whether restart-related files are present and whether their names look
plausible for GEOS-Chem.
"""

from pathlib import Path


RESTART_PATTERNS = [
    "GEOSChem.Restart*.nc",
    "GEOSChem.Restart*.nc4",
    "GEOSChem.Restart.*.nc",
    "GEOSChem.Restart.*.nc4",
]

HEMCO_RESTART_PATTERNS = [
    "HEMCO_restart*.nc",
    "HEMCO_restart*.nc4",
]


def _find_files(run_dir: Path, patterns: list[str]) -> list[Path]:
    """Find files matching one or more glob patterns in a run directory."""
    files: list[Path] = []
    for pattern in patterns:
        files.extend(run_dir.glob(pattern))
    return sorted(set(path for path in files if path.is_file()))


def _format_file_list(files: list[Path], max_files: int = 5) -> str:
    """Format a compact file list for diagnostic messages."""
    names = [path.name for path in files[:max_files]]
    if len(files) > max_files:
        names.append(f"... and {len(files) - max_files} more")
    return ", ".join(names)


def check_restart_files(run_dir: Path) -> list[dict]:
    """Check whether GEOS-Chem and HEMCO restart files are present."""
    results: list[dict] = []

    if not run_dir.exists() or not run_dir.is_dir():
        results.append(
            {
                "level": "ERROR",
                "item": "restart scan",
                "message": f"Cannot scan restart files because run directory is invalid: {run_dir}",
            }
        )
        return results

    geoschem_restart_files = _find_files(run_dir, RESTART_PATTERNS)
    hemco_restart_files = _find_files(run_dir, HEMCO_RESTART_PATTERNS)

    if geoschem_restart_files:
        results.append(
            {
                "level": "OK",
                "item": "GEOS-Chem restart",
                "message": f"Found {len(geoschem_restart_files)} GEOS-Chem restart file(s): {_format_file_list(geoschem_restart_files)}",
            }
        )
    else:
        results.append(
            {
                "level": "WARN",
                "item": "GEOS-Chem restart",
                "message": "No GEOS-Chem restart file found in the run directory. Expected names like GEOSChem.Restart*.nc4.",
            }
        )

    if hemco_restart_files:
        results.append(
            {
                "level": "OK",
                "item": "HEMCO restart",
                "message": f"Found {len(hemco_restart_files)} HEMCO restart file(s): {_format_file_list(hemco_restart_files)}",
            }
        )
    else:
        results.append(
            {
                "level": "WARN",
                "item": "HEMCO restart",
                "message": "No HEMCO restart file found in the run directory. This may be acceptable for a fresh run, but should be checked for continuation runs.",
            }
        )

    return results

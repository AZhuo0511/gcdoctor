"""Basic run-directory checks for gcdoctor.

This module only performs read-only checks. It does not modify any
GEOS-Chem run-directory files.
"""

from pathlib import Path


REQUIRED_FILES = [
    "geoschem_config.yml",
    "HEMCO_Config.rc",
    "HISTORY.rc",
]


def check_basic_files(run_dir: Path) -> list[dict]:
    """Check whether the core GEOS-Chem run-directory files exist."""
    results: list[dict] = []

    if not run_dir.exists():
        results.append(
            {
                "level": "ERROR",
                "item": "run_dir",
                "message": f"Run directory does not exist: {run_dir}",
            }
        )
        return results

    if not run_dir.is_dir():
        results.append(
            {
                "level": "ERROR",
                "item": "run_dir",
                "message": f"Path exists but is not a directory: {run_dir}",
            }
        )
        return results

    results.append(
        {
            "level": "OK",
            "item": "run_dir",
            "message": f"Run directory found: {run_dir}",
        }
    )

    for filename in REQUIRED_FILES:
        file_path = run_dir / filename
        if file_path.exists():
            results.append(
                {
                    "level": "OK",
                    "item": filename,
                    "message": f"Required file found: {filename}",
                }
            )
        else:
            results.append(
                {
                    "level": "ERROR",
                    "item": filename,
                    "message": f"Required file missing: {filename}",
                }
            )

    return results

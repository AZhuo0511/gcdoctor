"""Entry-level run directory safety checks for gcdoctor."""

from pathlib import Path


_GEOSCHEM_SIGNATURE_FILES = [
    "geoschem_config.yml",
    "HEMCO_Config.rc",
    "HISTORY.rc",
]

_GEOSCHEM_PATH_HINTS = [
    "rundirs",
    "GEOS-Chem",
    "gc_",
    "fullchem",
]


def check_run_directory_safety(run_dir: Path) -> list[dict]:
    """Check whether *run_dir* exists and looks like a GEOS-Chem run directory."""
    results: list[dict] = []

    # ---- existence / type ----
    if not run_dir.exists():
        results.append(
            {
                "level": "ERROR",
                "item": "run directory",
                "message": "Run directory does not exist.",
            }
        )
    elif not run_dir.is_dir():
        results.append(
            {
                "level": "ERROR",
                "item": "run directory",
                "message": "Run directory path is not a directory.",
            }
        )
    else:
        results.append(
            {
                "level": "OK",
                "item": "run directory",
                "message": "Run directory exists.",
            }
        )

    # ---- signature files (only when the directory exists) ----
    if run_dir.is_dir():
        found = sum(
            1 for f in _GEOSCHEM_SIGNATURE_FILES if (run_dir / f).is_file()
        )
        if found >= 2:
            results.append(
                {
                    "level": "OK",
                    "item": "run directory",
                    "message": "Run directory looks like a GEOS-Chem run directory.",
                }
            )
        elif found == 1:
            results.append(
                {
                    "level": "WARN",
                    "item": "run directory",
                    "message": "Only one typical GEOS-Chem run directory file was found.",
                }
            )
        else:
            results.append(
                {
                    "level": "WARN",
                    "item": "run directory",
                    "message": "Run directory does not look like a typical GEOS-Chem run directory.",
                }
            )

    # ---- path hints ----
    path_str = str(run_dir)
    if any(hint.lower() in path_str.lower() for hint in _GEOSCHEM_PATH_HINTS):
        results.append(
            {
                "level": "OK",
                "item": "run directory hint",
                "message": "Path contains GEOS-Chem-like run directory markers.",
            }
        )

    return results

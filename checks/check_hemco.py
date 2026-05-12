"""HEMCO_Config.rc checks for gcdoctor.

This module performs read-only checks on HEMCO_Config.rc.
"""

from pathlib import Path


TARGET_KEYWORDS = [
    "ROOT",
    "BoundaryConditions",
    "Restart",
    "Restarts",
    "SAMPLE_BCs",
]


def _strip_inline_comment(line: str) -> str:
    """Remove inline comments from a HEMCO_Config.rc line."""
    return line.split("#", 1)[0].strip()


def _extract_paths_from_line(line: str) -> list[str]:
    """Extract path-like tokens from one HEMCO_Config.rc line.

    The previous implementation matched any token beginning with ``/``.
    That incorrectly converted relative paths such as ``./test_data`` into
    ``/test_data``. Here we first split the line into tokens, then keep only
    tokens that explicitly look like paths.
    """
    paths: list[str] = []

    for token in line.split():
        cleaned_token = token.strip().rstrip(",;")
        if not cleaned_token:
            continue

        looks_like_path = (
            cleaned_token.startswith("/")
            or cleaned_token.startswith("./")
            or cleaned_token.startswith("../")
            or cleaned_token.startswith("$ROOT/")
            or cleaned_token.startswith("${ROOT}/")
        )

        if looks_like_path:
            paths.append(cleaned_token)

    return paths


def _find_root_value(lines: list[str]) -> str | None:
    """Find ROOT value in HEMCO_Config.rc if it is explicitly defined."""
    for line in lines:
        clean_line = _strip_inline_comment(line)
        if not clean_line:
            continue

        if clean_line.startswith("ROOT"):
            parts = clean_line.split(":", 1)
            if len(parts) == 2:
                return parts[1].strip()

            parts = clean_line.split()
            if len(parts) >= 2:
                return parts[-1].strip()

    return None


def check_hemco_config(run_dir: Path) -> list[dict]:
    """Check whether HEMCO_Config.rc exists and contains plausible paths."""
    results: list[dict] = []
    hemco_path = run_dir / "HEMCO_Config.rc"

    if not hemco_path.exists():
        results.append(
            {
                "level": "ERROR",
                "item": "HEMCO_Config.rc",
                "message": "Cannot check HEMCO paths because HEMCO_Config.rc is missing.",
            }
        )
        return results

    lines = hemco_path.read_text(errors="ignore").splitlines()
    root_value = _find_root_value(lines)

    if root_value:
        root_path = Path(root_value).expanduser()
        if root_path.exists():
            results.append(
                {
                    "level": "OK",
                    "item": "HEMCO ROOT",
                    "message": f"HEMCO ROOT exists: {root_value}",
                }
            )
        else:
            results.append(
                {
                    "level": "WARN",
                    "item": "HEMCO ROOT",
                    "message": f"HEMCO ROOT is defined but not found on this machine: {root_value}",
                }
            )
    else:
        results.append(
            {
                "level": "WARN",
                "item": "HEMCO ROOT",
                "message": "No explicit ROOT definition found in HEMCO_Config.rc.",
            }
        )

    matched_lines = []
    for line_number, line in enumerate(lines, start=1):
        clean_line = _strip_inline_comment(line)
        if not clean_line:
            continue

        if any(keyword in clean_line for keyword in TARGET_KEYWORDS):
            matched_lines.append((line_number, clean_line))

    if not matched_lines:
        results.append(
            {
                "level": "WARN",
                "item": "HEMCO paths",
                "message": "No ROOT / BoundaryConditions / Restart related lines were found.",
            }
        )
        return results

    for line_number, clean_line in matched_lines:
        if "SAMPLE_BCs" in clean_line:
            results.append(
                {
                    "level": "WARN",
                    "item": "BoundaryConditions",
                    "message": f"Line {line_number}: SAMPLE_BCs detected; verify that BC files match the GEOS-Chem mechanism version.",
                }
            )

        paths = _extract_paths_from_line(clean_line)
        for path_text in paths:
            expanded_path = path_text
            if root_value:
                expanded_path = expanded_path.replace("${ROOT}", root_value).replace("$ROOT", root_value)

            if "*" in expanded_path or "$" in expanded_path:
                results.append(
                    {
                        "level": "WARN",
                        "item": "HEMCO path",
                        "message": f"Line {line_number}: Path contains wildcard or unresolved variable, skipped existence check: {path_text}",
                    }
                )
                continue

            path_obj = Path(expanded_path).expanduser()
            if path_obj.exists():
                results.append(
                    {
                        "level": "OK",
                        "item": "HEMCO path",
                        "message": f"Line {line_number}: Path exists: {path_text}",
                    }
                )
            else:
                results.append(
                    {
                        "level": "WARN",
                        "item": "HEMCO path",
                        "message": f"Line {line_number}: Path not found on this machine: {path_text}",
                    }
                )

    return results

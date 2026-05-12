

"""geoschem_config.yml lightweight checks for gcdoctor.

This module extracts useful metadata from geoschem_config.yml without
requiring PyYAML. It is intentionally conservative: values are reported as
text snippets instead of fully validating YAML structure.
"""

from pathlib import Path


CONFIG_KEYS_OF_INTEREST = [
    "name",
    "simulation",
    "start_date",
    "end_date",
    "start_time",
    "end_time",
    "met_field",
    "meteorology",
    "grid",
    "resolution",
    "longitude",
    "latitude",
    "nested_grid_simulation",
    "is_nested",
    "region",
]


def _strip_comment(line: str) -> str:
    """Remove YAML comments from a single line."""
    return line.split("#", 1)[0].rstrip()


def _parse_simple_key_value(line: str) -> tuple[str, str] | None:
    """Parse a simple YAML key-value line.

    Only lines with the form ``key: value`` are parsed. Nested objects and
    lists are not expanded in this first version.
    """
    clean_line = _strip_comment(line).strip()
    if not clean_line or ":" not in clean_line:
        return None

    key, value = clean_line.split(":", 1)
    key = key.strip()
    value = value.strip().strip('"').strip("'")

    if not key:
        return None

    return key, value


def _looks_like_nested_config(lines: list[str]) -> bool:
    """Infer whether the config may describe a nested-grid run."""
    joined_text = "\n".join(lines).lower()
    nested_markers = [
        "nested",
        "buffer_zone",
        "parent_grid",
        "longitude: [",
        "latitude: [",
    ]
    return any(marker in joined_text for marker in nested_markers)


def _extract_config_metadata(lines: list[str]) -> dict[str, str]:
    """Extract selected metadata from geoschem_config.yml text."""
    metadata: dict[str, str] = {}

    for line in lines:
        parsed = _parse_simple_key_value(line)
        if not parsed:
            continue

        key, value = parsed
        normalized_key = key.lower().replace("-", "_")

        for target_key in CONFIG_KEYS_OF_INTEREST:
            if normalized_key == target_key or target_key in normalized_key:
                if value:
                    metadata.setdefault(normalized_key, value)
                break

    return metadata


def check_geoschem_config(run_dir: Path) -> list[dict]:
    """Check geoschem_config.yml and summarize important run metadata."""
    results: list[dict] = []
    config_path = run_dir / "geoschem_config.yml"

    if not config_path.exists():
        results.append(
            {
                "level": "ERROR",
                "item": "geoschem_config.yml",
                "message": "Cannot parse simulation metadata because geoschem_config.yml is missing.",
            }
        )
        return results

    try:
        lines = config_path.read_text(errors="ignore").splitlines()
    except OSError as exc:
        results.append(
            {
                "level": "ERROR",
                "item": "geoschem_config.yml",
                "message": f"Could not read geoschem_config.yml: {exc}",
            }
        )
        return results

    metadata = _extract_config_metadata(lines)
    if metadata:
        for key in sorted(metadata):
            results.append(
                {
                    "level": "OK",
                    "item": "geoschem_config.yml metadata",
                    "message": f"{key}: {metadata[key]}",
                }
            )
    else:
        results.append(
            {
                "level": "WARN",
                "item": "geoschem_config.yml metadata",
                "message": "No simple simulation metadata fields were extracted from geoschem_config.yml.",
            }
        )

    if _looks_like_nested_config(lines):
        results.append(
            {
                "level": "OK",
                "item": "geoschem_config.yml grid",
                "message": "Nested-grid related markers detected in geoschem_config.yml.",
            }
        )
    else:
        results.append(
            {
                "level": "WARN",
                "item": "geoschem_config.yml grid",
                "message": "No obvious nested-grid markers detected in geoschem_config.yml.",
            }
        )

    return results
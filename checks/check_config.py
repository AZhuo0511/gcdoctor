"""geoschem_config.yml lightweight checks for gcdoctor.

This module extracts metadata from geoschem_config.yml without requiring
PyYAML. It uses indentation context to build dotted-key paths (e.g.
``simulation.name``) and reports nested-grid related markers.
"""

from pathlib import Path


def _strip_comment(line: str) -> str:
    """Remove YAML comments from a single line."""
    return line.split("#", 1)[0].rstrip()


def _parse_indented_yaml(lines: list[str]) -> dict[str, str]:
    """Parse YAML using indentation context to build dotted-key paths.

    Only leaf key-value pairs are returned. Mapping keys (those without a
    value on the same line) contribute to the key prefix stack.
    """
    metadata: dict[str, str] = {}
    stack: list[tuple[int, str]] = []  # (indent_spaces, key)

    for line in lines:
        raw = line.rstrip("\n\r")
        clean = _strip_comment(raw)
        if not clean:
            continue

        # Skip list items
        if clean.lstrip().startswith("-"):
            continue

        if ":" not in clean:
            continue

        leading = len(raw) - len(raw.lstrip(" "))
        stripped = clean.strip()

        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if not key:
            continue

        # Pop keys at the same or deeper indentation
        while stack and stack[-1][0] >= leading:
            stack.pop()

        if value:
            full_key = ".".join([k for _, k in stack] + [key])
            metadata[full_key] = value
        else:
            stack.append((leading, key))

    return metadata


def _looks_like_nested_config(lines: list[str]) -> bool:
    """Infer whether the config may describe a nested-grid run."""
    joined_text = "\n".join(lines).lower()
    nested_markers = [
        "nested_grid_simulation: true",
        "nested_grid_simulation: yes",
        "is_nested: true",
        "is_nested: yes",
        "resolution: 0.5x0.625",
        "longitude: [",
        "latitude: [",
        "buffer_zone",
        "parent_grid",
        "nested",
    ]
    return any(marker in joined_text for marker in nested_markers)


def _extract_metadata_from_yaml_text(lines: list[str]) -> dict[str, str]:
    """Extract all leaf key-value pairs with dotted-key paths."""
    return _parse_indented_yaml(lines)


def get_config_metadata(lines: list[str]) -> dict[str, str]:
    """Public accessor: parse GEOS-Chem YAML config lines into dotted-key metadata."""
    return _parse_indented_yaml(lines)


def check_geoschem_config(run_dir: Path) -> list[dict]:
    """Check geoschem_config.yml and summarize run metadata."""
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

    metadata = _extract_metadata_from_yaml_text(lines)
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
                "message": "No simulation metadata fields were extracted from geoschem_config.yml.",
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

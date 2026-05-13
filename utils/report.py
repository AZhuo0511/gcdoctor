"""Markdown report writer for gcdoctor."""

from pathlib import Path
from collections import Counter

from utils.diagnosis import generate_diagnosis_summary


LEVEL_ORDER = ["ERROR", "WARN", "OK"]


def _group_results_by_level(results: list[dict]) -> dict[str, list[dict]]:
    """Group diagnostic records by level."""
    grouped: dict[str, list[dict]] = {level: [] for level in LEVEL_ORDER}

    for result in results:
        level = result.get("level", "UNKNOWN")
        grouped.setdefault(level, []).append(result)

    return grouped


def write_markdown_report(results: list[dict], run_dir: Path, output_path: Path) -> None:
    """Write gcdoctor diagnostic results to a Markdown report.

    Parameters
    ----------
    results:
        Diagnostic records collected by gcdoctor checks.
    run_dir:
        GEOS-Chem run directory that was diagnosed.
    output_path:
        Markdown report path to write.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    counts = Counter(result.get("level", "UNKNOWN") for result in results)
    grouped = _group_results_by_level(results)

    lines: list[str] = []
    lines.append("# gcdoctor report")
    lines.append("")
    lines.append("## Target run directory")
    lines.append("")
    lines.append(f"`{run_dir}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- ERROR: {counts.get('ERROR', 0)}")
    lines.append(f"- WARN: {counts.get('WARN', 0)}")
    lines.append(f"- OK: {counts.get('OK', 0)}")
    diagnosis_entries = generate_diagnosis_summary(results)
    lines.append("")
    lines.append("## Diagnosis summary")
    lines.append("")

    if diagnosis_entries:
        for entry in diagnosis_entries:
            level = entry.get("level", "UNKNOWN")
            message = entry.get("message", "")
            lines.append(f"- **{level}**: {message}")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Detailed results")
    lines.append("")

    for level in LEVEL_ORDER:
        items = grouped.get(level, [])
        lines.append(f"### {level}")
        lines.append("")

        if not items:
            lines.append("- None")
            lines.append("")
            continue

        for item in items:
            diagnostic_item = item.get("item", "unknown")
            message = item.get("message", "")
            lines.append(f"- **{diagnostic_item}**: {message}")

        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")

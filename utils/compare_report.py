"""Markdown compare report writer for gcdoctor compare tool."""

from pathlib import Path
from collections import Counter


def write_compare_report(
    results: list[dict],
    base_dir: Path,
    test_dir: Path,
    output_path: str | Path,
) -> None:
    """Write gcdoctor comparison results to a Markdown report.

    Parameters
    ----------
    results:
        Comparison diagnostic records.
    base_dir:
        BASE run directory path.
    test_dir:
        TEST run directory path.
    output_path:
        Markdown report path to write (``str`` or ``Path``).
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    counts = Counter(r.get("level", "UNKNOWN") for r in results)
    error_count = counts.get("ERROR", 0)
    warn_count = counts.get("WARN", 0)

    if error_count > 0:
        overall = "ERROR"
    elif warn_count > 0:
        overall = "WARN"
    else:
        overall = "OK"

    lines: list[str] = []
    lines.append("# gcdoctor compare report")
    lines.append("")

    lines.append("## Compared directories")
    lines.append("")
    lines.append(f"- BASE: `{base_dir}`")
    lines.append(f"- TEST: `{test_dir}`")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- OK: {counts.get('OK', 0)}")
    lines.append(f"- WARN: {counts.get('WARN', 0)}")
    lines.append(f"- ERROR: {error_count}")
    lines.append("")
    lines.append(f"Overall status: **{overall}**")
    lines.append("")

    # Experiment design assessment section
    _design_items = [
        r for r in results
        if r.get("item", "") in ("experiment design", "experiment design summary")
    ]
    lines.append("## Experiment design assessment")
    lines.append("")
    if _design_items:
        for item in _design_items:
            level = item.get("level", "UNKNOWN")
            message = item.get("message", "")
            lines.append(f"- **{level}**: {message}")
    else:
        lines.append("- No experiment design assessment items were generated.")
    lines.append("")

    # Detailed comparison results
    lines.append("## Detailed comparison results")
    lines.append("")

    for r in results:
        level = r.get("level", "UNKNOWN")
        item = r.get("item", "unknown")
        message = r.get("message", "")
        lines.append(f"- **{level}** `[{item}]`: {message}")

    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")

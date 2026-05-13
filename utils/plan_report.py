"""Experiment plan report writer for gcdoctor."""

from pathlib import Path
from collections import Counter


def write_plan_report(
    plan: dict,
    audit_results: list[dict],
    output_path: Path,
    strict: bool = False,
) -> None:
    """Write a gcdoctor experiment plan audit report.

    Parameters
    ----------
    plan:
        Plan detection result from :func:`detect_experiment_plan`.
    audit_results:
        Per-TEST audit records; each entry has ``name``, ``intent``,
        ``path``, ``status``, ``ok_count``, ``warn_count``,
        ``error_count``, and ``results`` (the raw compare output).
    output_path:
        Markdown report path to write.
    strict:
        Whether strict mode was enabled.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("# gcdoctor experiment plan report")
    lines.append("")

    # ---- Experiment root ----
    lines.append("## Experiment root")
    lines.append("")
    lines.append(f"- Root: `{plan['root']}`")
    base_dir = plan.get("base_dir")
    lines.append(f"- BASE: `{base_dir}`" if base_dir else "- BASE: *not found*")
    lines.append(f"- Strict mode: {strict}")
    lines.append("")

    # ---- Detected experiments ----
    lines.append("## Detected experiments")
    lines.append("")
    if base_dir:
        lines.append(f"- BASE: {base_dir.name}")
    for t in plan.get("tests", []):
        lines.append(f"- TEST: {t['name']}, intent={t['intent']}")
    lines.append("")

    # ---- Plan summary ----
    total_tests = len(audit_results)
    ok_exps = sum(1 for a in audit_results if a["status"] == "OK")
    warn_exps = sum(1 for a in audit_results if a["status"] == "WARN")
    error_exps = sum(1 for a in audit_results if a["status"] == "ERROR")

    issue_levels = Counter(i.get("level", "") for i in plan.get("issues", []))
    detection_errors = issue_levels.get("ERROR", 0)
    detection_warns = issue_levels.get("WARN", 0)

    _overall_errors = error_exps + detection_errors
    _overall_warns = warn_exps + detection_warns

    if _overall_errors > 0:
        overall = "ERROR"
    elif _overall_warns > 0:
        overall = "WARN"
    else:
        overall = "OK"

    lines.append("## Plan summary")
    lines.append("")
    lines.append(f"- Total TEST experiments: {total_tests}")
    lines.append(f"- OK experiments: {ok_exps}")
    lines.append(f"- WARN experiments: {warn_exps}")
    lines.append(f"- ERROR experiments: {error_exps}")
    lines.append(f"- Plan detection OK/WARN/ERROR: {issue_levels.get('OK', 0)} / {detection_warns} / {detection_errors}")
    lines.append(f"- Overall status: **{overall}**")
    lines.append("")

    # ---- Plan detection messages ----
    lines.append("## Plan detection messages")
    lines.append("")
    for issue in plan.get("issues", []):
        level = issue.get("level", "")
        message = issue.get("message", "")
        lines.append(f"- **{level}** `[plan detection]`: {message}")
    lines.append("")

    # ---- Experiment matrix assessment ----
    lines.append("## Experiment matrix assessment")
    lines.append("")
    for a in audit_results:
        lines.append(
            f"- **{a['status']}** `{a['name']}` intent={a['intent']}: "
            f"OK={a['ok_count']}, WARN={a['warn_count']}, ERROR={a['error_count']}"
        )
    lines.append("")

    # ---- Detailed audit results ----
    lines.append("## Detailed audit results")
    lines.append("")

    for a in audit_results:
        lines.append(f"### {a['name']}")
        lines.append("")
        lines.append(f"- Path: `{a['path']}`")
        lines.append(f"- Intent: {a['intent']}")
        lines.append(f"- Status: {a['status']}")
        lines.append("")

        for r in a.get("results", []):
            level = r.get("level", "")
            item = r.get("item", "")
            message = r.get("message", "")
            lines.append(f"- **{level}** `[{item}]`: {message}")

        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")

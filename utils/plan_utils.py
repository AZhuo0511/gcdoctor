"""Experiment plan detection utilities for gcdoctor."""

import re
from pathlib import Path
from typing import Optional


# Intent order for stable sorting
_INTENT_ORDER = [
    "meic-nox",
    "meic-co",
    "meic-so2",
    "meic-nh3",
    "meic-voc",
    "meic-all",
    "general",
]


def _intent_sort_key(intent: str) -> int:
    try:
        return _INTENT_ORDER.index(intent)
    except ValueError:
        return len(_INTENT_ORDER)


def infer_intent_from_name(name: str) -> str:
    """Infer an experiment intent from a directory name.

    Returns an intent string (``meic-nox``, ``meic-co``, …) or ``""``
    if no intent could be inferred.
    """
    name_lower = name.lower()

    if "meic" not in name_lower:
        return ""

    # Split into tokens by underscore, hyphen, or whitespace
    tokens = re.split(r"[_\-\s]+", name_lower)
    tokens = [t for t in tokens if t]

    species_token = tokens[-1] if tokens else ""

    if species_token in ("nox", "no_x"):
        return "meic-nox"
    if species_token == "co":
        return "meic-co"
    if species_token in ("so2", "so_2"):
        return "meic-so2"
    if species_token in ("nh3", "nh_3"):
        return "meic-nh3"
    if species_token == "voc":
        return "meic-voc"
    if species_token == "all":
        return "meic-all"

    # Fallback: check tokens more broadly
    for tok in tokens:
        if tok in ("nox", "no_x"):
            return "meic-nox"
        if tok == "co":
            return "meic-co"
        if tok in ("so2", "so_2"):
            return "meic-so2"
        if tok in ("nh3", "nh_3"):
            return "meic-nh3"
        if tok == "voc":
            return "meic-voc"
        if tok == "all":
            return "meic-all"

    # Contains "meic" but species unclear -> general
    return "general"


def detect_experiment_plan(
    experiment_root: Path,
    base_name: Optional[str] = None,
) -> dict:
    """Detect BASE and TEST directories within an experiment root.

    Parameters
    ----------
    experiment_root:
        Path to the experiment plan root directory.
    base_name:
        Optional explicit BASE directory name (relative to *experiment_root*).

    Returns
    -------
    dict
        With keys ``root``, ``base_dir``, ``tests``, ``issues``.
    """
    issues: list[dict] = []
    tests: list[dict] = []

    # ---- A. Experiment root check ----
    if not experiment_root.exists():
        issues.append(
            {"level": "ERROR", "item": "plan detection", "message": "Experiment root does not exist."}
        )
        return {"root": experiment_root, "base_dir": None, "tests": [], "issues": issues}

    if not experiment_root.is_dir():
        issues.append(
            {"level": "ERROR", "item": "plan detection", "message": "Experiment root is not a directory."}
        )
        return {"root": experiment_root, "base_dir": None, "tests": [], "issues": issues}

    issues.append(
        {"level": "OK", "item": "plan detection", "message": "Experiment root exists."}
    )

    # Collect direct subdirectories
    subdirs = sorted(
        [p for p in experiment_root.iterdir() if p.is_dir()],
        key=lambda p: p.name.lower(),
    )

    # ---- B. BASE detection ----
    base_dir: Optional[Path] = None

    if base_name:
        candidate = experiment_root / base_name
        if candidate.is_dir():
            base_dir = candidate
            issues.append(
                {"level": "OK", "item": "plan detection", "message": f"BASE directory selected by --base: {base_name}"}
            )
        else:
            issues.append(
                {"level": "ERROR", "item": "plan detection", "message": f"BASE directory specified by --base was not found: {base_name}"}
            )
    else:
        # Auto-detect BASE
        base_candidates: list[Path] = []

        for sd in subdirs:
            sd_name = sd.name
            if sd_name == "BASE":
                base_candidates.append(sd)
            elif "base" in sd_name.lower() or "ceds" in sd_name.lower():
                base_candidates.append(sd)

        # Prefer exact BASE_CEDS
        preferred = [p for p in base_candidates if "base_ceds" in p.name.lower()]
        if preferred:
            base_candidates = preferred

        if len(base_candidates) == 0:
            issues.append(
                {"level": "ERROR", "item": "plan detection", "message": "No BASE directory could be auto-detected. Use --base to specify it explicitly."}
            )
        elif len(base_candidates) == 1:
            base_dir = base_candidates[0]
            issues.append(
                {"level": "OK", "item": "plan detection", "message": f"Auto-detected BASE directory: {base_dir.name}"}
            )
        else:
            base_dir = base_candidates[0]
            names = ", ".join(p.name for p in base_candidates)
            issues.append(
                {"level": "WARN", "item": "plan detection", "message": f"Multiple BASE candidates found; selected {base_dir.name}. Candidates: {names}"}
            )

    # ---- C. TEST detection ----
    base_name_set = {base_dir.name} if base_dir else set()
    _test_count = 0

    for sd in subdirs:
        if sd.name in base_name_set:
            continue
        intent = infer_intent_from_name(sd.name)
        if intent:
            tests.append({"name": sd.name, "path": sd, "intent": intent})
            _test_count += 1
        else:
            issues.append(
                {"level": "WARN", "item": "plan detection", "message": f"Skipped directory because experiment intent could not be inferred: {sd.name}"}
            )

    if _test_count == 0:
        issues.append(
            {"level": "ERROR", "item": "plan detection", "message": "No TEST experiment directories were detected."}
        )
    else:
        issues.append(
            {"level": "OK", "item": "plan detection", "message": f"Detected {_test_count} TEST experiment directories."}
        )

    # ---- D. Sort tests by intent order, then name ----
    tests.sort(key=lambda t: (_intent_sort_key(t["intent"]), t["name"].lower()))

    return {"root": experiment_root, "base_dir": base_dir, "tests": tests, "issues": issues}

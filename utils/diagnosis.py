"""Diagnosis summary generator for gcdoctor.

Produces a short human-readable diagnosis block that summarizes the main
issues, likely causes, and recommended fixes before the detailed results.
"""


def generate_diagnosis_summary(results: list[dict]) -> list[dict]:
    """Generate high-level diagnosis entries from diagnostic results.

    Parameters
    ----------
    results:
        Diagnostic records collected by gcdoctor checks.

    Returns
    -------
    list[dict]
        Diagnosis entries in the standard ``{"level", "item", "message"}`` format.
    """
    diagnoses: list[dict] = []

    # Rule 1: BoundaryConditions species missing
    _has_bc_missing = any(
        "Missing BoundaryConditions species detected" in r.get("message", "")
        for r in results
    )
    if _has_bc_missing:
        diagnoses.append(
            {
                "level": "ERROR",
                "item": "diagnosis",
                "message": "Main issue: BoundaryConditions species are missing.",
            }
        )
        diagnoses.append(
            {
                "level": "ERROR",
                "item": "diagnosis",
                "message": "Likely cause: BoundaryConditions files do not match the current GEOS-Chem chemical mechanism.",
            }
        )
        diagnoses.append(
            {
                "level": "WARN",
                "item": "diagnosis",
                "message": "Recommended fix: Generate BoundaryConditions files from a matching global fullchem simulation instead of using old SAMPLE_BCs.",
            }
        )

    # Rule 2: SAMPLE_BCs risk
    _has_sample_bcs = any(
        "SAMPLE_BCs detected" in r.get("message", "") for r in results
    )
    if _has_sample_bcs:
        diagnoses.append(
            {
                "level": "WARN",
                "item": "diagnosis",
                "message": "Risk: SAMPLE_BCs are being used. They are suitable for testing only and may be incompatible with the current mechanism.",
            }
        )

    # Rule 3: restart missing (only ERROR level)
    _has_restart_error = any(
        r.get("level") == "ERROR"
        and (
            "GEOS-Chem restart" in r.get("message", "")
            or "HEMCO restart" in r.get("message", "")
            or "restart" in r.get("message", "")
            or "GEOS-Chem restart" in r.get("item", "")
            or "HEMCO restart" in r.get("item", "")
            or "restart" in r.get("item", "")
        )
        for r in results
    )
    if _has_restart_error:
        diagnoses.append(
            {
                "level": "ERROR",
                "item": "diagnosis",
                "message": "Run prerequisite issue: restart files appear incomplete or missing.",
            }
        )

    # Fallback
    if not diagnoses:
        diagnoses.append(
            {
                "level": "OK",
                "item": "diagnosis",
                "message": "No high-priority diagnosis rule was triggered.",
            }
        )

    return diagnoses

"""Core comparison logic for gcdoctor compare tool."""

from pathlib import Path

from checks.check_config import get_config_metadata


# Keys compared in geoschem_config.yml metadata
_CONFIG_COMPARE_KEYS = [
    "simulation.name",
    "operations.start_date",
    "operations.end_date",
    "grid.resolution",
    "grid.longitude",
    "grid.latitude",
    "grid.nested_grid_simulation",
    "met_field",
]

# Keywords scanned in HEMCO_Config.rc
_HEMCO_KEYWORDS = [
    "SAMPLE_BCs",
    "BoundaryConditions",
    "CEDS",
    "MEIC",
    "China",
    "China_mask",
    "Outside_China_mask",
    "MASK",
    "NOx",
    "CO",
    "SO2",
    "NH3",
    "VOC",
]

# Core config keys that define experiment comparability
_CORE_SIM_KEYS = [
    "operations.start_date",
    "operations.end_date",
    "grid.resolution",
    "grid.longitude",
    "grid.latitude",
]


def _read_text_lines(path: Path) -> list[str] | None:
    """Read a text file, returning lines or None on failure."""
    try:
        return path.read_text(errors="ignore").splitlines()
    except OSError:
        return None


def _file_status(path: Path) -> str:
    """Return 'exists', 'missing', or 'not-a-dir' for a path."""
    if not path.exists():
        return "missing"
    if not path.is_file():
        return "not-a-file"
    return "exists"


def compare_run_directories(base_dir: Path, test_dir: Path) -> list[dict]:
    """Compare two GEOS-Chem run directories and return diagnostic results."""
    results: list[dict] = []

    # ---- A. Directory existence ----
    _base_exists = base_dir.is_dir()
    _test_exists = test_dir.is_dir()

    if not base_dir.exists():
        results.append(
            {"level": "ERROR", "item": "base directory", "message": "BASE directory does not exist."}
        )
    elif not base_dir.is_dir():
        results.append(
            {"level": "ERROR", "item": "base directory", "message": "BASE path is not a directory."}
        )

    if not test_dir.exists():
        results.append(
            {"level": "ERROR", "item": "test directory", "message": "TEST directory does not exist."}
        )
    elif not test_dir.is_dir():
        results.append(
            {"level": "ERROR", "item": "test directory", "message": "TEST path is not a directory."}
        )

    if _base_exists and _test_exists:
        results.append(
            {"level": "OK", "item": "directories", "message": "Both BASE and TEST directories exist."}
        )

    # ---- B. Required files ----
    _required_files = ["geoschem_config.yml", "HEMCO_Config.rc", "HISTORY.rc"]
    _file_statuses: dict[str, dict[str, str]] = {}

    for fname in _required_files:
        base_status = _file_status(base_dir / fname) if _base_exists else "dir-missing"
        test_status = _file_status(test_dir / fname) if _test_exists else "dir-missing"
        _file_statuses[fname] = {"base": base_status, "test": test_status}

        if base_status == "exists" and test_status == "exists":
            results.append(
                {"level": "OK", "item": "required file", "message": f"{fname} exists in both BASE and TEST."}
            )
        elif base_status == "exists" and test_status != "exists":
            results.append(
                {"level": "ERROR", "item": "required file", "message": f"{fname} exists in BASE but is missing in TEST."}
            )
        elif base_status != "exists" and test_status == "exists":
            results.append(
                {"level": "ERROR", "item": "required file", "message": f"{fname} is missing in BASE but exists in TEST."}
            )
        else:
            results.append(
                {"level": "ERROR", "item": "required file", "message": f"{fname} is missing in both BASE and TEST."}
            )

    # ---- C. geoschem_config.yml metadata compare ----
    _base_config = _file_statuses.get("geoschem_config.yml", {}).get("base", "") == "exists"
    _test_config = _file_statuses.get("geoschem_config.yml", {}).get("test", "") == "exists"

    _base_meta: dict[str, str] = {}
    _test_meta: dict[str, str] = {}

    if _base_config and _test_config:
        _base_lines = _read_text_lines(base_dir / "geoschem_config.yml")
        _test_lines = _read_text_lines(test_dir / "geoschem_config.yml")
        if _base_lines is not None:
            _base_meta = get_config_metadata(_base_lines)
        if _test_lines is not None:
            _test_meta = get_config_metadata(_test_lines)

        _compared_any = False
        _all_core_consistent = True

        for key in _CONFIG_COMPARE_KEYS:
            _in_base = key in _base_meta
            _in_test = key in _test_meta

            if _in_base and _in_test:
                _compared_any = True
                if _base_meta[key] == _test_meta[key]:
                    results.append(
                        {"level": "OK", "item": "config compare", "message": f"{key} is consistent: {_base_meta[key]}"}
                    )
                else:
                    results.append(
                        {"level": "WARN", "item": "config compare", "message": f"{key} differs: BASE={_base_meta[key]}, TEST={_test_meta[key]}"}
                    )
                    if key in _CORE_SIM_KEYS:
                        _all_core_consistent = False
            elif _in_base:
                _compared_any = True
                results.append(
                    {"level": "WARN", "item": "config compare", "message": f"{key} exists only in BASE: {_base_meta[key]}"}
                )
                _all_core_consistent = False
            elif _in_test:
                _compared_any = True
                results.append(
                    {"level": "WARN", "item": "config compare", "message": f"{key} exists only in TEST: {_test_meta[key]}"}
                )
                _all_core_consistent = False

        if not _compared_any:
            results.append(
                {"level": "WARN", "item": "config compare", "message": "No comparable metadata keys were found in either geoschem_config.yml."}
            )
    else:
        results.append(
            {"level": "WARN", "item": "config compare", "message": "Skipped geoschem_config.yml metadata comparison because one or both config files are missing."}
        )
        _all_core_consistent = False

    # ---- D. HEMCO_Config.rc keyword comparison ----
    _base_hemco_ok = _file_statuses.get("HEMCO_Config.rc", {}).get("base", "") == "exists"
    _test_hemco_ok = _file_statuses.get("HEMCO_Config.rc", {}).get("test", "") == "exists"
    _hemco_keyword_results: dict[str, str] = {}  # keyword -> "both" | "base_only" | "test_only"

    if _base_hemco_ok and _test_hemco_ok:
        _base_hemco_lines = _read_text_lines(base_dir / "HEMCO_Config.rc")
        _test_hemco_lines = _read_text_lines(test_dir / "HEMCO_Config.rc")
        _base_text = "\n".join(_base_hemco_lines or [])
        _test_text = "\n".join(_test_hemco_lines or [])
        _base_lower = _base_text.lower()
        _test_lower = _test_text.lower()

        for kw in _HEMCO_KEYWORDS:
            _kw_lower = kw.lower()
            _in_base = _kw_lower in _base_lower
            _in_test = _kw_lower in _test_lower

            if _in_base and _in_test:
                results.append(
                    {"level": "OK", "item": "HEMCO keyword", "message": f"Keyword '{kw}' appears in both BASE and TEST."}
                )
                _hemco_keyword_results[kw] = "both"
            elif _in_test:
                results.append(
                    {"level": "WARN", "item": "HEMCO keyword", "message": f"Keyword '{kw}' appears only in TEST."}
                )
                _hemco_keyword_results[kw] = "test_only"
            elif _in_base:
                results.append(
                    {"level": "WARN", "item": "HEMCO keyword", "message": f"Keyword '{kw}' appears only in BASE."}
                )
                _hemco_keyword_results[kw] = "base_only"

        # Special HEMCO rules
        _meic_test_only = _hemco_keyword_results.get("MEIC") == "test_only"
        _has_mask_test = any(
            _hemco_keyword_results.get(m) in ("test_only", "both")
            for m in ["China_mask", "Outside_China_mask"]
        )

        if _meic_test_only:
            results.append(
                {"level": "WARN", "item": "experiment design", "message": "TEST contains MEIC-related entries while BASE does not. This may be expected for a MEIC sensitivity experiment."}
            )

        _sample_bcs_asym = _hemco_keyword_results.get("SAMPLE_BCs") in ("base_only", "test_only")
        if _sample_bcs_asym:
            results.append(
                {"level": "WARN", "item": "experiment design", "message": "SAMPLE_BCs usage differs between BASE and TEST. Confirm whether BoundaryConditions are intentionally different."}
            )

        _bc_asym = _hemco_keyword_results.get("BoundaryConditions") in ("base_only", "test_only")
        if _bc_asym:
            results.append(
                {"level": "WARN", "item": "experiment design", "message": "BoundaryConditions configuration appears only in one directory. Confirm nested-run BC consistency."}
            )
    else:
        results.append(
            {"level": "WARN", "item": "HEMCO keyword", "message": "Skipped HEMCO_Config.rc keyword comparison because one or both files are missing."}
        )

    # ---- E. HISTORY.rc comparison ----
    _base_hist_ok = _file_statuses.get("HISTORY.rc", {}).get("base", "") == "exists"
    _test_hist_ok = _file_statuses.get("HISTORY.rc", {}).get("test", "") == "exists"

    if _base_hist_ok and _test_hist_ok:
        _base_hist_text = (base_dir / "HISTORY.rc").read_text(errors="ignore")
        _test_hist_text = (test_dir / "HISTORY.rc").read_text(errors="ignore")
        if _base_hist_text == _test_hist_text:
            results.append(
                {"level": "OK", "item": "HISTORY compare", "message": "HISTORY.rc content is identical between BASE and TEST."}
            )
        else:
            results.append(
                {"level": "WARN", "item": "HISTORY compare", "message": "HISTORY.rc content differs between BASE and TEST. Confirm diagnostic output settings."}
            )
    else:
        results.append(
            {"level": "WARN", "item": "HISTORY compare", "message": "Skipped HISTORY.rc comparison because one or both files are missing."}
        )

    # ---- F. Restart files comparison ----
    _geoschem_restart_patterns = ["GEOSChem.Restart*.nc4", "GEOSChem.Restart*.nc"]
    _hemco_restart_patterns = ["HEMCO_restart*.nc", "HEMCO_restart*.nc4"]

    def _count_restart_files(d: Path, patterns: list[str]) -> int:
        if not d.is_dir():
            return 0
        count = 0
        for pat in patterns:
            count += len(list(d.glob(pat)))
        return count

    _base_geoschem_count = _count_restart_files(base_dir, _geoschem_restart_patterns)
    _test_geoschem_count = _count_restart_files(test_dir, _geoschem_restart_patterns)
    _base_hemco_count = _count_restart_files(base_dir, _hemco_restart_patterns)
    _test_hemco_count = _count_restart_files(test_dir, _hemco_restart_patterns)

    # GEOS-Chem restart
    if _base_geoschem_count > 0 and _test_geoschem_count > 0:
        results.append(
            {"level": "OK", "item": "restart compare", "message": "GEOS-Chem restart files exist in both BASE and TEST."}
        )
    elif _base_geoschem_count > 0:
        results.append(
            {"level": "WARN", "item": "restart compare", "message": "GEOS-Chem restart files exist only in BASE."}
        )
    elif _test_geoschem_count > 0:
        results.append(
            {"level": "WARN", "item": "restart compare", "message": "GEOS-Chem restart files exist only in TEST."}
        )
    else:
        results.append(
            {"level": "ERROR", "item": "restart compare", "message": "GEOS-Chem restart files are missing in both BASE and TEST."}
        )

    # HEMCO restart
    if _base_hemco_count > 0 and _test_hemco_count > 0:
        results.append(
            {"level": "OK", "item": "restart compare", "message": "HEMCO restart files exist in both BASE and TEST."}
        )
    elif _base_hemco_count > 0:
        results.append(
            {"level": "WARN", "item": "restart compare", "message": "HEMCO restart files exist only in BASE."}
        )
    elif _test_hemco_count > 0:
        results.append(
            {"level": "WARN", "item": "restart compare", "message": "HEMCO restart files exist only in TEST."}
        )
    else:
        results.append(
            {"level": "WARN", "item": "restart compare", "message": "HEMCO restart files are missing in both BASE and TEST."}
        )

    # ---- G. Experiment design summary ----
    _all_core_ok = _base_config and _test_config
    if _all_core_ok:
        _core_consistent = True
        for key in _CORE_SIM_KEYS:
            if _base_meta.get(key) != _test_meta.get(key):
                _core_consistent = False
                break

        if _core_consistent:
            results.append(
                {"level": "OK", "item": "experiment design summary", "message": "BASE and TEST have consistent core simulation period and grid settings."}
            )
        else:
            results.append(
                {"level": "WARN", "item": "experiment design summary", "message": "BASE and TEST differ in core simulation period or grid settings. Confirm whether the experiments are directly comparable."}
            )

    # MEIC + mask detection
    if _meic_test_only and _has_mask_test:
        results.append(
            {"level": "OK", "item": "experiment design summary", "message": "TEST appears to include MEIC and mask-related entries, which is consistent with a regional emission replacement experiment."}
        )
    elif _meic_test_only:
        results.append(
            {"level": "WARN", "item": "experiment design summary", "message": "TEST includes MEIC-related entries but no obvious mask keyword was found. Confirm that regional replacement does not double-count emissions."}
        )

    return results

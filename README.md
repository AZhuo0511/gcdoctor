# gcdoctor

A lightweight diagnostic tool for GEOS-Chem run directories.

## Features

- Checks required run directory files
- Extracts metadata from geoschem_config.yml without PyYAML
- Detects nested-grid markers
- Checks HEMCO_Config.rc paths and SAMPLE_BCs usage
- Checks GEOS-Chem and HEMCO restart files
- Scans GEOS-Chem logs for common errors
- Detects missing BoundaryConditions species such as BC_ACR
- Generates a Markdown report with Diagnosis summary and Detailed results
- Supports custom report output paths

## Usage

Run against the bundled test directory:

```bash
python -m gcdoctor.main test_data/minimal_run ; echo $?
```

The test dataset intentionally contains HEMCO ERROR entries, so **exit code 1 is expected**.

Specify a custom report path:

```bash
python -m gcdoctor.main test_data/minimal_run --output reports/test_report.md
```

Example: diagnose a real GEOS-Chem nested run directory on Ubuntu:

```bash
python -m gcdoctor.main ~/GEOS-Chem/rundirs/gc_05x0625_merra2_fullchem_southchina_test --output ~/gcdoctor_southchina_report.md
```

gcdoctor is **read-only** for the target GEOS-Chem run directory. It reads configuration,
restart, HEMCO, and log files, then writes a separate Markdown report.

## Exit codes

- `0` — no ERROR-level result was detected
- `1` — at least one ERROR-level result was detected

The bundled test directory (`test_data/minimal_run/`) returns 1 because its
`GC.log` deliberately contains HEMCO ERROR entries for validation purposes.

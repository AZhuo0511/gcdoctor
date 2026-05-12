# gcdoctor

A diagnostic tool for GEOS-Chem run directories.

## Features

- Check GEOS-Chem run directory structure
- Validate HEMCO_Config.rc paths
- Detect missing Restart files
- Scan logs for common GEOS-Chem / HEMCO errors
- Generate Markdown diagnostic reports

## Usage

```bash
python -m gcdoctor.main /path/to/run_directory
# Privacy Policy (Prototype Data Handling)

## 1. Scope
This document defines de-identification and precision policies for telemetry used in the accident risk prototype.

## 2. Personally Identifiable Information (PII)
- **Not collected**: names, emails, phone numbers, addresses, SSN, passport IDs.
- **Prohibited**: license plates, VIN, device identifiers (IMEI/IMSI/MAC), IP addresses.
- **Conditional**: internal `driver_id` must be hashed using a salted one-way hash if data providers require linkage.

## 3. Geospatial Precision
- Latitude/Longitude rounded to **4 decimal places** (~11 m at the equator).
- No raw coordinates are exposed outside aggregated heatmaps (tiles/hexes).

## 4. Time Precision
- Timestamps stored as **seconds since epoch (UTC)**.
- Millisecond inputs are downsampled to seconds for privacy and consistency.

## 5. Data Retention
- Raw files are retained only in secured storage for the shortest period required for processing.
- Derived aggregates (tiles/heatmaps) are retained for analysis.

## 6. Access Control
- Access granted to project members only.
- All exports require a license check and a privacy review.

## 7. Compliance & Licensing
- Each dataset’s license is recorded in `docs/data_license_review.md`.
- Redistribution must follow attribution requirements of OGL v3 or provider contracts.

## 8. Change Management
- Any schema or precision changes require approval at **Gate A**.

## 9. Implementation (Phase 2.3)

- **Direct identifiers**: Columns such as `name` are removed from raw exports before any analysis (`scripts/deidentify.py`).
- **Linkable IDs**: Columns like `driver_id` (if present) are hashed using SHA-256 with a project-specific salt via the `DEID_SALT` environment variable.
- **Geospatial precision**: `lat` and `lon` are rounded to 4 decimal places.
- **Time precision**: `timestamp` values are normalized to seconds; millisecond inputs are downsampled.
- **Outputs**: De-identified datasets are written to `data/clean/`. The raw source remains unchanged in `data/raw/` to ensure reproducibility.
- **Summary**: Each run writes `docs/deidentify_summary.md` capturing applied rules and outputs for auditing purposes.

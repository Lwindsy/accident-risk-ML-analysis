# Data Contract v1.0 — Short-Horizon Accident Risk Prototype

**Freeze date (UTC):** 2025-10-20  
**Purpose.** This contract freezes the machine-readable schema, coordinate system, time basis, and sampling policy for all downstream phases. Any change requires a formal review and a version bump.

## Global Meta
- **CRS:** EPSG:4326 (WGS-84)
- **Time Basis:** UTC
- **Sampling Rate:** **10 Hz** (all inputs must be resampled to 10 Hz)
- **Prediction Windows:** 10 s history → 10 s horizon (as per PRD)

## Field Definitions (must-have)
| name      | type  | unit                | notes                                      |
|-----------|-------|---------------------|--------------------------------------------|
| timestamp | float | seconds_since_epoch | Monotonic, UTC                             |
| lat       | float | degrees             | WGS-84, range [-90, 90]                    |
| lon       | float | degrees             | WGS-84, range [-180, 180]                  |
| speed     | float | m/s                 | ≥ 0                                        |
| accel     | float | m/s²                | Forward positive                           |
| heading   | float | degrees             | [0, 360), unwrap → interp → wrap           |

## Standardization Policy
- **Resampling:** Uniform 10 Hz grid on `timestamp`.  
  - Numeric interpolation: linear; heading uses unwrap→linear→wrap.  
  - Categorical columns (if any): forward-fill.  
  - Gaps > 2 s invalidate a window.
- **Coordinates:** Must be EPSG:4326.  
- **Units:** SI units for speed/accel, degrees for headings.

## Quality Gates
- ≥ 95% valid rows after standardization.
- No future information leakage in feature generation.
- Standardized outputs **must not contain PII** (see privacy policy).

## Versioning & Lock
- This document corresponds to `docs/data_contract.yaml`.  
- A SHA-256 hash is stored in `docs/data_contract.lock`.  
- Any change to the YAML contract requires:
  1) Version bump (semantic),  
  2) Updated lock,  
  3) Test updates,  
  4) Reviewer sign-off.

## Rationale
Freezing schema and sampling rate at Phase 2.5 prevents downstream refactors caused by upstream drift (e.g., CRS or frequency changes). The 10 Hz standard suits near-term (≤10 s) risk prediction while maintaining manageable compute.

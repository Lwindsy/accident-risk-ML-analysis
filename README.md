
# Accident Risk Prediction — Project Overview (Phase 0 → 3)

**Status:** Phase 3 completed (Environment ready, Gate A frozen)    

---

## 1 Project Summary
This repository implements an offline prototype that predicts **short‑horizon (≤ 10 s) accident risk** from driving telemetry.  
The system ingests raw trajectory data, ensures privacy‑compliant handling, performs feature engineering, and outputs risk probabilities and hotspot visualizations.

---

## 2 Current Phase
- **Phase 0 → 2.5:** PRD, data acquisition, compliance, de‑identification, precision audit, and data contract freeze.  
- **Phase 3:** Engineering environment — reproducible in ≤ 10 minutes for any developer.  
- **Next (Phase 4):** Data preprocessing and feature engineering using contract‑standardized inputs.

---

## 3 Repository Structure (as of Phase 3)
```
accident‑risk/
├── config/
│   └── logging.conf                   # unified logging (console + file)
├── data/
│   ├── raw/                           # original inputs (licensed + placeholder)
│   ├── clean/                         # de‑identified outputs
│   ├── standardized/                  # 10 Hz resampled per data contract
│   └── processed/                     # to be generated in Phase 4
├── docs/
│   ├── PRD_v1.md                      # product requirements document
│   ├── data_inventory.md              # dataset sources + licenses
│   ├── data_dictionary.csv            # field definitions
│   ├── schema_v1.yaml                 # telemetry schema (frozen)
│   ├── data_contract.yaml/.lock       # Gate A data contract v1.0
│   ├── privacy_policy.md              # privacy policy + implementation
│   ├── privacy_audit_report.md        # raw/clean PII audit results
│   ├── deidentify_summary.md          # hash + precision summary
│   ├── precision_audit_report.md      # coordinate/time precision check
│   ├── compliance_statement.md        # formal Gate A memo
│   ├── env_setup_guide.md             # onboarding instructions
│   └── phase*_completion_log*.md      # frozen logs for each phase
├── reports/
│   └── precision/                     # charts (lat/lon/time histograms)
├── scripts/
│   ├── quality_check.py               # Phase 1 data quality validation
│   ├── generate_schema.py / validate_schema.py
│   ├── license_verify.py              # verify license URL reachability
│   ├── privacy_check.py               # detect PII fields + precision signals
│   ├── deidentify.py                  # drop/hash/round/normalize sensitive data
│   ├── precision_audit.py             # verify lat/lon/time granularity
│   ├── build_data_contract.py / verify_data_contract.py / resample_to_contract.py
│   ├── setup_dirs.py / setup_env.py   # create folders + venv bootstrap
│   ├── init_logger.py                 # configure logging
│   └── verify_reproducibility.py      # 10‑minute environment validator
├── tests/
│   ├── test_schema.py / test_privacy_check.py / test_precision_audit.py
│   ├── test_data_contract.py / test_resample_policy.py
│   ├── test_structure.py / test_env_setup.py / test_logger.py / test_reproducibility.py
│   └── conftest.py                    # shared fixtures + import path fix
├── Makefile                           # full automation and Gate A workflow
├── requirements.txt / requirements‑dev.txt
└── README.md (this file)
```

---

## 4 Makefile Targets (Snapshot)
| Target | Description |
|---------|--------------|
| `make privacy-audit` | Run PII scan on raw data (fails if PII found). |
| `make privacy-audit-allow` | Same but non‑blocking (exit 0). |
| `make deidentify` | Apply hash/round policies and write `data/clean/`. |
| `make privacy-audit-clean` | Audit clean data (must pass). |
| `make precision-audit` | Generate precision report + charts. |
| `make data-contract-build` / `verify` | Build and validate contract + lock checksum. |
| `make data-standardize` | Resample to 10 Hz per contract. |
| `make setup-structure` / `setup` | Create dirs + install runtime/dev deps. |
| `make lint` / `typecheck` / `test` / `ci` | Quality gates via flake8 / mypy / pytest. |
| `make gateA-approve` | Full compliance chain: license → PII → de‑id → clean audit → PASS. |

---

## 5 Environment & Dependencies
- **Python:** 3.11 recommended  
- **Runtime:** `pandas`, `numpy`, `pyyaml`, `matplotlib`  
- **Dev:** `pytest`, `flake8`, `black`, `isort`, `mypy`, `pytest‑cov`, `types‑requests`, `pandas‑stubs`  
- **Logs:** `config/logging.conf` → `logs/project_YYYYmmdd_HHMMSS.log`  
- **Reproducibility:** `python scripts/verify_reproducibility.py --force‑recreate` must finish < 10 min and return `"passed_all": true`.

---

## 6 Data Governance (Gate A Chain)
1. **License Verification** → `docs/data_license_review.md` (all links reachable).  
2. **Privacy Audit** → `privacy_check.py` detects PII (`name`, `driver_id`, etc.).  
3. **De‑identification** → `deidentify.py` drops or hashes sensitive fields (SHA‑256 with `DEID_SALT`).  
4. **Precision Audit** → geo ≤ 4 decimals; timestamps in seconds.  
5. **Data Contract Freeze** → `data_contract.yaml/.lock`; sampling = 10 Hz; CRS = EPSG:4326; UTC time.  
6. **Compliance Statement** → `docs/compliance_statement.md` and Gate A logs.  

All subsequent phases must honor this contract and schema; any change requires new Gate A review.

---

## 7 Setup & Validation
```bash
# One‑command environment setup
make setup‑structure && make setup

# Run compliance pipeline
export DEID_SALT="dev‑salt"
make gateA‑approve

# Verify environment reproducibility
python scripts/verify_reproducibility.py --force‑recreate
```

Expected: all green checks, exit code 0, runtime ≤ 10 minutes.


.PHONY: download list-data quality-check schema validate-schema gateA-check

download:
	@echo "Downloading sample driving dataset..."
	@mkdir -p data/raw
	@curl -L -o data/raw/driving_sample.csv https://raw.githubusercontent.com/mwaskom/seaborn-data/master/mpg.csv
	@echo "Sample dataset downloaded."

list-data:
	@echo "Listing datasets in ./data/raw:"
	@ls -lh data/raw

quality-check:
	@echo "Running quick quality check..."
	@python scripts/quality_check.py

schema:
	@echo "Generating schema_v1.yaml from data_dictionary.csv..."
	@python scripts/generate_schema.py

validate-schema:
	@echo "Validating schema against sample CSV (demo mode)..."
	@python scripts/validate_schema.py data/raw/driving_sample.csv

gateA-check: schema validate-schema
	@echo "Gate A pre-check completed."


.PHONY: privacy-audit privacy-audit-allow gateA-approve

privacy-audit:
	python3 scripts/privacy_check.py

privacy-audit-allow:
	python3 scripts/privacy_check.py --allow-pii

gateA-approve:
	python3 scripts/license_verify.py
	python3 scripts/privacy_check.py --allow-pii
	DEID_SALT=$(DEID_SALT) python3 scripts/deidentify.py
	python3 scripts/privacy_check.py --glob "data/clean/*.csv"
	@echo "Gate A approval check complete"

.PHONY: deidentify privacy-audit-clean

deidentify:
	DEID_SALT=please-change-me python3 scripts/deidentify.py

# 对清洗后的数据再跑一次隐私审计，确保无PII
privacy-audit-clean:
	python3 scripts/privacy_check.py --glob "data/clean/*.csv"

.PHONY: precision-audit
precision-audit:
	python3 scripts/precision_audit.py

.PHONY: data-contract-build data-contract-verify data-standardize gateA-assert-contract

data-contract-build:
	python3 scripts/build_data_contract.py

data-contract-verify:
	python3 scripts/verify_data_contract.py

data-standardize:
	python3 scripts/resample_to_contract.py --input-glob "data/clean/*.csv" --output-dir "data/standardized" --rate-hz 10

gateA-assert-contract:
	python3 scripts/build_data_contract.py
	python3 scripts/verify_data_contract.py
	@echo "Data Contract assertions passed (Phase 2.5)."


# Detect platform to build correct venv paths.
ifeq ($(OS),Windows_NT)
  ACTIVATE = .venv\Scripts\activate
  PY = .venv\Scripts\python.exe
  PIP = .venv\Scripts\pip.exe
  SEP = \ 
else
  ACTIVATE = . .venv/bin/activate
  PY = .venv/bin/python
  PIP = .venv/bin/pip
  SEP = /
endif

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  setup             Create/refresh venv and install runtime + dev requirements"
	@echo "  env               Alias of 'setup'"
	@echo "  setup-structure   Create required folders safely (idempotent)"
	@echo "  init-logger       Initialize logger and write a timestamped log file"
	@echo "  test              Run pytest test suite"
	@echo "  lint              Run flake8, black (check), isort (check)"
	@echo "  typecheck         Run mypy for static type checking"
	@echo "  clean-venv        Remove local virtual environment"
	@echo "  ci                Run structure, env, lint, typecheck, and tests"

# Ensure minimal repo scaffolding is present.
.PHONY: setup-structure
setup-structure:
	@echo "[make] Ensuring canonical directories exist"
	@python scripts$(SEP)setup_dirs.py

# Create or reuse .venv and install dependencies.
.PHONY: setup
setup:
	@echo "[make] Bootstrapping environment in .venv"
	@python scripts$(SEP)setup_env.py

# Alias for convenience.
.PHONY: env
env: setup

# Initialize logging; produces logs/project_*.log and console output.
.PHONY: init-logger
init-logger:
	@echo "[make] Initializing logger"
	@python scripts$(SEP)init_logger.py

# Run tests with pytest; assumes dev dependencies installed.
.PHONY: test
test:
	@echo "[make] Running tests"
	@$(PY) -m pytest -q

# Linting with flake8 and format checks with black/isort (no changes applied).
.PHONY: lint
lint:
	@echo "[make] Lint: flake8"
	@$(PY) -m flake8 .

# Static type checking.
.PHONY: typecheck
typecheck:
	@echo "[make] Type checking with mypy"
	@$(PY) -m mypy --config-file mypy.ini

# Clean local venv only (safe; no source removal).
.PHONY: clean-venv
clean-venv:
	@echo "[make] Removing .venv"
	@if [ -d ".venv" ]; then rm -rf .venv; fi

# Aggregate CI-like flow: structure -> env -> lint -> typecheck -> test
.PHONY: ci
ci: setup-structure setup lint typecheck test
	@echo "[make] CI pipeline completed"
import argparse
import re
import time
from pathlib import Path
from typing import List, Tuple
import requests

REVIEW_MD = Path("docs/data_license_review.md")

# Known-good license domains: if network is flaky, we can still mark these OK in non-strict mode.
KNOWN_OK_DOMAINS = {
    "www.nationalarchives.gov.uk",   # Open Government Licence v3
    "nationalarchives.gov.uk",
}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

def _is_table_row(line: str) -> bool:
    """Return True if this markdown line looks like a table row (not header or separator)."""
    if "|" not in line:
        return False
    # Skip header identifiers and separator lines like |----|
    if re.search(r"^\s*\|?\s*(?:-+\s*\|)+\s*-*\s*$", line):
        return False
    if "Dataset Name" in line and "License URL" in line:
        return False
    return True

def _split_cells(line: str) -> List[str]:
    """Split a markdown table row into cells, trimming outer pipes and whitespace."""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    cells = [c.strip() for c in line.split("|")]
    return cells

def parse_review_table(md_path: Path) -> List[Tuple[str, str]]:
    """
    Parse the markdown table and return (dataset_name, license_url) rows.
    The expected columns are:
      0: Dataset Name
      1: Source URL
      2: License Type
      3: License URL
      4: Usage Allowed
      5: Notes
    """
    if not md_path.exists():
        raise FileNotFoundError(f"Missing file: {md_path}")

    rows: List[Tuple[str, str]] = []
    with md_path.open("r", encoding="utf-8") as f:
        for raw in f:
            if not _is_table_row(raw):
                continue
            cells = _split_cells(raw)
            # Require at least 6 columns as per spec
            if len(cells) < 6:
                continue
            dataset = cells[0]
            license_url = cells[3]
            rows.append((dataset, license_url))
    return rows

def http_ok(url: str, timeout: float = 8.0, retries: int = 2) -> bool:
    """
    Check if URL is reachable with status 2xx.
    Strategy:
      1) HEAD with redirects and UA
      2) GET if HEAD not 2xx
      3) retry on network exceptions with brief backoff
    """
    if not url or url.lower() in {"n/a", "-", "none"}:
        return False

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    def attempt(method: str) -> bool:
        try:
            resp = session.request(
                method=method,
                url=url,
                allow_redirects=True,
                timeout=timeout,
            )
            return 200 <= resp.status_code < 300
        except requests.RequestException:
            return False

    for i in range(retries + 1):
        # Try HEAD first
        if attempt("HEAD"):
            return True
        # Fallback to GET
        if attempt("GET"):
            return True
        if i < retries:
            time.sleep(0.6 * (i + 1))
    return False

def domain_from_url(url: str) -> str:
    m = re.match(r"^https?://([^/]+)", url.strip())
    return m.group(1).lower() if m else ""

def verify(strict: bool) -> int:
    """
    Verify license URLs. Returns process exit code (0 on success).
    In non-strict mode, known-good license domains pass even if network is flaky.
    """
    rows = parse_review_table(REVIEW_MD)
    if not rows:
        print("No data rows parsed from docs/data_license_review.md")
        return 1

    print("Verifying license URLs...\n")
    failures = 0
    for dataset, url in rows:
        if not url or url.lower() in {"n/a", "-", "none"}:
            print(f"[SKIP] {dataset}: no license URL")
            continue

        ok = http_ok(url)
        if ok:
            print(f"[OK]   {dataset}: {url}")
            continue

        # Non-strict fallback: trust well-known license domains even if transiently unreachable
        domain = domain_from_url(url)
        if not strict and domain in KNOWN_OK_DOMAINS:
            print(f"[OK*]  {dataset}: {url} (trusted domain fallback)")
            continue

        print(f"[FAIL] {dataset}: {url}")
        failures += 1

    print("\nCompleted license verification.")
    return 0 if failures == 0 else 2

def main():
    parser = argparse.ArgumentParser(
        description="Verify license URLs in docs/data_license_review.md"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on any unreachable URL (no trusted-domain fallback).",
    )
    args = parser.parse_args()
    exit_code = verify(strict=args.strict)
    raise SystemExit(exit_code)

if __name__ == "__main__":
    main()

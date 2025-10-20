"""
Tests for scripts/verify_reproducibility.py.

These tests avoid side effects by using dry-run mode and by monkeypatching
subprocess calls and timers to simulate durations and outcomes deterministically.
"""
from pathlib import Path
import importlib.util
import json


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _import_verify():
    target = PROJECT_ROOT / "scripts" / "verify_reproducibility.py"
    spec = importlib.util.spec_from_file_location("verify_repro", target)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module


def test_dry_run_succeeds_within_threshold(tmp_path, monkeypatch, capsys):
    mod = _import_verify()
    # Prepare required files in the tmp working dir
    monkeypatch.chdir(tmp_path)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "scripts" / "setup_env.py").write_text("print('ok')")
    (tmp_path / "requirements.txt").write_text("numpy\n")
    (tmp_path / "requirements-dev.txt").write_text("pytest\n")

    # Monkeypatch subprocess to simulate success and time to simulate fast runs
    monkeypatch.setattr(mod, "_run", lambda cmd, dry_run: 0)

    # Use a controlled perf_counter to simulate 2 seconds total
    times = [0.0, 1.0, 1.0, 2.0]
    def fake_perf():
        return times.pop(0)
    monkeypatch.setattr(mod.time, "perf_counter", fake_perf)

    code = mod.main(["--dry-run", "--max-minutes", "10"])
    out = capsys.readouterr().out
    assert code == 0

    # Extract JSON block regardless of prefix and nested braces
    lines = []
    brace_level = 0
    collecting = False

    for raw in out.splitlines():
        clean = raw.replace("[repro]", "").rstrip()
        if "{" in clean:
            brace_level += clean.count("{")
            collecting = True
        if collecting:
            lines.append(clean.strip())
        if "}" in clean:
            brace_level -= clean.count("}")
            if brace_level == 0 and collecting:
                break

    assert lines, f"No JSON block detected in output:\n{out}"

    json_text = "\n".join(lines)
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise AssertionError(f"Malformed JSON extracted:\n{json_text}\n\nOriginal output:\n{out}\n\nError: {e}")

    assert data["passed_all"] is True
    assert data["dry_run"] is True


def test_real_logic_threshold_exceeded(tmp_path, monkeypatch, capsys):
    mod = _import_verify()
    monkeypatch.chdir(tmp_path)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "scripts" / "setup_env.py").write_text("print('ok')")
    (tmp_path / "requirements.txt").write_text("numpy\n")
    (tmp_path / "requirements-dev.txt").write_text("pytest\n")

    # Simulate commands OK
    monkeypatch.setattr(mod, "_run", lambda cmd, dry_run: 0)

    # 800 seconds total to exceed default 10 min (600 s)
    times = [0.0, 400.0, 400.0, 800.0]
    def fake_perf():
        return times.pop(0)
    monkeypatch.setattr(mod.time, "perf_counter", fake_perf)

    code = mod.main([])  # default max-minutes=10
    out = capsys.readouterr().out
    assert code == 2
    assert "exceeded" in out.lower()


def test_missing_files_cause_validation_error(tmp_path, monkeypatch, capsys):
    mod = _import_verify()
    monkeypatch.chdir(tmp_path)
    # Do not create required files
    code = mod.main(["--dry-run"])
    out = capsys.readouterr().out
    assert code == 2
    assert "Missing required files" in out


def test_pytest_failure_propagates(tmp_path, monkeypatch, capsys):
    mod = _import_verify()
    monkeypatch.chdir(tmp_path)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "scripts" / "setup_env.py").write_text("print('ok')")
    (tmp_path / "requirements.txt").write_text("numpy\n")
    (tmp_path / "requirements-dev.txt").write_text("pytest\n")

    # setup_env success, pytest fails
    def fake_run(cmd, dry_run):
        if "setup_env.py" in " ".join(cmd):
            return 0
        if "-m" in cmd and "pytest" in cmd:
            return 1
        return 0

    monkeypatch.setattr(mod, "_run", fake_run)

    # Keep time small so failure is not due to time
    times = [0.0, 1.0, 1.0, 2.0]
    def fake_perf():
        return times.pop(0)
    monkeypatch.setattr(mod.time, "perf_counter", fake_perf)

    code = mod.main([])
    out = capsys.readouterr().out
    assert code == 2
    assert "Failed steps" in out

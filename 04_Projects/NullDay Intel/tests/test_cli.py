"""Tests for main CLI entrypoint."""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_cli_dry_run_help():
    cmd = [sys.executable, str(PROJECT_ROOT / "main.py"), "--help"]
    res = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
    assert res.returncode == 0
    assert "NullDay Intel" in res.stdout
    assert "--dry-run" in res.stdout
    assert "--mode" in res.stdout


def test_cli_dry_run_execution(tmp_path):
    test_db = tmp_path / "cli_test.db"
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "main.py"),
        "--mode",
        "daily",
        "--dry-run",
        "--db-path",
        str(test_db),
    ]
    res = subprocess.run(
        cmd,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(PROJECT_ROOT),
        env=env,
    )
    assert res.returncode == 0
    assert "[DRY-RUN]" in res.stdout
    assert "DISCORD WEBHOOK PAYLOAD PREVIEW" in res.stdout
    assert "X / TWITTER ALERT PREVIEW" in res.stdout

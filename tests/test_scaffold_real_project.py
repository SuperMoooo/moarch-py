"""Generates real projects and runs their own checks. Slow and needs network: `-m scaffold`."""

import os
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from moarch_py.cli import app

# Each run creates fresh virtual environments, which antivirus Auto-Sandbox
# heuristics scan one by one; on a Windows machine with AVG that can freeze it.
# So it runs on CI (which sets CI=true) or when explicitly asked for locally.
pytestmark = [
    pytest.mark.scaffold,
    pytest.mark.skipif(
        not (os.environ.get("CI") or os.environ.get("MOARCH_PY_SCAFFOLD")),
        reason="runs on CI; set MOARCH_PY_SCAFFOLD=1 to run it locally",
    ),
]


def _run(command: list[str], cwd: Path) -> None:
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    assert completed.returncode == 0, f"{' '.join(command)}\n{completed.stdout}{completed.stderr}"


@pytest.mark.parametrize("database", ["postgres", "sqlite"])
def test_a_generated_project_passes_its_own_checks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, database: str
) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    created = runner.invoke(app, ["init", "demo-api", "--all", "--db", database])
    assert created.exit_code == 0, created.output
    project = tmp_path / "demo-api"
    added = runner.invoke(app, ["create", "feature", "orders", "-p", str(project)])
    assert added.exit_code == 0, added.output

    # Through `python -m`, never the venv's .exe launchers: antivirus
    # Auto-Sandbox heuristics flag those (see commands.RUFF).
    python = ["uv", "run", "python", "-m"]
    _run([*python, "ruff", "format", "--check", "."], project)
    _run([*python, "ruff", "check", "."], project)
    _run([*python, "mypy", "src"], project)
    _run([*python, "pytest", "-q"], project)

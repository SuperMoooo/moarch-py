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


# import-linter ships no `python -m` entry point; this calls the function behind
# its `lint-imports` script, for the same antivirus reason as `python -m` below.
_LINT_IMPORTS = "from importlinter.cli import lint_imports_command; lint_imports_command()"

# A second module using orders the allowed way: only through its public.py.
_USES_ORDERS_PUBLICLY = '''"""Uses orders only through its public interface."""

from demo_api.modules.orders.public import OrderRead, find_order

__all__ = ["OrderRead", "find_order"]
'''

# The import the contract exists to stop: past public.py, into orders' models.
_REACHES_INTO_ORDERS = "from demo_api.modules.orders.models import Order  # noqa: F401\n"


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
    for module in ("orders", "invoices"):
        added = runner.invoke(app, ["create", "module", module, "-p", str(project)])
        assert added.exit_code == 0, added.output
    lines = runner.invoke(app, ["create", "model", "orders", "order_lines", "-p", str(project)])
    assert lines.exit_code == 0, lines.output
    invoices = project / "src/demo_api/modules/invoices"
    (invoices / "uses_orders.py").write_text(_USES_ORDERS_PUBLICLY, encoding="utf-8")

    # Through `python -m`, never the venv's .exe launchers: antivirus
    # Auto-Sandbox heuristics flag those (see commands.RUFF).
    python = ["uv", "run", "python", "-m"]
    _run([*python, "ruff", "format", "--check", "."], project)
    _run([*python, "ruff", "check", "."], project)
    _run([*python, "mypy", "src"], project)
    _run(["uv", "run", "python", "-c", _LINT_IMPORTS], project)
    _run([*python, "pytest", "-q"], project)

    # The same check must fail once invoices reaches past orders' public.py.
    (invoices / "reaches_in.py").write_text(_REACHES_INTO_ORDERS, encoding="utf-8")
    broken = subprocess.run(
        ["uv", "run", "python", "-c", _LINT_IMPORTS],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )
    assert broken.returncode != 0, broken.stdout
    assert "demo_api.modules.invoices.reaches_in -> demo_api.modules.orders.models" in broken.stdout

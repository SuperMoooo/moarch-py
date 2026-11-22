"""Builds the generated project's `pyproject.toml`, keeping anything already in it.

`moarch-py init` inside an existing `uv init` project must not lose what is
there, so the file is edited with tomlkit (which keeps comments and order)
rather than rendered from a template.
"""

from __future__ import annotations

from pathlib import Path

import tomlkit
from tomlkit.items import Table

from moarch_py.options import ProjectOptions


def _table(document: tomlkit.TOMLDocument | Table, key: str) -> Table:
    """The table at [key], created if missing."""
    if key not in document:
        document[key] = tomlkit.table()
    table = document[key]
    assert isinstance(table, Table)
    return table


def build_pyproject(
    existing: str | None,
    options: ProjectOptions,
    *,
    python_version: str,
    unpinned_dependencies: tuple[list[str], list[str]] | None = None,
) -> str:
    """Returns the project's `pyproject.toml` text.

    [existing] is the current file, if any. [unpinned_dependencies] (runtime,
    dev) is written only when `uv add` will not run (`--no-install`), so the
    file still lists what the project needs.
    """
    document = tomlkit.parse(existing) if existing else tomlkit.document()

    project = _table(document, "project")
    project.setdefault("name", options.name.distribution)
    project.setdefault("version", "0.1.0")
    project.setdefault("description", f"{options.name.title}: a FastAPI service.")
    project.setdefault("readme", "README.md")
    project["requires-python"] = f">={python_version}"
    if unpinned_dependencies:
        runtime, development = unpinned_dependencies
        project["dependencies"] = runtime
        groups = _table(document, "dependency-groups")
        groups["dev"] = development
    else:
        project.setdefault("dependencies", [])

    # A built package (not a loose script) so `src/<package>` imports the same
    # way in the app, the tests and the Docker image.
    build_system = tomlkit.table()
    build_system["requires"] = ["hatchling"]
    build_system["build-backend"] = "hatchling.build"
    document["build-system"] = build_system

    tool = _table(document, "tool")
    tool["ruff"] = _ruff_config(python_version)
    tool["mypy"] = _mypy_config(python_version)
    pytest_table = _table(tool, "pytest")
    pytest_table["ini_options"] = _pytest_config()
    tool["importlinter"] = _import_linter_config(options.name.package)
    return tomlkit.dumps(document)


def _ruff_config(python_version: str) -> Table:
    ruff = tomlkit.table()
    ruff["target-version"] = "py" + python_version.replace(".", "")
    ruff["line-length"] = 100
    lint = tomlkit.table()
    # E/F: errors; I: import order; B: likely bugs; UP: modern syntax;
    # SIM: simpler code; N: PEP 8 names; ASYNC: blocking calls in async code;
    # RUF: ruff's own checks; ANN: every function annotated, and ANN401 bans
    # `Any` (mypy strict catches a missing annotation too, but only in CI —
    # ruff flags it in the editor as it is typed); PGH: no blanket type-ignore
    # or noqa comment without the code it silences.
    lint["select"] = ["E", "F", "I", "B", "UP", "SIM", "N", "ASYNC", "RUF", "ANN", "PGH"]
    ruff["lint"] = lint
    return ruff


def _mypy_config(python_version: str) -> Table:
    mypy = tomlkit.table()
    mypy["python_version"] = python_version
    mypy["strict"] = True
    mypy["plugins"] = ["pydantic.mypy"]
    return mypy


def _pytest_config() -> Table:
    ini_options = tomlkit.table()
    ini_options["testpaths"] = ["tests"]
    # auto: every `async def test_` runs on the event loop, no decorator needed.
    ini_options["asyncio_mode"] = "auto"
    ini_options["asyncio_default_fixture_loop_scope"] = "function"
    # importlib: two modules may both have a `test_service.py` without a clash.
    ini_options["addopts"] = "--import-mode=importlib"
    return ini_options


def _import_linter_config(package: str) -> Table:
    """The contract that makes `modules/` a modular monolith: `uv run lint-imports` checks it.

    Each package under `modules/` is independent of the others: an import from
    one into another breaks the contract, directly or through a chain of
    imports, unless its target is that module's `public.py`. The wildcards
    cover every module, so `create module` never has to edit this table.
    """
    modules = f"{package}.modules"
    contract = tomlkit.table()
    contract["name"] = "Modules talk to each other only through public.py"
    contract["type"] = "independence"
    contract["modules"] = [f"{modules}.*"]
    # `**` (any depth) on the left: import-linter rejects `*` followed by `**`.
    contract["ignore_imports"] = [f"{modules}.** -> {modules}.*.public"]
    # A project with no module, or none that uses another yet, matches nothing
    # here; that is fine, not a configuration error (import-linter's default).
    contract["unmatched_ignore_imports_alerting"] = "none"
    contracts = tomlkit.aot()
    contracts.append(contract)

    import_linter = tomlkit.table()
    import_linter["root_packages"] = [package]
    import_linter["contracts"] = contracts
    return import_linter


def read_project_name(project_root: Path) -> str | None:
    """The `[project] name` of an existing pyproject.toml, or None."""
    path = project_root / "pyproject.toml"
    if not path.exists():
        return None
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    project = document.get("project")
    if project is None or "name" not in project:
        return None
    return str(project["name"])

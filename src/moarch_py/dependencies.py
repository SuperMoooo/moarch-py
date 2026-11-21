"""The packages a generated project depends on, decided by its options.

Versions are not pinned here on purpose: `init` hands these names to
`uv add`, which resolves the newest compatible release and writes it to
`pyproject.toml` as a lower bound and to `uv.lock` exactly. Every new
project therefore starts current, and stays reproducible from its lock.
"""

from __future__ import annotations

from dataclasses import dataclass

from moarch_py.options import ProjectOptions


@dataclass(frozen=True)
class ProjectDependencies:
    """The runtime and development packages for one project."""

    runtime: list[str]
    development: list[str]


def dependencies_for(options: ProjectOptions) -> ProjectDependencies:
    """Returns what `uv add` and `uv add --dev` install for [options]."""
    runtime = [
        # `standard` brings uvicorn, the `fastapi` CLI and email validation.
        "fastapi[standard]",
        "pydantic-settings",
        "sqlalchemy[asyncio]",
        options.database.driver_package,
    ]
    if options.migrations:
        runtime.append("alembic")

    development = ["pytest", "pytest-asyncio", "ruff", "mypy"]
    # The test suite always runs on in-memory SQLite, whatever the app uses,
    # so `uv run pytest` needs no database server.
    if options.database.driver_package != "aiosqlite":
        development.append("aiosqlite")
    if options.pre_commit:
        development.append("pre-commit")
    return ProjectDependencies(runtime=runtime, development=development)

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
        # `standard` brings uvicorn, the `fastapi` CLI, httpx and email validation.
        "fastapi[standard]",
        "pydantic-settings",
        "sqlalchemy[asyncio]",
        options.database.driver_package,
    ]
    if options.migrations:
        runtime.append("alembic")
    runtime.extend(_option_packages(options))

    # import-linter: `lint-imports` keeps modules talking only through public.py.
    development = ["pytest", "pytest-asyncio", "ruff", "mypy", "import-linter"]
    # The test suite always runs on in-memory SQLite, whatever the app uses,
    # so `uv run pytest` needs no database server.
    if options.database.driver_package != "aiosqlite":
        development.append("aiosqlite")
    if options.pre_commit:
        development.append("pre-commit")
    if options.uses_redis:
        # Redis in memory, so the tests need no Redis server either.
        development.append("fakeredis")
    return ProjectDependencies(runtime=runtime, development=development)


def _option_packages(options: ProjectOptions) -> list[str]:
    """The runtime packages the checklist options beyond "What to generate" need."""
    packages: list[str] = []
    if options.auth or options.push:
        # [crypto]: RS256, for Google and Apple ID tokens and Firebase's service account.
        packages.append("pyjwt[crypto]")
    if options.auth:
        packages.append("pwdlib[argon2]")
    if options.uses_redis:
        packages.append("redis")
    packages.extend(options.broker.packages)
    if options.email:
        packages.append("aiosmtplib")
    if options.storage:
        packages.append("obstore")
    if options.tracing:
        packages.extend(
            [
                "opentelemetry-sdk",
                "opentelemetry-exporter-otlp-proto-http",
                "opentelemetry-instrumentation-fastapi",
                "opentelemetry-instrumentation-sqlalchemy",
            ]
        )
    if options.sentry:
        packages.append("sentry-sdk[fastapi]")
    if options.metrics:
        packages.append("prometheus-client")
    return packages

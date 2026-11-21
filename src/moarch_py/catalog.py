"""The registry of every file `moarch-py init` generates.

A new generated file is a template under `templates/` plus one entry here.
Miss the entry and `init` never writes it and `update` can never refresh it.
`when` decides from the project's options whether the file belongs.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from moarch_py.options import ProjectOptions


def _always(_: ProjectOptions) -> bool:
    return True


@dataclass(frozen=True)
class ScaffoldSpec:
    """One generated file: where it goes, what renders it, and when it exists."""

    slug: str
    """The name `moarch-py update <slug>` takes; unique across the catalog."""

    path: str
    """The project-relative path; `{package}` is replaced by the package name."""

    template: str
    """The template under `moarch_py/templates/`."""

    group: str
    """The group `moarch-py update <group>` refreshes together."""

    when: Callable[[ProjectOptions], bool] = _always

    extra: dict[str, str] = field(default_factory=dict)
    """Template variables only this file needs (a skill's name and description)."""

    def path_for(self, package: str) -> str:
        """The path in a project whose package is [package]."""
        return self.path.format(package=package)


# Skills the generated project ships: (slug, description). The description is
# what an agent matches a task against, so it says when to use the skill.
PROJECT_SKILLS: tuple[tuple[str, str], ...] = (
    (
        "add-module",
        "Add a new module to this moarch-py modular monolith — a business area with its own "
        "tables, endpoints and rules. Scaffolds every layer and its public.py with "
        "`moarch-py create module`, then fills in the model, schemas, repository, service, "
        "router, public interface, migration and tests. Use when asked to add a module, "
        "feature, resource, entity or endpoints for a new kind of data.",
    ),
    (
        "write-tests",
        "Write or update tests in this moarch-py FastAPI project: API tests through the "
        "async client and service tests against the in-memory database. Use when asked "
        "for tests, after adding an endpoint or a service rule, or when a test fails.",
    ),
    (
        "fix-bug",
        "Find and fix a bug in this moarch-py FastAPI project by reproducing it first: "
        "find the layer that owns the symptom, write a test that fails because of it, "
        "fix the cause there and keep the test. Use when something is broken, returns "
        "the wrong status or data, raises, or fails for a reason that is not obvious.",
    ),
    (
        "review",
        "Review a change in this moarch-py FastAPI project against its architecture rules "
        "(layers, transactions, schemas, errors, settings, migrations) and report every "
        "violation with file and line. Use when asked to review a diff, a branch or a "
        "PR, and before calling your own change done.",
    ),
    (
        "make-readable",
        "Make code in this moarch-py FastAPI project easier to read without changing what "
        "it does: names that say what a variable, function or class is, functions that "
        "do one thing, and comments that explain why wherever the logic is not obvious. "
        "Use when asked to clean up, clarify, rename, document or comment code, or when "
        "code is hard to follow.",
    ),
    (
        "explain",
        "Explain what code in this moarch-py FastAPI project does, step by step, and teach "
        "the Python, FastAPI, SQLAlchemy and Pydantic behind it with the project's own "
        "code as the example: traces a request through every layer, names each concept "
        "with a short explanation and a link to the official docs, and ends with a way "
        "to see it happen. Use when asked how something works, why it is written that "
        "way, what happens when…, or to learn the stack.",
    ),
)


def _migrations(options: ProjectOptions) -> bool:
    return options.migrations


def _docker(options: ProjectOptions) -> bool:
    return options.docker


def _ci(options: ProjectOptions) -> bool:
    return options.ci


def _pre_commit(options: ProjectOptions) -> bool:
    return options.pre_commit


def _ai(options: ProjectOptions) -> bool:
    return options.ai


def _skill_context(slug: str, description: str) -> dict[str, str]:
    return {"skill_name": f"moarch-{slug}", "skill_description": description}


_PKG = "src/{package}"

CATALOG: tuple[ScaffoldSpec, ...] = (
    # ── project root ──────────────────────────────────────────────────────
    ScaffoldSpec("readme", "README.md", "project/README.md.j2", "docs"),
    ScaffoldSpec("gitignore", ".gitignore", "project/gitignore.j2", "config"),
    ScaffoldSpec("python-version", ".python-version", "project/python-version.j2", "config"),
    ScaffoldSpec("env-example", ".env.example", "project/env.example.j2", "config"),
    ScaffoldSpec("architecture", "docs/ARCHITECTURE.md", "project/ARCHITECTURE.md.j2", "docs"),
    # ── application package ───────────────────────────────────────────────
    ScaffoldSpec("package", f"{_PKG}/__init__.py", "app/package_init.py.j2", "core"),
    ScaffoldSpec("main", f"{_PKG}/main.py", "app/main.py.j2", "core"),
    ScaffoldSpec("core", f"{_PKG}/core/__init__.py", "app/empty_init.py.j2", "core"),
    ScaffoldSpec("config", f"{_PKG}/core/config.py", "app/core/config.py.j2", "core"),
    ScaffoldSpec("logging", f"{_PKG}/core/logging.py", "app/core/logging.py.j2", "core"),
    ScaffoldSpec("errors", f"{_PKG}/core/errors.py", "app/core/errors.py.j2", "core"),
    ScaffoldSpec("db", f"{_PKG}/db/__init__.py", "app/empty_init.py.j2", "db"),
    ScaffoldSpec("db-base", f"{_PKG}/db/base.py", "app/db/base.py.j2", "db"),
    ScaffoldSpec("db-session", f"{_PKG}/db/session.py", "app/db/session.py.j2", "db"),
    ScaffoldSpec("db-repository", f"{_PKG}/db/repository.py", "app/db/repository.py.j2", "db"),
    ScaffoldSpec("db-models", f"{_PKG}/db/models.py", "app/db/models.py.j2", "db"),
    ScaffoldSpec("api", f"{_PKG}/api/__init__.py", "app/empty_init.py.j2", "api"),
    ScaffoldSpec("health", f"{_PKG}/api/health.py", "app/api/health.py.j2", "api"),
    ScaffoldSpec("api-v1", f"{_PKG}/api/v1/__init__.py", "app/empty_init.py.j2", "api"),
    ScaffoldSpec("api-v1-router", f"{_PKG}/api/v1/router.py", "app/api/v1/router.py.j2", "api"),
    ScaffoldSpec("modules", f"{_PKG}/modules/__init__.py", "app/modules_init.py.j2", "api"),
    ScaffoldSpec("py-typed", f"{_PKG}/py.typed", "app/py.typed.j2", "core"),
    # ── tests ─────────────────────────────────────────────────────────────
    ScaffoldSpec("conftest", "tests/conftest.py", "tests/conftest.py.j2", "tests"),
    ScaffoldSpec("test-health", "tests/test_health.py", "tests/test_health.py.j2", "tests"),
    # ── migrations ────────────────────────────────────────────────────────
    ScaffoldSpec(
        "alembic-ini", "alembic.ini", "migrations/alembic.ini.j2", "migrations", _migrations
    ),
    ScaffoldSpec(
        "alembic-env", "migrations/env.py", "migrations/env.py.j2", "migrations", _migrations
    ),
    ScaffoldSpec(
        "alembic-script",
        "migrations/script.py.mako",
        "migrations/script.py.mako.j2",
        "migrations",
        _migrations,
    ),
    ScaffoldSpec(
        "alembic-versions",
        "migrations/versions/.gitkeep",
        "app/py.typed.j2",
        "migrations",
        _migrations,
    ),
    # ── docker ────────────────────────────────────────────────────────────
    ScaffoldSpec("dockerfile", "Dockerfile", "docker/Dockerfile.j2", "docker", _docker),
    ScaffoldSpec("dockerignore", ".dockerignore", "docker/dockerignore.j2", "docker", _docker),
    ScaffoldSpec(
        "compose", "docker-compose.yml", "docker/docker-compose.yml.j2", "docker", _docker
    ),
    # ── quality ───────────────────────────────────────────────────────────
    ScaffoldSpec("ci", ".github/workflows/ci.yml", "ci/ci.yml.j2", "ci", _ci),
    ScaffoldSpec(
        "pre-commit", ".pre-commit-config.yaml", "ci/pre-commit-config.yaml.j2", "ci", _pre_commit
    ),
    # ── editor: ruff as the formatter and linter on save ──────────────────
    ScaffoldSpec(
        "vscode-settings", ".vscode/settings.json", "editor/vscode-settings.json.j2", "editor"
    ),
    ScaffoldSpec(
        "vscode-extensions", ".vscode/extensions.json", "editor/vscode-extensions.json.j2", "editor"
    ),
    # ── AI agent guide ────────────────────────────────────────────────────
    ScaffoldSpec("agents", "AGENTS.md", "ai/AGENTS.md.j2", "ai", _ai),
    ScaffoldSpec("claude-md", "CLAUDE.md", "ai/CLAUDE.md.j2", "ai", _ai),
    ScaffoldSpec(
        "claude-settings", ".claude/settings.json", "ai/claude-settings.json.j2", "ai", _ai
    ),
    *(
        ScaffoldSpec(
            f"skill-{slug}",
            f".agents/skills/moarch-{slug}/SKILL.md",
            f"ai/skills/{slug}.md.j2",
            "ai",
            _ai,
            _skill_context(slug, description),
        )
        for slug, description in PROJECT_SKILLS
    ),
    *(
        ScaffoldSpec(
            f"claude-skill-{slug}",
            f".claude/skills/moarch-{slug}/SKILL.md",
            "ai/claude_skill.md.j2",
            "ai",
            _ai,
            _skill_context(slug, description),
        )
        for slug, description in PROJECT_SKILLS
    ),
)


def specs_for(options: ProjectOptions) -> list[ScaffoldSpec]:
    """The catalog entries that belong in a project with [options]."""
    return [spec for spec in CATALOG if spec.when(options)]

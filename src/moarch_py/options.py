"""What a project can be generated with: the `init` checklist and its answers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from moarch_py.naming import ProjectName


class Database(StrEnum):
    """The database engines a project can run on, all through SQLAlchemy async."""

    POSTGRES = "postgres"
    MYSQL = "mysql"
    SQLITE = "sqlite"

    @property
    def label(self) -> str:
        """The name shown in the wizard."""
        return {
            Database.POSTGRES: "PostgreSQL (asyncpg)",
            Database.MYSQL: "MySQL / MariaDB (aiomysql)",
            Database.SQLITE: "SQLite (aiosqlite) — no server, good for prototypes",
        }[self]

    @property
    def driver_package(self) -> str:
        """The async DB-API driver SQLAlchemy needs for this engine."""
        return {
            Database.POSTGRES: "asyncpg",
            Database.MYSQL: "aiomysql",
            Database.SQLITE: "aiosqlite",
        }[self]

    @property
    def runs_in_container(self) -> bool:
        """Whether docker-compose starts a server for it (SQLite is a file)."""
        return self is not Database.SQLITE

    def local_url(self, package: str) -> str:
        """The `DATABASE_URL` for a database on this machine, as in `.env.example`."""
        return {
            Database.POSTGRES: f"postgresql+asyncpg://postgres:postgres@localhost:5432/{package}",
            Database.MYSQL: f"mysql+aiomysql://app:app@localhost:3306/{package}",
            Database.SQLITE: f"sqlite+aiosqlite:///./{package}.db",
        }[self]

    def compose_url(self, package: str) -> str:
        """The `DATABASE_URL` inside docker-compose, where the host is the `db` service."""
        return self.local_url(package).replace("@localhost:", "@db:")


@dataclass(frozen=True)
class ChecklistOption:
    """One box in the `init` "What to generate" checklist."""

    key: str
    """The attribute on `ProjectOptions` and the name in `.moarch-py.yaml`."""

    label: str
    """What the wizard shows."""

    default: bool
    """Ticked when the wizard opens, and taken by `--all`."""


CHECKLIST: tuple[ChecklistOption, ...] = (
    ChecklistOption("migrations", "Migrations (Alembic)", default=True),
    ChecklistOption("docker", "Dockerfile + docker-compose", default=True),
    ChecklistOption("ci", "GitHub Actions CI (ruff, mypy, pytest)", default=True),
    ChecklistOption("pre_commit", "pre-commit hooks (ruff format + lint)", default=True),
    ChecklistOption("ai", "AI agent guide (AGENTS.md, CLAUDE.md, skills)", default=True),
)


@dataclass(frozen=True)
class ProjectOptions:
    """Every answer `init` collected; the only input the templates read."""

    name: ProjectName
    database: Database
    migrations: bool = True
    docker: bool = True
    ci: bool = True
    pre_commit: bool = True
    ai: bool = True

    @property
    def enabled(self) -> list[str]:
        """The checklist keys that are on, in checklist order, for `.moarch-py.yaml`."""
        return [option.key for option in CHECKLIST if getattr(self, option.key)]

    @classmethod
    def with_defaults(cls, name: ProjectName, database: Database) -> ProjectOptions:
        """The options `--all` takes: every checklist default."""
        return cls.from_checklist(name, database, {o.key for o in CHECKLIST if o.default})

    @classmethod
    def from_checklist(
        cls, name: ProjectName, database: Database, ticked: set[str]
    ) -> ProjectOptions:
        """Builds the options from the set of ticked checklist keys."""
        flags = {option.key: option.key in ticked for option in CHECKLIST}
        return cls(name=name, database=database, **flags)

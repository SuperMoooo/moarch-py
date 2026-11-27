"""What a project can be generated with: the `init` checklists and their answers."""

from __future__ import annotations

from dataclasses import dataclass, fields
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


class Broker(StrEnum):
    """The message server that carries background tasks from the API to the worker."""

    NONE = "none"
    RABBITMQ = "rabbitmq"
    REDIS = "redis"

    @property
    def label(self) -> str:
        """The name shown in the wizard."""
        return {
            Broker.NONE: "None — only FastAPI's in-process BackgroundTasks",
            Broker.RABBITMQ: "RabbitMQ (taskiq-aio-pika)",
            Broker.REDIS: "Redis (taskiq-redis)",
        }[self]

    @property
    def packages(self) -> list[str]:
        """What the worker needs installed for this broker."""
        return {
            Broker.NONE: [],
            Broker.RABBITMQ: ["taskiq", "taskiq-aio-pika"],
            Broker.REDIS: ["taskiq", "taskiq-redis"],
        }[self]

    @property
    def local_url(self) -> str:
        """The `BROKER_URL` for a broker on this machine."""
        return {
            Broker.NONE: "",
            Broker.RABBITMQ: "amqp://guest:guest@localhost:5672/",
            # Database 1, so tasks never share keys with the cache in database 0.
            Broker.REDIS: "redis://localhost:6379/1",
        }[self]

    @property
    def compose_url(self) -> str:
        """The `BROKER_URL` inside docker-compose, where the host is the service name."""
        return self.local_url.replace("localhost", self.value)


@dataclass(frozen=True)
class ChecklistOption:
    """One box in an `init` checklist."""

    key: str
    """The attribute on `ProjectOptions` and the name in `.moarch-py.yaml`."""

    label: str
    """What the wizard shows."""

    default: bool = False
    """Ticked when the wizard opens, and taken by `--all` (for a sub-option: once its lead is)."""

    needs: tuple[str, ...] = ()
    """Options it cannot work without; ticking it ticks them too, "(needed by …)"."""


@dataclass(frozen=True)
class Checklist:
    """One titled group of options the wizard asks together."""

    title: str
    options: tuple[ChecklistOption, ...]

    lead: str | None = None
    """An option asked first as yes/no; the others are only offered when it is yes."""


CHECKLISTS: tuple[Checklist, ...] = (
    Checklist(
        "What to generate",
        (
            ChecklistOption("migrations", "Migrations (Alembic)", default=True),
            ChecklistOption("docker", "Dockerfile + docker-compose", default=True),
            ChecklistOption("ci", "GitHub Actions CI (ruff, mypy, pytest)", default=True),
            ChecklistOption("pre_commit", "pre-commit hooks (ruff format + lint)", default=True),
            ChecklistOption("ai", "AI agent guide (AGENTS.md, CLAUDE.md, skills)", default=True),
        ),
    ),
    Checklist(
        "Auth",
        (
            ChecklistOption("auth", "Auth: users, register, login, access tokens"),
            ChecklistOption(
                "auth_refresh",
                "Refresh tokens (rotated, reuse revokes the session)",
                default=True,
                needs=("auth",),
            ),
            ChecklistOption("auth_google", "Google sign-in (ID token)", needs=("auth",)),
            ChecklistOption("auth_apple", "Apple sign-in (ID token)", needs=("auth",)),
        ),
        lead="auth",
    ),
    Checklist(
        "Security",
        (
            ChecklistOption("rate_limit", "Rate limiting per client (Redis)"),
            ChecklistOption("audit_log", "Audit log (append-only: who did what)"),
            ChecklistOption("idempotency", "Idempotency keys on writes"),
            ChecklistOption("security_headers", "Security headers + strict CORS"),
            ChecklistOption("lockout", "Account lockout after failed logins", needs=("auth",)),
            ChecklistOption("integrity", "Device integrity (Play Integrity, App Attest)"),
        ),
    ),
    Checklist(
        "Background & realtime",
        (
            ChecklistOption("scheduler", "Scheduled tasks (taskiq scheduler)"),
            ChecklistOption("websockets", "WebSockets (/ws, fan-out over Redis)"),
            ChecklistOption("sse", "Server-sent events (/events, fan-out over Redis)"),
        ),
    ),
    Checklist(
        "Services",
        (
            ChecklistOption("email", "Email (SMTP, Mailpit locally)"),
            ChecklistOption("cache", "Cache (Redis)"),
            ChecklistOption("storage", "File storage (local disk or S3-compatible)"),
            ChecklistOption("push", "Push notifications (FCM)", needs=("auth",)),
            ChecklistOption("moderation", "Report & block (store rules)", needs=("auth",)),
            ChecklistOption("purchases", "Purchases (store receipts verified)", needs=("auth",)),
        ),
    ),
    # Request IDs and structured logs are in every project; these send its
    # telemetry somewhere (docs/adr/0008).
    Checklist(
        "Observability",
        (
            ChecklistOption("tracing", "Tracing (OpenTelemetry, Grafana locally)"),
            ChecklistOption("sentry", "Error reporting (Sentry)"),
            ChecklistOption("metrics", "Metrics (Prometheus /metrics)"),
        ),
    ),
)

CHECKLIST: tuple[ChecklistOption, ...] = tuple(
    option for checklist in CHECKLISTS for option in checklist.options
)
"""Every option of every checklist, in wizard order."""

OPTIONS_BY_KEY: dict[str, ChecklistOption] = {option.key: option for option in CHECKLIST}


def default_keys() -> set[str]:
    """The options `--all` takes: each default, and a sub-option's only when its lead is."""
    ticked: set[str] = set()
    for checklist in CHECKLISTS:
        lead_is_default = checklist.lead is None or OPTIONS_BY_KEY[checklist.lead].default
        if lead_is_default:
            ticked.update(option.key for option in checklist.options if option.default)
    return ticked


def resolve_needs(ticked: set[str]) -> tuple[set[str], dict[str, list[str]]]:
    """[ticked] plus every option a ticked one needs, and why each was added.

    Returns (all ticked keys, needed key → the keys that needed it), so the
    wizard and `create` can say "auth (needed by lockout)".
    """
    resolved = set(ticked)
    needed_by: dict[str, list[str]] = {}
    pending = sorted(ticked)
    while pending:
        key = pending.pop()
        for need in OPTIONS_BY_KEY[key].needs:
            if need not in ticked:
                needed_by.setdefault(need, []).append(key)
            if need not in resolved:
                resolved.add(need)
                pending.append(need)
    return resolved, needed_by


class OptionsError(ValueError):
    """Raised for a combination of options that cannot work together."""


@dataclass(frozen=True)
class ProjectOptions:
    """Every answer `init` collected; the only input the templates read."""

    name: ProjectName
    database: Database
    broker: Broker = Broker.NONE
    # ── What to generate ──
    migrations: bool = True
    docker: bool = True
    ci: bool = True
    pre_commit: bool = True
    ai: bool = True
    # ── Auth ──
    auth: bool = False
    auth_refresh: bool = False
    auth_google: bool = False
    auth_apple: bool = False
    # ── Security ──
    rate_limit: bool = False
    audit_log: bool = False
    idempotency: bool = False
    security_headers: bool = False
    lockout: bool = False
    integrity: bool = False
    # ── Background & realtime ──
    scheduler: bool = False
    websockets: bool = False
    sse: bool = False
    # ── Services ──
    email: bool = False
    cache: bool = False
    storage: bool = False
    push: bool = False
    moderation: bool = False
    purchases: bool = False
    # ── Observability ──
    tracing: bool = False
    sentry: bool = False
    metrics: bool = False

    def __post_init__(self) -> None:
        missing = [
            f"{option.key} needs {need}"
            for option in CHECKLIST
            if getattr(self, option.key)
            for need in option.needs
            if not getattr(self, need)
        ]
        if self.scheduler and not self.has_worker:
            missing.append("scheduler needs a broker (rabbitmq or redis)")
        if missing:
            raise OptionsError("; ".join(missing))

    @property
    def enabled(self) -> list[str]:
        """The checklist keys that are on, in checklist order, for `.moarch-py.yaml`."""
        return [option.key for option in CHECKLIST if getattr(self, option.key)]

    @property
    def has_worker(self) -> bool:
        """A broker was chosen, so there is a worker process running tasks."""
        return self.broker is not Broker.NONE

    @property
    def uses_redis(self) -> bool:
        """Something keeps state in Redis, so the project gets one shared Redis.

        Rate limits and realtime fan-out must be shared by every instance of
        the API; in memory they would look right on one instance and quietly
        break on two (docs/adr/0005).
        """
        return (
            self.cache
            or self.rate_limit
            or self.websockets
            or self.sse
            or self.broker is Broker.REDIS
        )

    @property
    def uses_google_api(self) -> bool:
        """Something calls Google's APIs as the project's service account (FCM, Play)."""
        return self.push or self.integrity or self.purchases

    @property
    def realtime(self) -> bool:
        """WebSockets or server-sent events, which share the Redis broadcaster."""
        return self.websockets or self.sse

    @property
    def social_sign_in(self) -> bool:
        """Google or Apple sign-in, which share linked identities."""
        return self.auth_google or self.auth_apple

    @property
    def email_flows(self) -> bool:
        """Email verification and password reset: auth that can send email."""
        return self.auth and self.email

    @property
    def any_security(self) -> bool:
        """At least one Security option, so docs/SECURITY.md exists."""
        return (
            self.rate_limit
            or self.audit_log
            or self.idempotency
            or self.security_headers
            or self.lockout
            or self.integrity
        )

    @property
    def any_service(self) -> bool:
        """At least one Services option, so docs/SERVICES.md exists."""
        return (
            self.email
            or self.cache
            or self.storage
            or self.push
            or self.moderation
            or self.purchases
        )

    @property
    def traces_tasks(self) -> bool:
        """Tracing with a worker: a task's spans join the trace of the request that sent it."""
        return self.tracing and self.has_worker

    @property
    def local_telemetry(self) -> bool:
        """Tracing with Docker: docker-compose runs Grafana's otel-lgtm to look at it."""
        return self.tracing and self.docker

    def with_added(self, keys: set[str], *, broker: Broker | None = None) -> ProjectOptions:
        """These options plus [keys] (and what they need), for `create <thing>`."""
        ticked, _ = resolve_needs({*self.enabled, *keys})
        flags = {option.key: option.key in ticked for option in CHECKLIST}
        return ProjectOptions(
            name=self.name, database=self.database, broker=broker or self.broker, **flags
        )

    @classmethod
    def with_defaults(cls, name: ProjectName, database: Database) -> ProjectOptions:
        """The options `--all` takes: every checklist default."""
        return cls.from_checklist(name, database, default_keys())

    @classmethod
    def from_checklist(
        cls,
        name: ProjectName,
        database: Database,
        ticked: set[str],
        *,
        broker: Broker = Broker.NONE,
    ) -> ProjectOptions:
        """Builds the options from the ticked checklist keys, adding what they need."""
        resolved, _ = resolve_needs(ticked)
        flags = {option.key: option.key in resolved for option in CHECKLIST}
        return cls(name=name, database=database, broker=broker, **flags)


def option_field_names() -> set[str]:
    """Every boolean option field on `ProjectOptions`; tests check it matches CHECKLIST."""
    return {field.name for field in fields(ProjectOptions) if field.type in ("bool", bool)}

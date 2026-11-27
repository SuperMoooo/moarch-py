"""What each checklist option beyond "What to generate" writes: its files and its anchor snippets.

Read it option by option. Each block lists the files the option owns
(`_file`) and the snippets it adds to shared files (`_insert`). A file an
option owns is rendered once, when the option is added; anything that
depends on a *second* option is a snippet of that combination (auth with
email, auth with the audit log…), so adding either one first, or both at
`init`, ends with the same project (docs/adr/0006).
"""

from __future__ import annotations

from collections.abc import Callable

from moarch_py.options import Broker, ProjectOptions
from moarch_py.specs import AnchorInsert, ScaffoldSpec

Predicate = Callable[[ProjectOptions], bool]


def _on(*names: str) -> Predicate:
    """True when every named option (a field or a property of ProjectOptions) is on."""

    def predicate(options: ProjectOptions) -> bool:
        return all(getattr(options, name) for name in names)

    return predicate


def _broker_is(broker: Broker) -> Predicate:
    def predicate(options: ProjectOptions) -> bool:
        return options.broker is broker

    return predicate


def _file(slug: str, path: str, template: str, group: str, when: Predicate) -> ScaffoldSpec:
    return ScaffoldSpec(slug, path, template, group, when)


def _insert(
    slug: str,
    path: str,
    anchor: str,
    when: Predicate,
    *,
    template: str | None = None,
    text: str | None = None,
) -> AnchorInsert:
    return AnchorInsert(slug, path, anchor, when, template=template, text=text)


# ── shared files every option may add to ──────────────────────────────────
_PKG = "src/{package}"
_MAIN = f"{_PKG}/main.py"
_CONFIG = f"{_PKG}/core/config.py"
_ROUTER = f"{_PKG}/api/v1/router.py"
_REGISTRY = f"{_PKG}/db/models.py"
_ENV = ".env.example"
_COMPOSE = "docker-compose.yml"
_CONFTEST = "tests/conftest.py"
_README = "README.md"
_AGENTS = "AGENTS.md"
_LOGGING = f"{_PKG}/core/logging.py"
_HEALTH = f"{_PKG}/api/health.py"
_REQUEST_ID = f"{_PKG}/core/request_id.py"
_BROKER = f"{_PKG}/worker/broker.py"
_OBSERVABILITY_GUIDE = "docs/OBSERVABILITY.md"
_PROMETHEUS = "docker/prometheus.yaml"
_USERS = f"{_PKG}/modules/users"
_USERS_TESTS = "tests/modules/users"
_AUDIT = f"{_PKG}/modules/audit"

_REDIS = _on("uses_redis")
_AUTH = _on("auth")
_REFRESH = _on("auth_refresh")
_GOOGLE = _on("auth_google")
_APPLE = _on("auth_apple")
_SOCIAL = _on("social_sign_in")
_EMAIL_FLOWS = _on("email_flows")
_LOCKOUT = _on("lockout")
_AUDIT_LOG = _on("audit_log")
_RATE_LIMIT = _on("rate_limit")
_IDEMPOTENCY = _on("idempotency")
_HEADERS = _on("security_headers")
_SECURITY = _on("any_security")
_WORKER = _on("has_worker")
_SCHEDULER = _on("scheduler")
_REALTIME = _on("realtime")
_WEBSOCKETS = _on("websockets")
_SSE = _on("sse")
_EMAIL = _on("email")
_CACHE = _on("cache")
_STORAGE = _on("storage")
_PUSH = _on("push")
_TRACING = _on("tracing")
_SENTRY = _on("sentry")
_METRICS = _on("metrics")
_TRACES_TASKS = _on("traces_tasks")
_LOCAL_TELEMETRY = _on("local_telemetry")
_SERVICES = _on("any_service")
_GOOGLE_API = _on("uses_google_api")
_INTEGRITY = _on("integrity")
_MODERATION = _on("moderation")
_PURCHASES = _on("purchases")

_IMPORT = "from {{ name.package }}"

OPTION_SPECS: tuple[ScaffoldSpec, ...] = (
    # ── Redis, shared by everything that keeps state across instances ──
    _file("redis", f"{_PKG}/core/redis.py", "redis/redis.py.j2", "core", _REDIS),
    # ── Auth: the users module ──
    _file("users", f"{_USERS}/__init__.py", "auth/init.py.j2", "auth", _AUTH),
    _file("users-public", f"{_USERS}/public.py", "auth/public.py.j2", "auth", _AUTH),
    _file("users-models", f"{_USERS}/models.py", "auth/models.py.j2", "auth", _AUTH),
    _file("users-schemas", f"{_USERS}/schemas.py", "auth/schemas.py.j2", "auth", _AUTH),
    _file("users-repository", f"{_USERS}/repository.py", "auth/repository.py.j2", "auth", _AUTH),
    _file("users-passwords", f"{_USERS}/passwords.py", "auth/passwords.py.j2", "auth", _AUTH),
    _file("users-tokens", f"{_USERS}/tokens.py", "auth/tokens.py.j2", "auth", _AUTH),
    _file("users-parts", f"{_USERS}/parts.py", "auth/parts.py.j2", "auth", _AUTH),
    _file("users-service", f"{_USERS}/service.py", "auth/service.py.j2", "auth", _AUTH),
    _file(
        "users-dependencies", f"{_USERS}/dependencies.py", "auth/dependencies.py.j2", "auth", _AUTH
    ),
    _file("users-router", f"{_USERS}/router.py", "auth/router.py.j2", "auth", _AUTH),
    _file(
        "test-auth-api",
        f"{_USERS_TESTS}/test_auth_api.py",
        "auth/test_auth_api.py.j2",
        "auth",
        _AUTH,
    ),
    _file(
        "test-passwords",
        f"{_USERS_TESTS}/test_passwords.py",
        "auth/test_passwords.py.j2",
        "auth",
        _AUTH,
    ),
    _file("auth-guide", "docs/AUTH.md", "auth/AUTH.md.j2", "docs", _AUTH),
    # ── Refresh tokens ──
    _file(
        "users-refresh-tokens",
        f"{_USERS}/refresh_tokens.py",
        "auth/refresh_tokens.py.j2",
        "auth",
        _REFRESH,
    ),
    _file(
        "users-refresh-router",
        f"{_USERS}/refresh_router.py",
        "auth/refresh_router.py.j2",
        "auth",
        _REFRESH,
    ),
    _file(
        "test-refresh-tokens",
        f"{_USERS_TESTS}/test_refresh_tokens.py",
        "auth/test_refresh_tokens.py.j2",
        "auth",
        _REFRESH,
    ),
    # ── Google and Apple sign-in ──
    _file(
        "users-social", f"{_USERS}/social_sign_in.py", "auth/social_sign_in.py.j2", "auth", _SOCIAL
    ),
    _file(
        "test-social",
        f"{_USERS_TESTS}/test_social_sign_in.py",
        "auth/test_social_sign_in.py.j2",
        "auth",
        _SOCIAL,
    ),
    _file(
        "users-google", f"{_USERS}/google_sign_in.py", "auth/google_sign_in.py.j2", "auth", _GOOGLE
    ),
    _file(
        "test-google",
        f"{_USERS_TESTS}/test_google_sign_in.py",
        "auth/test_google_sign_in.py.j2",
        "auth",
        _GOOGLE,
    ),
    _file("users-apple", f"{_USERS}/apple_sign_in.py", "auth/apple_sign_in.py.j2", "auth", _APPLE),
    _file(
        "test-apple",
        f"{_USERS_TESTS}/test_apple_sign_in.py",
        "auth/test_apple_sign_in.py.j2",
        "auth",
        _APPLE,
    ),
    # ── Email verification and password reset (auth + email) ──
    _file(
        "users-email-verification",
        f"{_USERS}/email_verification.py",
        "auth/email_verification.py.j2",
        "auth",
        _EMAIL_FLOWS,
    ),
    _file(
        "users-email-flows",
        f"{_USERS}/email_flows.py",
        "auth/email_flows.py.j2",
        "auth",
        _EMAIL_FLOWS,
    ),
    _file(
        "users-email-router",
        f"{_USERS}/email_router.py",
        "auth/email_router.py.j2",
        "auth",
        _EMAIL_FLOWS,
    ),
    _file(
        "test-email-flows",
        f"{_USERS_TESTS}/test_email_flows.py",
        "auth/test_email_flows.py.j2",
        "auth",
        _EMAIL_FLOWS,
    ),
    # ── Lockout ──
    _file("users-lockout", f"{_USERS}/lockout.py", "auth/lockout.py.j2", "security", _LOCKOUT),
    _file(
        "test-lockout",
        f"{_USERS_TESTS}/test_lockout.py",
        "auth/test_lockout.py.j2",
        "security",
        _LOCKOUT,
    ),
    # ── Audit log: its own module ──
    _file("audit", f"{_AUDIT}/__init__.py", "audit/init.py.j2", "security", _AUDIT_LOG),
    _file("audit-public", f"{_AUDIT}/public.py", "audit/public.py.j2", "security", _AUDIT_LOG),
    _file("audit-models", f"{_AUDIT}/models.py", "audit/models.py.j2", "security", _AUDIT_LOG),
    _file("audit-schemas", f"{_AUDIT}/schemas.py", "audit/schemas.py.j2", "security", _AUDIT_LOG),
    _file(
        "audit-repository",
        f"{_AUDIT}/repository.py",
        "audit/repository.py.j2",
        "security",
        _AUDIT_LOG,
    ),
    _file(
        "test-audit",
        "tests/modules/audit/test_audit_public.py",
        "audit/test_audit_public.py.j2",
        "security",
        _AUDIT_LOG,
    ),
    _file(
        "users-audit-events",
        f"{_USERS}/audit_events.py",
        "auth/audit_events.py.j2",
        "security",
        _on("auth", "audit_log"),
    ),
    # ── Rate limiting, idempotency, security headers ──
    _file(
        "rate-limit",
        f"{_PKG}/core/rate_limit.py",
        "security/rate_limit.py.j2",
        "security",
        _RATE_LIMIT,
    ),
    _file(
        "test-rate-limit",
        "tests/test_rate_limit.py",
        "security/test_rate_limit.py.j2",
        "security",
        _RATE_LIMIT,
    ),
    _file(
        "idempotency",
        f"{_PKG}/core/idempotency.py",
        "security/idempotency.py.j2",
        "security",
        _IDEMPOTENCY,
    ),
    _file(
        "test-idempotency",
        "tests/test_idempotency.py",
        "security/test_idempotency.py.j2",
        "security",
        _IDEMPOTENCY,
    ),
    _file(
        "security-headers",
        f"{_PKG}/core/security_headers.py",
        "security/security_headers.py.j2",
        "security",
        _HEADERS,
    ),
    _file(
        "test-security-headers",
        "tests/test_security_headers.py",
        "security/test_security_headers.py.j2",
        "security",
        _HEADERS,
    ),
    _file("security-guide", "docs/SECURITY.md", "security/SECURITY.md.j2", "docs", _SECURITY),
    # ── Background tasks ──
    _file("worker", f"{_PKG}/worker/__init__.py", "worker/init.py.j2", "worker", _WORKER),
    _file("worker-broker", f"{_PKG}/worker/broker.py", "worker/broker.py.j2", "worker", _WORKER),
    _file("worker-tasks", f"{_PKG}/worker/tasks.py", "worker/tasks.py.j2", "worker", _WORKER),
    _file(
        "worker-database",
        f"{_PKG}/worker/database.py",
        "worker/database.py.j2",
        "worker",
        _WORKER,
    ),
    _file("root-conftest", "conftest.py", "worker/root_conftest.py.j2", "worker", _WORKER),
    _file("test-tasks", "tests/test_tasks.py", "worker/test_tasks.py.j2", "worker", _WORKER),
    _file(
        "worker-scheduler",
        f"{_PKG}/worker/scheduler.py",
        "worker/scheduler.py.j2",
        "worker",
        _SCHEDULER,
    ),
    _file(
        "test-scheduler",
        "tests/test_scheduler.py",
        "worker/test_scheduler.py.j2",
        "worker",
        _SCHEDULER,
    ),
    _file("background-guide", "docs/BACKGROUND.md", "worker/BACKGROUND.md.j2", "docs", _WORKER),
    # ── Realtime ──
    _file("realtime", f"{_PKG}/realtime/__init__.py", "realtime/init.py.j2", "realtime", _REALTIME),
    _file(
        "realtime-broadcaster",
        f"{_PKG}/realtime/broadcaster.py",
        "realtime/broadcaster.py.j2",
        "realtime",
        _REALTIME,
    ),
    _file(
        "realtime-identity",
        f"{_PKG}/realtime/identity.py",
        "realtime/identity.py.j2",
        "realtime",
        _REALTIME,
    ),
    _file(
        "test-broadcaster",
        "tests/test_broadcaster.py",
        "realtime/test_broadcaster.py.j2",
        "realtime",
        _REALTIME,
    ),
    _file(
        "realtime-websockets",
        f"{_PKG}/realtime/websockets.py",
        "realtime/websockets.py.j2",
        "realtime",
        _WEBSOCKETS,
    ),
    _file(
        "test-websockets",
        "tests/test_websockets.py",
        "realtime/test_websockets.py.j2",
        "realtime",
        _WEBSOCKETS,
    ),
    _file(
        "realtime-events",
        f"{_PKG}/realtime/events.py",
        "realtime/events.py.j2",
        "realtime",
        _SSE,
    ),
    _file("test-events", "tests/test_events.py", "realtime/test_events.py.j2", "realtime", _SSE),
    _file("realtime-guide", "docs/REALTIME.md", "realtime/REALTIME.md.j2", "docs", _REALTIME),
    # ── Services ──
    _file("services", f"{_PKG}/services/__init__.py", "services/init.py.j2", "services", _SERVICES),
    _file("email", f"{_PKG}/services/email.py", "services/email.py.j2", "services", _EMAIL),
    _file("test-email", "tests/test_email.py", "services/test_email.py.j2", "services", _EMAIL),
    _file("cache", f"{_PKG}/services/cache.py", "services/cache.py.j2", "services", _CACHE),
    _file("test-cache", "tests/test_cache.py", "services/test_cache.py.j2", "services", _CACHE),
    _file("storage", f"{_PKG}/services/storage.py", "services/storage.py.j2", "services", _STORAGE),
    _file(
        "test-storage", "tests/test_storage.py", "services/test_storage.py.j2", "services", _STORAGE
    ),
    _file("users-push", f"{_USERS}/push.py", "services/push.py.j2", "services", _PUSH),
    _file(
        "test-push", f"{_USERS_TESTS}/test_push.py", "services/test_push.py.j2", "services", _PUSH
    ),
    _file("services-guide", "docs/SERVICES.md", "services/SERVICES.md.j2", "docs", _SERVICES),
    # ── Observability: where the telemetry goes (request IDs and logs are core) ──
    _file(
        "tracing",
        f"{_PKG}/core/tracing.py",
        "observability/tracing.py.j2",
        "observability",
        _TRACING,
    ),
    _file(
        "test-tracing",
        "tests/test_tracing.py",
        "observability/test_tracing.py.j2",
        "observability",
        _TRACING,
    ),
    _file(
        "prometheus-config",
        _PROMETHEUS,
        "observability/prometheus.yaml.j2",
        "observability",
        _LOCAL_TELEMETRY,
    ),
    _file(
        "sentry", f"{_PKG}/core/sentry.py", "observability/sentry.py.j2", "observability", _SENTRY
    ),
    _file(
        "metrics",
        f"{_PKG}/core/metrics.py",
        "observability/metrics.py.j2",
        "observability",
        _METRICS,
    ),
    _file(
        "test-metrics",
        "tests/test_metrics.py",
        "observability/test_metrics.py.j2",
        "observability",
        _METRICS,
    ),
    # ── Google's APIs as one service account: FCM, Play Integrity, Play billing ──
    _file(
        "google-service-account",
        f"{_PKG}/core/google_service_account.py",
        "google/service_account.py.j2",
        "core",
        _GOOGLE_API,
    ),
    _file(
        "test-google-service-account",
        "tests/test_google_service_account.py",
        "google/test_service_account.py.j2",
        "core",
        _GOOGLE_API,
    ),
    # ── Device integrity ──
    _file(
        "integrity",
        f"{_PKG}/modules/integrity/__init__.py",
        "integrity/init.py.j2",
        "security",
        _INTEGRITY,
    ),
    _file(
        "integrity-public",
        f"{_PKG}/modules/integrity/public.py",
        "integrity/public.py.j2",
        "security",
        _INTEGRITY,
    ),
    _file(
        "integrity-models",
        f"{_PKG}/modules/integrity/models.py",
        "integrity/models.py.j2",
        "security",
        _INTEGRITY,
    ),
    _file(
        "integrity-schemas",
        f"{_PKG}/modules/integrity/schemas.py",
        "integrity/schemas.py.j2",
        "security",
        _INTEGRITY,
    ),
    _file(
        "integrity-repository",
        f"{_PKG}/modules/integrity/repository.py",
        "integrity/repository.py.j2",
        "security",
        _INTEGRITY,
    ),
    _file(
        "integrity-service",
        f"{_PKG}/modules/integrity/service.py",
        "integrity/service.py.j2",
        "security",
        _INTEGRITY,
    ),
    _file(
        "integrity-dependencies",
        f"{_PKG}/modules/integrity/dependencies.py",
        "integrity/dependencies.py.j2",
        "security",
        _INTEGRITY,
    ),
    _file(
        "integrity-router",
        f"{_PKG}/modules/integrity/router.py",
        "integrity/router.py.j2",
        "security",
        _INTEGRITY,
    ),
    _file(
        "integrity-verifiers",
        f"{_PKG}/modules/integrity/verifiers.py",
        "integrity/verifiers.py.j2",
        "security",
        _INTEGRITY,
    ),
    _file(
        "test-integrity",
        "tests/modules/integrity/test_integrity_api.py",
        "integrity/test_integrity_api.py.j2",
        "security",
        _INTEGRITY,
    ),
    # ── Report & block ──
    _file(
        "moderation",
        f"{_PKG}/modules/moderation/__init__.py",
        "moderation/init.py.j2",
        "services",
        _MODERATION,
    ),
    _file(
        "moderation-public",
        f"{_PKG}/modules/moderation/public.py",
        "moderation/public.py.j2",
        "services",
        _MODERATION,
    ),
    _file(
        "moderation-models",
        f"{_PKG}/modules/moderation/models.py",
        "moderation/models.py.j2",
        "services",
        _MODERATION,
    ),
    _file(
        "moderation-schemas",
        f"{_PKG}/modules/moderation/schemas.py",
        "moderation/schemas.py.j2",
        "services",
        _MODERATION,
    ),
    _file(
        "moderation-repository",
        f"{_PKG}/modules/moderation/repository.py",
        "moderation/repository.py.j2",
        "services",
        _MODERATION,
    ),
    _file(
        "moderation-service",
        f"{_PKG}/modules/moderation/service.py",
        "moderation/service.py.j2",
        "services",
        _MODERATION,
    ),
    _file(
        "moderation-dependencies",
        f"{_PKG}/modules/moderation/dependencies.py",
        "moderation/dependencies.py.j2",
        "services",
        _MODERATION,
    ),
    _file(
        "moderation-router",
        f"{_PKG}/modules/moderation/router.py",
        "moderation/router.py.j2",
        "services",
        _MODERATION,
    ),
    _file(
        "test-moderation",
        "tests/modules/moderation/test_moderation_api.py",
        "moderation/test_moderation_api.py.j2",
        "services",
        _MODERATION,
    ),
    # ── Purchases ──
    _file(
        "purchases",
        f"{_PKG}/modules/purchases/__init__.py",
        "purchases/init.py.j2",
        "services",
        _PURCHASES,
    ),
    _file(
        "purchases-public",
        f"{_PKG}/modules/purchases/public.py",
        "purchases/public.py.j2",
        "services",
        _PURCHASES,
    ),
    _file(
        "purchases-models",
        f"{_PKG}/modules/purchases/models.py",
        "purchases/models.py.j2",
        "services",
        _PURCHASES,
    ),
    _file(
        "purchases-schemas",
        f"{_PKG}/modules/purchases/schemas.py",
        "purchases/schemas.py.j2",
        "services",
        _PURCHASES,
    ),
    _file(
        "purchases-repository",
        f"{_PKG}/modules/purchases/repository.py",
        "purchases/repository.py.j2",
        "services",
        _PURCHASES,
    ),
    _file(
        "purchases-service",
        f"{_PKG}/modules/purchases/service.py",
        "purchases/service.py.j2",
        "services",
        _PURCHASES,
    ),
    _file(
        "purchases-dependencies",
        f"{_PKG}/modules/purchases/dependencies.py",
        "purchases/dependencies.py.j2",
        "services",
        _PURCHASES,
    ),
    _file(
        "purchases-router",
        f"{_PKG}/modules/purchases/router.py",
        "purchases/router.py.j2",
        "services",
        _PURCHASES,
    ),
    _file(
        "purchases-verifiers",
        f"{_PKG}/modules/purchases/verifiers.py",
        "purchases/verifiers.py.j2",
        "services",
        _PURCHASES,
    ),
    _file(
        "test-purchases",
        "tests/modules/purchases/test_purchases_api.py",
        "purchases/test_purchases_api.py.j2",
        "services",
        _PURCHASES,
    ),
)


def _redis_inserts() -> tuple[AnchorInsert, ...]:
    return (
        _insert(
            "redis-settings",
            _CONFIG,
            "settings",
            _REDIS,
            text="# One Redis for the cache, rate limits, realtime fan-out (docs/adr/0005).\n"
            'redis_url: str = "redis://localhost:6379/0"',
        ),
        _insert(
            "redis-env",
            _ENV,
            "env",
            _REDIS,
            text="\n# Shared by the cache, rate limits and realtime fan-out.\n"
            "REDIS_URL=redis://localhost:6379/0",
        ),
        _insert(
            "redis-compose-env",
            _COMPOSE,
            "compose-environment",
            _REDIS,
            text="REDIS_URL: redis://redis:6379/0",
        ),
        _insert(
            "redis-compose-service",
            _COMPOSE,
            "compose-services",
            _REDIS,
            template="redis/compose.yml.j2",
        ),
        _insert(
            "redis-import",
            _MAIN,
            "main-imports",
            _REDIS,
            text=f"{_IMPORT}.core.redis import create_redis",
        ),
        _insert(
            "redis-state",
            _MAIN,
            "app-state",
            _REDIS,
            text="# One connection pool per process, shared by every request.\n"
            "app.state.redis = create_redis(settings)",
        ),
        _insert(
            "redis-shutdown",
            _MAIN,
            "shutdown",
            _REDIS,
            text="await running_app.state.redis.aclose()",
        ),
        _insert("redis-test-import", _CONFTEST, "test-imports", _REDIS, text="import fakeredis"),
        _insert(
            "redis-test-app",
            _CONFTEST,
            "test-app",
            _REDIS,
            text="# A Redis in memory, empty for every test: no server needed.\n"
            "test_app.state.redis = fakeredis.FakeAsyncRedis(server=fakeredis.FakeServer())",
        ),
    )


def _users_import(module: str, names: str) -> str:
    return f"{_IMPORT}.modules.users.{module} import {names}"


def _reexport(module: str, name: str) -> str:
    """An import public.py re-exports: the `X as X` form says so to mypy and ruff."""
    return _users_import(module, f"{name} as {name}")


def _auth_inserts() -> tuple[AnchorInsert, ...]:
    users_router = f"{_USERS}/router.py"
    users_models = f"{_USERS}/models.py"
    users_schemas = f"{_USERS}/schemas.py"
    users_repository = f"{_USERS}/repository.py"
    users_dependencies = f"{_USERS}/dependencies.py"
    users_public = f"{_USERS}/public.py"
    auth_guide = "docs/AUTH.md"
    return (
        # ── base auth ──
        _insert(
            "auth-router-import",
            _ROUTER,
            "router-imports",
            _AUTH,
            text=_users_import("router", "router as users_router"),
        ),
        _insert(
            "auth-router", _ROUTER, "routers", _AUTH, text="api_router.include_router(users_router)"
        ),
        _insert(
            "auth-registry",
            _REGISTRY,
            "models",
            _AUTH,
            text=_users_import("models", "DeviceToken, User") + "  # noqa: F401",
        ),
        _insert("auth-settings", _CONFIG, "settings", _AUTH, template="auth/insert/settings.py.j2"),
        _insert(
            "auth-settings-checks",
            _CONFIG,
            "settings-checks",
            _AUTH,
            template="auth/insert/settings_checks.py.j2",
        ),
        _insert("auth-env", _ENV, "env", _AUTH, template="auth/insert/env.j2"),
        _insert(
            "auth-fixtures", _CONFTEST, "fixtures", _AUTH, template="auth/insert/fixtures.py.j2"
        ),
        _insert(
            "auth-readme",
            _README,
            "guides",
            _AUTH,
            text="- [docs/AUTH.md](docs/AUTH.md): sign-in, tokens, protecting an endpoint",
        ),
        _insert(
            "auth-agents", _AGENTS, "agent-rules", _AUTH, template="auth/insert/agent_rules.md.j2"
        ),
        # ── refresh tokens ──
        _insert(
            "refresh-model",
            users_models,
            "module-models",
            _REFRESH,
            template="auth/insert/refresh_model.py.j2",
        ),
        _insert(
            "refresh-registry",
            _REGISTRY,
            "models",
            _REFRESH,
            text=_users_import("models", "RefreshToken") + "  # noqa: F401",
        ),
        _insert(
            "refresh-repository-import",
            users_repository,
            "repository-imports",
            _REFRESH,
            text="from datetime import datetime\n"
            "from sqlalchemy import update\n" + _users_import("models", "RefreshToken"),
        ),
        _insert(
            "refresh-repository",
            users_repository,
            "module-repositories",
            _REFRESH,
            template="auth/insert/refresh_repository.py.j2",
        ),
        _insert(
            "refresh-schemas",
            users_schemas,
            "module-schemas",
            _REFRESH,
            template="auth/insert/refresh_schemas.py.j2",
        ),
        _insert(
            "refresh-dependencies-import",
            users_dependencies,
            "parts-imports",
            _REFRESH,
            text=_users_import("refresh_tokens", "RefreshTokens")
            + "\n"
            + _users_import("repository", "RefreshTokenRepository"),
        ),
        _insert(
            "refresh-dependencies",
            users_dependencies,
            "auth-parts",
            _REFRESH,
            text="parts.refresh_tokens = RefreshTokens(RefreshTokenRepository(session), settings)",
        ),
        _insert(
            "refresh-router-import",
            users_router,
            "auth-router-imports",
            _REFRESH,
            text=_users_import("refresh_router", "router as refresh_router"),
        ),
        _insert(
            "refresh-router",
            users_router,
            "auth-routers",
            _REFRESH,
            text="router.include_router(refresh_router)",
        ),
        _insert(
            "refresh-public-import",
            users_public,
            "public-imports",
            _REFRESH,
            text=_reexport("refresh_tokens", "purge_expired_refresh_tokens"),
        ),
        _insert(
            "refresh-settings",
            _CONFIG,
            "settings",
            _REFRESH,
            text="# A refresh token is single-use; this is how long an unused one stays valid.\n"
            "refresh_token_days: int = 30",
        ),
        _insert("refresh-env", _ENV, "env", _REFRESH, text="REFRESH_TOKEN_DAYS=30"),
        _insert(
            "refresh-guide",
            auth_guide,
            "auth-guide",
            _REFRESH,
            template="auth/insert/guide_refresh.md.j2",
        ),
        # ── Google and Apple, through linked identities ──
        _insert(
            "social-model-import",
            users_models,
            "model-imports",
            _SOCIAL,
            text="from sqlalchemy import UniqueConstraint",
        ),
        _insert(
            "social-model",
            users_models,
            "module-models",
            _SOCIAL,
            template="auth/insert/social_model.py.j2",
        ),
        _insert(
            "social-registry",
            _REGISTRY,
            "models",
            _SOCIAL,
            text=_users_import("models", "LinkedIdentity") + "  # noqa: F401",
        ),
        _insert(
            "social-repository-import",
            users_repository,
            "repository-imports",
            _SOCIAL,
            text=_users_import("models", "LinkedIdentity"),
        ),
        _insert(
            "social-repository",
            users_repository,
            "module-repositories",
            _SOCIAL,
            template="auth/insert/social_repository.py.j2",
        ),
        _insert(
            "social-guide",
            auth_guide,
            "auth-guide",
            _SOCIAL,
            template="auth/insert/guide_social.md.j2",
        ),
        _insert(
            "google-schemas",
            users_schemas,
            "module-schemas",
            _GOOGLE,
            template="auth/insert/google_schemas.py.j2",
        ),
        _insert(
            "google-router-import",
            users_router,
            "auth-router-imports",
            _GOOGLE,
            text=_users_import("google_sign_in", "router as google_router"),
        ),
        _insert(
            "google-router",
            users_router,
            "auth-routers",
            _GOOGLE,
            text="router.include_router(google_router)",
        ),
        _insert(
            "google-settings",
            _CONFIG,
            "settings",
            _GOOGLE,
            text="# Every OAuth client ID your apps sign in with (iOS, Android, web): the\n"
            "# audiences a Google ID token may be issued for.\n"
            "google_client_ids: list[str] = []",
        ),
        _insert(
            "google-env",
            _ENV,
            "env",
            _GOOGLE,
            text="# JSON list of your Google OAuth client IDs.\nGOOGLE_CLIENT_IDS=[]",
        ),
        _insert(
            "apple-schemas",
            users_schemas,
            "module-schemas",
            _APPLE,
            template="auth/insert/apple_schemas.py.j2",
        ),
        _insert(
            "apple-router-import",
            users_router,
            "auth-router-imports",
            _APPLE,
            text=_users_import("apple_sign_in", "router as apple_router"),
        ),
        _insert(
            "apple-router",
            users_router,
            "auth-routers",
            _APPLE,
            text="router.include_router(apple_router)",
        ),
        _insert(
            "apple-settings",
            _CONFIG,
            "settings",
            _APPLE,
            text="# Your app's bundle ID (and Services ID for the web): the audiences an\n"
            "# Apple identity token may be issued for.\n"
            "apple_client_ids: list[str] = []",
        ),
        _insert(
            "apple-env",
            _ENV,
            "env",
            _APPLE,
            text="# JSON list of your app's bundle ID and Services ID.\nAPPLE_CLIENT_IDS=[]",
        ),
        # ── email verification and password reset ──
        _insert(
            "email-flows-model",
            users_models,
            "module-models",
            _EMAIL_FLOWS,
            template="auth/insert/email_model.py.j2",
        ),
        _insert(
            "email-flows-registry",
            _REGISTRY,
            "models",
            _EMAIL_FLOWS,
            text=_users_import("models", "EmailCode") + "  # noqa: F401",
        ),
        _insert(
            "email-flows-repository-import",
            users_repository,
            "repository-imports",
            _EMAIL_FLOWS,
            text=_users_import("models", "EmailCode"),
        ),
        _insert(
            "email-flows-repository",
            users_repository,
            "module-repositories",
            _EMAIL_FLOWS,
            template="auth/insert/email_repository.py.j2",
        ),
        _insert(
            "email-flows-schemas",
            users_schemas,
            "module-schemas",
            _EMAIL_FLOWS,
            template="auth/insert/email_schemas.py.j2",
        ),
        _insert(
            "email-flows-dependencies-import",
            users_dependencies,
            "parts-imports",
            _EMAIL_FLOWS,
            text=_users_import("email_verification", "EmailVerification")
            + "\n"
            + _users_import("repository", "EmailCodeRepository")
            + f"\n{_IMPORT}.services.email import EmailSender",
        ),
        _insert(
            "email-flows-dependencies",
            users_dependencies,
            "auth-parts",
            _EMAIL_FLOWS,
            template="auth/insert/email_dependencies.py.j2",
        ),
        _insert(
            "email-flows-router-import",
            users_router,
            "auth-router-imports",
            _EMAIL_FLOWS,
            text=_users_import("email_router", "router as email_router"),
        ),
        _insert(
            "email-flows-router",
            users_router,
            "auth-routers",
            _EMAIL_FLOWS,
            text="router.include_router(email_router)",
        ),
        _insert(
            "email-flows-public-import",
            users_public,
            "public-imports",
            _EMAIL_FLOWS,
            text=_reexport("email_flows", "CurrentVerifiedUser"),
        ),
        _insert(
            "email-flows-settings",
            _CONFIG,
            "settings",
            _EMAIL_FLOWS,
            template="auth/insert/email_settings.py.j2",
        ),
        _insert("email-flows-env", _ENV, "env", _EMAIL_FLOWS, template="auth/insert/email_env.j2"),
        _insert(
            "email-flows-guide",
            auth_guide,
            "auth-guide",
            _EMAIL_FLOWS,
            template="auth/insert/guide_email.md.j2",
        ),
        # ── lockout ──
        _insert(
            "lockout-model",
            users_models,
            "module-models",
            _LOCKOUT,
            template="auth/insert/lockout_model.py.j2",
        ),
        _insert(
            "lockout-model-import",
            users_models,
            "model-imports",
            _LOCKOUT,
            text="from sqlalchemy import UniqueConstraint",
        ),
        _insert(
            "lockout-registry",
            _REGISTRY,
            "models",
            _LOCKOUT,
            text=_users_import("models", "LoginFailure") + "  # noqa: F401",
        ),
        _insert(
            "lockout-repository-import",
            users_repository,
            "repository-imports",
            _LOCKOUT,
            text=_users_import("models", "LoginFailure"),
        ),
        _insert(
            "lockout-repository",
            users_repository,
            "module-repositories",
            _LOCKOUT,
            template="auth/insert/lockout_repository.py.j2",
        ),
        _insert(
            "lockout-dependencies-import",
            users_dependencies,
            "parts-imports",
            _LOCKOUT,
            text=_users_import("lockout", "DatabaseLockout")
            + "\n"
            + _users_import("repository", "LoginFailureRepository"),
        ),
        _insert(
            "lockout-dependencies",
            users_dependencies,
            "auth-parts",
            _LOCKOUT,
            text="parts.lockout = DatabaseLockout(LoginFailureRepository(session), settings)",
        ),
        _insert(
            "lockout-settings",
            _CONFIG,
            "settings",
            _LOCKOUT,
            text="# Wrong passwords in a row from one client (IP) that lock it out for a while,\n"
            "# and wrong passwords from all clients within a window that lock the account.\n"
            "lockout_max_failures: int = 5\n"
            "lockout_minutes: int = 15\n"
            "lockout_account_max_failures: int = 50\n"
            "lockout_account_window_minutes: int = 60",
        ),
        _insert(
            "lockout-env",
            _ENV,
            "env",
            _LOCKOUT,
            text="LOCKOUT_MAX_FAILURES=5\nLOCKOUT_MINUTES=15\n"
            "LOCKOUT_ACCOUNT_MAX_FAILURES=50\nLOCKOUT_ACCOUNT_WINDOW_MINUTES=60",
        ),
        # ── auth events in the audit log ──
        _insert(
            "audit-events-dependencies-import",
            users_dependencies,
            "parts-imports",
            _on("auth", "audit_log"),
            text=_users_import("audit_events", "AuditLogRecorder"),
        ),
        _insert(
            "audit-events-dependencies",
            users_dependencies,
            "auth-parts",
            _on("auth", "audit_log"),
            text="parts.events.append(AuditLogRecorder(session))",
        ),
        # ── push notifications, to a user's devices ──
        _insert(
            "push-public-import",
            users_public,
            "public-imports",
            _PUSH,
            text=_reexport("push", "PushNotification")
            + "\n"
            + _reexport("push", "PushNotifierDep"),
        ),
        _insert(
            "push-import",
            _MAIN,
            "main-imports",
            _PUSH,
            text=_users_import("push", "build_push_sender"),
        ),
        _insert(
            "push-state",
            _MAIN,
            "app-state",
            _PUSH,
            text="app.state.push_sender = build_push_sender(settings)",
        ),
        _insert(
            "google-api-settings",
            _CONFIG,
            "settings",
            _GOOGLE_API,
            text="# The Google service account's JSON key file, for FCM and Google Play's APIs;\n"
            "# and the Android app's package name, which Play Integrity and Play billing check.\n"
            'google_service_account_file: str = ""\n'
            'android_package_name: str = ""',
        ),
        _insert(
            "google-api-env",
            _ENV,
            "env",
            _GOOGLE_API,
            text="\n# Google service account key (JSON), for FCM and Google Play. Empty: off.\n"
            "GOOGLE_SERVICE_ACCOUNT_FILE=\nANDROID_PACKAGE_NAME=",
        ),
    )


def _security_inserts() -> tuple[AnchorInsert, ...]:
    guide = "docs/SECURITY.md"
    return (
        _insert(
            "security-readme",
            _README,
            "guides",
            _SECURITY,
            text="- [docs/SECURITY.md](docs/SECURITY.md): rate limits, audit log, idempotency, "
            "headers, lockout",
        ),
        # ── rate limiting ──
        _insert(
            "rate-limit-import",
            _MAIN,
            "main-imports",
            _RATE_LIMIT,
            text=f"{_IMPORT}.core.rate_limit import RateLimitMiddleware",
        ),
        _insert(
            "rate-limit-middleware",
            _MAIN,
            "middleware",
            _RATE_LIMIT,
            text="app.add_middleware(RateLimitMiddleware, settings=settings)",
        ),
        _insert(
            "rate-limit-settings",
            _CONFIG,
            "settings",
            _RATE_LIMIT,
            text="# Requests per minute from one client: sign-in paths, and everything else.\n"
            "rate_limit_auth_per_minute: int = 10\n"
            "rate_limit_default_per_minute: int = 120",
        ),
        _insert(
            "rate-limit-env",
            _ENV,
            "env",
            _RATE_LIMIT,
            text="\nRATE_LIMIT_AUTH_PER_MINUTE=10\nRATE_LIMIT_DEFAULT_PER_MINUTE=120",
        ),
        _insert(
            "rate-limit-guide",
            guide,
            "security-guide",
            _RATE_LIMIT,
            template="security/insert/guide_rate_limit.md.j2",
        ),
        # ── audit log ──
        _insert(
            "audit-registry",
            _REGISTRY,
            "models",
            _AUDIT_LOG,
            text=f"{_IMPORT}.modules.audit.models import AuditEvent  # noqa: F401",
        ),
        _insert(
            "audit-guide",
            guide,
            "security-guide",
            _AUDIT_LOG,
            template="security/insert/guide_audit_log.md.j2",
        ),
        _insert(
            "audit-agents",
            _AGENTS,
            "agent-rules",
            _AUDIT_LOG,
            text="- **Record what matters in the audit log.** A service that approves, moves "
            "money or changes who may do what calls `record_audit_event` from "
            "`modules/audit/public.py` in the same unit of work. The log is append-only: "
            "never update or delete its rows.",
        ),
        # ── idempotency ──
        _insert(
            "idempotency-registry",
            _REGISTRY,
            "models",
            _IDEMPOTENCY,
            text=f"{_IMPORT}.core.idempotency import IdempotencyRecord  # noqa: F401",
        ),
        _insert(
            "idempotency-import",
            _MAIN,
            "main-imports",
            _IDEMPOTENCY,
            text=f"{_IMPORT}.core.idempotency import IdempotencyMiddleware",
        ),
        _insert(
            "idempotency-middleware",
            _MAIN,
            "middleware",
            _IDEMPOTENCY,
            text="app.add_middleware(IdempotencyMiddleware)",
        ),
        _insert(
            "idempotency-guide",
            guide,
            "security-guide",
            _IDEMPOTENCY,
            template="security/insert/guide_idempotency.md.j2",
        ),
        # ── security headers and strict CORS ──
        _insert(
            "headers-import",
            _MAIN,
            "main-imports",
            _HEADERS,
            text=f"{_IMPORT}.core.security_headers import SecurityHeadersMiddleware",
        ),
        _insert(
            "headers-middleware",
            _MAIN,
            "middleware",
            _HEADERS,
            text="app.add_middleware(SecurityHeadersMiddleware, settings=settings)",
        ),
        _insert(
            "headers-settings-checks",
            _CONFIG,
            "settings-checks",
            _HEADERS,
            template="security/insert/cors_check.py.j2",
        ),
        _insert(
            "headers-guide",
            guide,
            "security-guide",
            _HEADERS,
            template="security/insert/guide_headers.md.j2",
        ),
        _insert(
            "integrity-router-import",
            _ROUTER,
            "router-imports",
            _INTEGRITY,
            text=f"{_IMPORT}.modules.integrity.router import router as integrity_router",
        ),
        _insert(
            "integrity-router",
            _ROUTER,
            "routers",
            _INTEGRITY,
            text="api_router.include_router(integrity_router)",
        ),
        _insert(
            "integrity-registry",
            _REGISTRY,
            "models",
            _INTEGRITY,
            text=f"{_IMPORT}.modules.integrity.models import IntegrityChallenge  # noqa: F401",
        ),
        _insert(
            "integrity-settings",
            _CONFIG,
            "settings",
            _INTEGRITY,
            text="# How long the app has to turn an integrity challenge into a verdict.\n"
            "integrity_challenge_minutes: int = 5",
        ),
        _insert("integrity-env", _ENV, "env", _INTEGRITY, text="INTEGRITY_CHALLENGE_MINUTES=5"),
        _insert(
            "integrity-guide",
            guide,
            "security-guide",
            _INTEGRITY,
            template="security/insert/guide_integrity.md.j2",
        ),
        _insert(
            "lockout-guide",
            guide,
            "security-guide",
            _LOCKOUT,
            template="security/insert/guide_lockout.md.j2",
        ),
    )


def _worker_inserts() -> tuple[AnchorInsert, ...]:
    tasks = f"{_PKG}/worker/tasks.py"
    return (
        _insert(
            "worker-settings",
            _CONFIG,
            "settings",
            _WORKER,
            template="worker/insert/settings.py.j2",
        ),
        _insert("worker-env", _ENV, "env", _WORKER, template="worker/insert/env.j2"),
        _insert(
            "worker-compose-env",
            _COMPOSE,
            "compose-environment",
            _WORKER,
            text="BROKER_URL: {{ options.broker.compose_url }}",
        ),
        _insert(
            "rabbitmq-compose-service",
            _COMPOSE,
            "compose-services",
            _broker_is(Broker.RABBITMQ),
            template="worker/insert/rabbitmq_compose.yml.j2",
        ),
        _insert(
            "worker-compose-service",
            _COMPOSE,
            "compose-services",
            _WORKER,
            template="worker/insert/worker_compose.yml.j2",
        ),
        _insert(
            "worker-import",
            _MAIN,
            "main-imports",
            _WORKER,
            text=f"{_IMPORT}.worker.broker import broker",
        ),
        _insert(
            "worker-startup",
            _MAIN,
            "startup",
            _WORKER,
            text="# The API only sends tasks; it connects to the broker once, at startup.\n"
            "await broker.startup()",
        ),
        _insert("worker-shutdown", _MAIN, "shutdown", _WORKER, text="await broker.shutdown()"),
        _insert(
            "worker-health-import",
            _HEALTH,
            "health-imports",
            _WORKER,
            text=f"{_IMPORT}.worker.broker import broker_status",
        ),
        _insert(
            "worker-readiness",
            _HEALTH,
            "readiness-checks",
            _WORKER,
            text='checks["broker"] = await broker_status()',
        ),
        _insert(
            "worker-readme",
            _README,
            "guides",
            _WORKER,
            text="- [docs/BACKGROUND.md](docs/BACKGROUND.md): background tasks and the worker",
        ),
        _insert(
            "worker-agents",
            _AGENTS,
            "agent-rules",
            _WORKER,
            text="- **Slow or retryable work is a task.** Sending email, calling a slow API or "
            "crunching a report goes in `worker/tasks.py` and is sent with "
            "`await task.kiq(...)`; arguments are plain JSON values (ids, not models).",
        ),
        _insert(
            "scheduler-compose-service",
            _COMPOSE,
            "compose-services",
            _SCHEDULER,
            template="worker/insert/scheduler_compose.yml.j2",
        ),
        _insert(
            "scheduler-guide",
            "docs/BACKGROUND.md",
            "background-guide",
            _SCHEDULER,
            template="worker/insert/guide_scheduler.md.j2",
        ),
        _insert(
            "purge-refresh-import",
            tasks,
            "task-imports",
            _on("scheduler", "auth_refresh"),
            text=_users_import("public", "purge_expired_refresh_tokens")
            + f"\n{_IMPORT}.worker.database import session_factory",
        ),
        _insert(
            "purge-refresh-task",
            tasks,
            "tasks",
            _on("scheduler", "auth_refresh"),
            template="worker/insert/purge_refresh_task.py.j2",
        ),
    )


def _realtime_inserts() -> tuple[AnchorInsert, ...]:
    identity = f"{_PKG}/realtime/identity.py"
    guide = "docs/REALTIME.md"
    return (
        _insert(
            "realtime-readme",
            _README,
            "guides",
            _REALTIME,
            text="- [docs/REALTIME.md](docs/REALTIME.md): WebSockets, server-sent events, "
            "broadcasting",
        ),
        _insert(
            "realtime-auth-import",
            identity,
            "identity-imports",
            _on("realtime", "auth"),
            text=_users_import("public", "user_id_from_access_token"),
        ),
        _insert(
            "realtime-auth",
            identity,
            "identity",
            _on("realtime", "auth"),
            text="read_user_id = user_id_from_access_token",
        ),
        _insert(
            "realtime-auth-public-import",
            f"{_USERS}/public.py",
            "public-imports",
            _on("realtime", "auth"),
            text=_reexport("tokens", "user_id_from_access_token"),
        ),
        _insert(
            "websockets-router-import",
            _ROUTER,
            "router-imports",
            _WEBSOCKETS,
            text=f"{_IMPORT}.realtime.websockets import router as websockets_router",
        ),
        _insert(
            "websockets-router",
            _ROUTER,
            "routers",
            _WEBSOCKETS,
            text="api_router.include_router(websockets_router)",
        ),
        _insert(
            "websockets-guide",
            guide,
            "realtime-guide",
            _WEBSOCKETS,
            template="realtime/insert/guide_websockets.md.j2",
        ),
        _insert(
            "events-router-import",
            _ROUTER,
            "router-imports",
            _SSE,
            text=f"{_IMPORT}.realtime.events import router as events_router",
        ),
        _insert(
            "events-router",
            _ROUTER,
            "routers",
            _SSE,
            text="api_router.include_router(events_router)",
        ),
        _insert(
            "events-guide",
            guide,
            "realtime-guide",
            _SSE,
            template="realtime/insert/guide_events.md.j2",
        ),
    )


def _services_inserts() -> tuple[AnchorInsert, ...]:
    guide = "docs/SERVICES.md"
    return (
        _insert(
            "services-readme",
            _README,
            "guides",
            _SERVICES,
            text="- [docs/SERVICES.md](docs/SERVICES.md): email, cache, file storage, push, "
            "report & block, purchases",
        ),
        # ── email ──
        _insert(
            "email-settings",
            _CONFIG,
            "settings",
            _EMAIL,
            template="services/insert/email_settings.py.j2",
        ),
        _insert("email-env", _ENV, "env", _EMAIL, template="services/insert/email_env.j2"),
        _insert(
            "email-compose-env",
            _COMPOSE,
            "compose-environment",
            _EMAIL,
            text="SMTP_HOST: mailpit",
        ),
        _insert(
            "email-compose-service",
            _COMPOSE,
            "compose-services",
            _EMAIL,
            template="services/insert/mailpit_compose.yml.j2",
        ),
        _insert(
            "email-import",
            _MAIN,
            "main-imports",
            _EMAIL,
            text=f"{_IMPORT}.services.email import SmtpEmailSender",
        ),
        _insert(
            "email-state",
            _MAIN,
            "app-state",
            _EMAIL,
            text="app.state.email_sender = SmtpEmailSender(settings)",
        ),
        _insert(
            "email-test-import",
            _CONFTEST,
            "test-imports",
            _EMAIL,
            text=f"{_IMPORT}.services.email import OutboxEmailSender",
        ),
        _insert(
            "email-test-app",
            _CONFTEST,
            "test-app",
            _EMAIL,
            text="# Emails land in a list the test can read, never in an inbox.\n"
            "test_app.state.email_sender = OutboxEmailSender()",
        ),
        _insert(
            "email-fixtures",
            _CONFTEST,
            "fixtures",
            _EMAIL,
            template="services/insert/outbox_fixture.py.j2",
        ),
        _insert(
            "email-guide",
            guide,
            "services-guide",
            _EMAIL,
            template="services/insert/guide_email.md.j2",
        ),
        # ── cache ──
        _insert(
            "cache-guide",
            guide,
            "services-guide",
            _CACHE,
            template="services/insert/guide_cache.md.j2",
        ),
        # ── storage ──
        _insert(
            "storage-settings",
            _CONFIG,
            "settings",
            _STORAGE,
            template="services/insert/storage_settings.py.j2",
        ),
        _insert("storage-env", _ENV, "env", _STORAGE, template="services/insert/storage_env.j2"),
        _insert(
            "storage-compose-env",
            _COMPOSE,
            "compose-environment",
            _STORAGE,
            text="S3_ENDPOINT_URL: http://minio:9000",
        ),
        _insert(
            "storage-compose-service",
            _COMPOSE,
            "compose-services",
            _STORAGE,
            template="services/insert/minio_compose.yml.j2",
        ),
        _insert(
            "storage-import",
            _MAIN,
            "main-imports",
            _STORAGE,
            text=f"{_IMPORT}.services.storage import build_file_storage",
        ),
        _insert(
            "storage-state",
            _MAIN,
            "app-state",
            _STORAGE,
            text="app.state.file_storage = build_file_storage(settings)",
        ),
        _insert(
            "storage-guide",
            guide,
            "services-guide",
            _STORAGE,
            template="services/insert/guide_storage.md.j2",
        ),
        # ── push ──
        _insert(
            "push-guide",
            guide,
            "services-guide",
            _PUSH,
            template="services/insert/guide_push.md.j2",
        ),
        _insert(
            "moderation-router-import",
            _ROUTER,
            "router-imports",
            _MODERATION,
            text=f"{_IMPORT}.modules.moderation.router import router as moderation_router",
        ),
        _insert(
            "moderation-router",
            _ROUTER,
            "routers",
            _MODERATION,
            text="api_router.include_router(moderation_router)",
        ),
        _insert(
            "moderation-registry",
            _REGISTRY,
            "models",
            _MODERATION,
            text=f"{_IMPORT}.modules.moderation.models import Block, Report  # noqa: F401",
        ),
        _insert(
            "moderation-guide",
            guide,
            "services-guide",
            _MODERATION,
            template="services/insert/guide_moderation.md.j2",
        ),
        _insert(
            "moderation-agents",
            _AGENTS,
            "agent-rules",
            _MODERATION,
            text="- **Respect blocks.** An endpoint that lists what users publish, or lets one "
            "user reach another, filters with `blocked_user_ids` / `is_blocked_between` from "
            "`modules/moderation/public.py`.",
        ),
        _insert(
            "purchases-router-import",
            _ROUTER,
            "router-imports",
            _PURCHASES,
            text=f"{_IMPORT}.modules.purchases.router import router as purchases_router",
        ),
        _insert(
            "purchases-router",
            _ROUTER,
            "routers",
            _PURCHASES,
            text="api_router.include_router(purchases_router)",
        ),
        _insert(
            "purchases-registry",
            _REGISTRY,
            "models",
            _PURCHASES,
            text=f"{_IMPORT}.modules.purchases.models import Entitlement  # noqa: F401",
        ),
        _insert(
            "purchases-guide",
            guide,
            "services-guide",
            _PURCHASES,
            template="services/insert/guide_purchases.md.j2",
        ),
    )


def _observability_inserts() -> tuple[AnchorInsert, ...]:
    return (
        # ── tracing ──
        _insert(
            "tracing-settings",
            _CONFIG,
            "settings",
            _TRACING,
            text="# Where traces go (an OpenTelemetry collector); empty sends none.\n"
            'otel_exporter_endpoint: str = ""',
        ),
        _insert(
            "tracing-env",
            _ENV,
            "env",
            _TRACING,
            text="\n# Your collector (OTLP/HTTP), e.g. http://localhost:4318. Empty: off.\n"
            "OTEL_EXPORTER_ENDPOINT=",
        ),
        _insert(
            "tracing-import",
            _MAIN,
            "main-imports",
            _TRACING,
            text=f"{_IMPORT}.core.tracing import configure_tracing",
        ),
        _insert(
            "tracing-state",
            _MAIN,
            "app-state",
            _TRACING,
            text="configure_tracing(app, engine, settings)",
        ),
        _insert(
            "tracing-guide",
            _OBSERVABILITY_GUIDE,
            "observability-guide",
            _TRACING,
            template="observability/insert/guide_tracing.md.j2",
        ),
        # ── sentry ──
        _insert(
            "sentry-settings",
            _CONFIG,
            "settings",
            _SENTRY,
            text="# Your Sentry project's DSN; empty reports nothing.\n"
            'sentry_dsn: str = ""\n'
            "# Share of requests traced in Sentry: 0.0 to 1.0.\n"
            "sentry_traces_sample_rate: float = 0.1",
        ),
        _insert(
            "sentry-env",
            _ENV,
            "env",
            _SENTRY,
            text="\n# Sentry DSN. Empty: errors are not reported.\nSENTRY_DSN=\n"
            "SENTRY_TRACES_SAMPLE_RATE=0.1",
        ),
        _insert(
            "sentry-import",
            _MAIN,
            "main-imports",
            _SENTRY,
            text=f"{_IMPORT}.core.sentry import configure_sentry",
        ),
        _insert("sentry-setup", _MAIN, "setup", _SENTRY, text="configure_sentry(settings)"),
        _insert(
            "sentry-guide",
            _OBSERVABILITY_GUIDE,
            "observability-guide",
            _SENTRY,
            template="observability/insert/guide_sentry.md.j2",
        ),
        # ── metrics ──
        _insert(
            "metrics-import",
            _MAIN,
            "main-imports",
            _METRICS,
            text=f"{_IMPORT}.core.metrics import install_metrics",
        ),
        _insert("metrics-routes", _MAIN, "app-routers", _METRICS, text="install_metrics(app)"),
        _insert(
            "metrics-guide",
            _OBSERVABILITY_GUIDE,
            "observability-guide",
            _METRICS,
            template="observability/insert/guide_metrics.md.j2",
        ),
        _insert(
            "tracing-log-import",
            _LOGGING,
            "logging-imports",
            _TRACING,
            text=f"{_IMPORT}.core.tracing import add_trace_ids",
        ),
        _insert(
            "tracing-log-context", _LOGGING, "log-context", _TRACING, text="add_trace_ids(record)"
        ),
        # ── tracing with a worker: one trace from the request through its tasks ──
        _insert(
            "traces-tasks-import",
            _BROKER,
            "broker-imports",
            _TRACES_TASKS,
            text="from taskiq.middlewares.opentelemetry_middleware import OpenTelemetryMiddleware\n"
            f"{_IMPORT}.core.tracing import configure_worker_tracing",
        ),
        _insert(
            "traces-tasks-middleware",
            _BROKER,
            "broker-middlewares",
            _TRACES_TASKS,
            text="# Sends the request's trace with the task and continues it in the worker.\n"
            "broker.add_middlewares(OpenTelemetryMiddleware())",
        ),
        _insert(
            "traces-tasks-startup",
            _BROKER,
            "worker-startup",
            _TRACES_TASKS,
            text="configure_worker_tracing(settings)",
        ),
        # ── tracing with Docker: Grafana's otel-lgtm to look at it ──
        _insert(
            "local-telemetry-compose-env",
            _COMPOSE,
            "compose-environment",
            _LOCAL_TELEMETRY,
            text="OTEL_EXPORTER_ENDPOINT: http://otel-lgtm:4318",
        ),
        _insert(
            "local-telemetry-compose-service",
            _COMPOSE,
            "compose-services",
            _LOCAL_TELEMETRY,
            template="observability/insert/otel_lgtm_compose.yml.j2",
        ),
        _insert(
            "local-telemetry-guide",
            _OBSERVABILITY_GUIDE,
            "observability-guide",
            _LOCAL_TELEMETRY,
            template="observability/insert/guide_local_telemetry.md.j2",
        ),
        _insert(
            "metrics-scrape",
            _PROMETHEUS,
            "prometheus-scrape",
            _on("metrics", "local_telemetry"),
            template="observability/insert/metrics_scrape.yml.j2",
        ),
        # ── sentry: each error tagged with its request ID ──
        _insert(
            "sentry-request-id-import",
            _REQUEST_ID,
            "request-id-imports",
            _SENTRY,
            text="import sentry_sdk",
        ),
        _insert(
            "sentry-request-id",
            _REQUEST_ID,
            "request-context",
            _SENTRY,
            text="# Sentry keeps one scope per request: the tag lands on that request's errors.\n"
            'sentry_sdk.set_tag("request_id", request_id)',
        ),
    )


OPTION_INSERTS: tuple[AnchorInsert, ...] = (
    *_redis_inserts(),
    *_auth_inserts(),
    *_security_inserts(),
    *_worker_inserts(),
    *_realtime_inserts(),
    *_services_inserts(),
    *_observability_inserts(),
)

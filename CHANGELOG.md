# Changelog

## 0.3.0 — 26/11/2026

**Presets, auth, security, background tasks, realtime and services.**

- `init --preset <fintech|ecommerce|social|health|field|content|mvp>`, and a
  first "What are you building?" question: the checklists open pre-ticked for
  that kind of app, with the options it needs locked on.
- Four new checklists after *What to generate*: Auth, Security, Background &
  realtime (after a broker question, `--broker none|rabbitmq|redis`) and
  Services. An option that needs another ticks it, `(needed by …)`.
- `create auth [--no-refresh] [--google] [--apple]`: a `users` module
  matching the Flutter moarch's REST auth client, argon2id passwords, a
  configurable password policy, HS256 access tokens, rotating refresh tokens
  with reuse detection, Google and Apple sign-in by ID token, and with email,
  verification and password reset.
- `create security <rate-limit|audit-log|idempotency|headers|lockout>`.
- `create worker [--broker redis|rabbitmq] [--schedule]`: taskiq worker and
  scheduler, in docker-compose too.
- `create realtime <websockets|sse>`: a Redis pub/sub broadcaster feeding
  `/ws` and `/events`.
- `create service <email|cache|storage|push|moderation|purchases|tracing|sentry|metrics|observability>`.
- The endpoints the Flutter moarch's services call: device integrity
  (`create security integrity`: a single-use challenge, Play Integrity checked
  with Google, App Attest a 503 until implemented), report & block
  (`create service moderation`) and purchases (`create service purchases`:
  Google Play receipts verified and acknowledged, one purchase per account).
  The `fintech`, `social` and `content` presets tick them, as in Flutter.
- Lockout counts per account **and** client IP, so nobody can lock out an
  account that is not theirs; a ceiling of failures across all IPs within an
  hour still locks the account (docs/adr/0007).
- FCM, Play Integrity and Play billing call Google as one service account
  (`GOOGLE_SERVICE_ACCOUNT_FILE`, `core/google_service_account.py`).
- Sentry is configured for sentry-sdk 3 (`data_collection`).
- Each part writes its guide in `docs/` and its rules into `AGENTS.md`.

Shared files (`main.py`, `config.py`, `docker-compose.yml`, `.env.example`,
`conftest.py`, `README.md`, `AGENTS.md`) get new `# moarch:` anchors, where
every option adds its lines, whether at `init` or later with `create`.
`docker-compose.yml` now shares one `x-app` block between the API and any
worker, and every service restarts on failure. SQLite connections enforce
foreign keys, so `ON DELETE CASCADE` works in the tests too. `.moarch-py.yaml`
records the broker.

**Existing projects:** the `create` commands for the new options need the new
anchors, so they work on projects made with this version. On an older
project, a missing anchor stops the command before it writes anything and
prints the lines to paste by hand.

## 0.2.2 — 22/11/2026

**Stricter typing in new projects.** Their Ruff config adds `ANN` (every
function annotated; `ANN401` bans `Any`) and `PGH` (no blanket
`# type: ignore` or `# noqa` without a code), on top of `mypy --strict`.
Every template passes them. `update` does not rewrite `pyproject.toml`, so
for an existing project add `"ANN", "PGH"` to `[tool.ruff.lint] select`
by hand and fix what `ruff check` then reports.

moarch-py's own code now runs `mypy --strict` over `src/` and `tests/` in
CI, with the same Ruff rules.

## 0.2.1 — 21/11/2026

**Mock responses:** every module gets `mocks.py`: sample data and a
`<Name>MockService` that answers like the real service, stores nothing and
needs no database. `MOCK_RESPONSES=true` (a new `Settings` field, refused in
production) switches every module to it, and every response then carries
`X-Mock-Response: true`. Each module gets `test_<name>_mocks.py`, and
`conftest.py` a `mock_client` fixture. Projects made before this need the
`mock_responses` setting in `core/config.py` before `create module`.

## 0.2.0 — 21/11/2026

Generated projects are now **modular monoliths**.

- `moarch-py create module <name>` replaces `create feature` (kept as a hidden
  alias). It writes `src/<pkg>/modules/<name>/` and `tests/modules/<name>/`.
- Each module gets `public.py`: the only file other modules may import. It hands
  out schemas and read functions (`find_<name>`), never models, and has its own
  tests.
- New projects get an import-linter `independence` contract in `pyproject.toml`
  (wildcards, so new modules need no config), `import-linter` as a dev
  dependency, a "Module boundaries" CI step and a `lint-imports` pre-commit hook.
- The AI guide teaches the module rules: `moarch-add-module` replaces
  `moarch-add-feature`, and `AGENTS.md`, `docs/ARCHITECTURE.md`, review,
  explain and write-tests cover `public.py` and `lint-imports`.
- `moarch-py create model <module> <name>` (the Flutter moarch's grammar): adds
  another model to an existing module (its class, Create/Update/Read schemas
  and repository, at new `# moarch:` anchors in that module's files),
  registers it in `db/models.py` and writes a repository test. No service or
  router: the module decides how it is used.
- `.moarch-py.yaml` records `modules:`; a 0.1.0 manifest's `features:` is still
  read.

**Breaking for 0.1.0 projects:** their code stays in `features/`, while new
modules go to `modules/`, and they have no import-linter contract. Move
`features/<name>/` to `modules/<name>/` (and the imports in `api/v1/router.py`
and `db/models.py`), or keep creating with 0.1.0.

## 0.1.0 — 21/11/2026

First version.

- `moarch-py init [name]`: interactive wizard (database; migrations, Docker,
  CI, pre-commit, AI guide), `--all`, `--db`, `--dry-run`, `--no-install`,
  `--force`. Runs `uv add`, formats with Ruff, starts a git repository and
  writes `.moarch-py.yaml`.
- `moarch-py create feature <name>`: model, schemas, repository, service,
  router, dependencies and API tests, registered at the `# moarch:` anchors.
- Generated projects: Python 3.12, FastAPI, SQLAlchemy 2 async, Alembic,
  pydantic-settings, multi-stage uv Dockerfile, docker-compose, GitHub
  Actions, pre-commit, Ruff (CLI, pre-commit, CI and VS Code on save), mypy
  strict, pytest on in-memory SQLite.
- AI agent guide: `AGENTS.md`, `CLAUDE.md` and six skills (add-feature,
  write-tests, fix-bug, review, make-readable, explain).

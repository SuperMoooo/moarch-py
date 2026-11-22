# moarch-py

A Python CLI that scaffolds **modular-monolith FastAPI projects** on uv,
SQLAlchemy 2 (async), Alembic and Pydantic v2, with your conventions built in:
modules with enforced boundaries, layers, tests, Docker, CI, Ruff, mypy and an
AI agent guide.

It is the FastAPI sibling of [moarch for Flutter](https://pub.dev/packages/moarch)
and uses the same commands: `init` makes the project, `create` adds to it.

## Install

```bash
uvx moarch-py init my-api          # run once without installing
uv tool install moarch-py          # or install the `moarch-py` command
```

It needs [uv](https://docs.astral.sh/uv/). Generated projects target
Python 3.12+.

## Quick start

```bash
moarch-py init shop-api            # wizard: database + what to generate
cd shop-api
docker compose up -d db
uv run alembic upgrade head
uv run fastapi dev src/shop_api/main.py      # http://localhost:8000/docs

moarch-py create module orders     # public.py, model, schemas, repository, service, router, mocks, tests
uv run alembic revision --autogenerate -m "create orders"
uv run alembic upgrade head
uv run python -m pytest
uv run lint-imports                # modules talk only through public.py
```

## Commands

```bash
moarch-py init [name]               # interactive scaffold; no name = the current folder (after `uv init`)
moarch-py init --all                # default structure, no prompts
moarch-py init --db sqlite          # pick the database without the question (postgres | mysql | sqlite)
moarch-py init --preset fintech     # start the checklists from a kind of app (see below)
moarch-py init --broker rabbitmq    # pick the task broker without the question (none | rabbitmq | redis)
moarch-py init --dry-run            # list every file it would write
moarch-py init --no-install         # write the files, skip `uv add`

moarch-py create module <name>      # a module: public.py + every layer, registered at the # moarch: anchors
moarch-py create module <name> -p path/to/project --dry-run
moarch-py create model <module> <name>   # another model inside a module: class, schemas, repository, test

moarch-py create auth [--no-refresh] [--google] [--apple]   # users, sign-in, tokens
moarch-py create security <rate-limit|audit-log|idempotency|headers|lockout>...
moarch-py create worker [--broker redis|rabbitmq] [--schedule]   # taskiq worker, scheduler
moarch-py create realtime <websockets|sse>...
moarch-py create service <email|cache|storage|push|tracing|sentry|metrics|observability>...
moarch-py create service --list     # every name a create command takes (also security, realtime)
```

Every `create <option>` takes `-p <project>`, `--dry-run` and `--no-install`,
and adds exactly what ticking the option at `init` would have.

Coming next, with the same syntax as the Flutter moarch:
`create auth --github`, `create version v2`, `create tests`,
`update [name|group]`, `doctor [--fix]` and `release bump`.

`create feature` still works as a hidden alias of `create module` (its name in
0.1.0, and the Flutter moarch's word).

## What it generates

```text
shop-api/
├── pyproject.toml · uv.lock · .python-version (3.12) · .env.example · .moarch-py.yaml
├── Dockerfile · .dockerignore · docker-compose.yml      multi-stage uv build, non-root, healthcheck
├── alembic.ini · migrations/                            async env, ruff-formatted revisions
├── .github/workflows/ci.yml                             ruff, mypy, import-linter, pytest, migrations on a real DB, image build
├── .pre-commit-config.yaml                              ruff and import-linter through uv
├── .vscode/                                             Ruff as formatter + linter on save
├── AGENTS.md · CLAUDE.md · .agents/skills/ · .claude/   the AI agent guide
├── docs/ARCHITECTURE.md
├── src/shop_api/
│   ├── main.py            create_app(): settings, engine, CORS, error handlers, routers
│   ├── core/              config (pydantic-settings), logging, errors (AppError → JSON)
│   ├── db/                Base + naming convention, session, BaseRepository[Model], models registry
│   ├── api/health.py      /health and /health/ready
│   ├── api/v1/router.py   every module router, under /api/v1
│   └── modules/<name>/    public · models · schemas · repository · service · router · dependencies · mocks
└── tests/                 a fresh in-memory database per test; no server needed
```

Each option in the wizard can be switched off: migrations, Docker, CI,
pre-commit, and the AI guide.

## Start from a kind of app

The first question `init` asks is what you are building. **Let me decide**
opens the checklists with the usual defaults. A preset pre-ticks them for that
kind of app and locks the options it cannot do without, shown as
`(required by …)`; everything else stays yours to toggle. Nothing records the
preset: a project only has options.

| Preset | `--preset` | Required | Also ticked | Broker |
| --- | --- | --- | --- | --- |
| FinTech / banking | `fintech` | auth, refresh tokens, lockout, rate limiting, audit log, idempotency, security headers | Google, Apple, email, scheduler, tracing, Sentry, metrics | RabbitMQ |
| E-commerce / marketplace | `ecommerce` | auth, idempotency, email | refresh, Google, Apple, rate limiting, headers, cache, storage, push, tracing, Sentry, metrics | Redis |
| Social / community | `social` | auth, storage, WebSockets | refresh, Google, Apple, email, push, cache, rate limiting | Redis |
| Health / fitness | `health` | auth, refresh tokens, audit log, security headers, lockout | email, push, scheduler, tracing, Sentry, metrics | Redis |
| Field service / delivery | `field` | auth, storage | refresh, push, server-sent events | Redis |
| News / media / content | `content` | auth, cache | refresh, Google, Apple, email, storage, push, server-sent events | none |
| MVP | `mvp` | auth | refresh, Google, Apple, email | none |

Every preset keeps migrations, Docker, CI, pre-commit and the agent guide.
`--preset <slug>` skips the question (and, without a terminal, every other
one too). `--all` cannot be combined with it.

## The options

After *What to generate*, the wizard asks four more checklists. Ticking one
that needs another ticks that too, shown as `(needed by …)`. Anything that
must be shared by every instance of the API (rate limits, realtime fan-out)
keeps its state in one shared Redis, added on its own, never in memory. Each
part writes its guide in `docs/` and its rules into the project's `AGENTS.md`,
and its tests use fakes (fakeredis, an in-memory broker, an email outbox), so
`uv run pytest` still needs no server.

**Auth** (`docs/AUTH.md`): a `users` module whose endpoints match the Flutter
moarch's REST auth client (`/auth/register`, `/login`, `/logout`, `/me`,
`DELETE /me`, `/device-token`). argon2id passwords, a password policy in the
settings (NIST SP 800-63B defaults: length, no forced character mix), and 15
minute HS256 access tokens. Protect any endpoint with `user: CurrentUser`
from `users/public.py`.
- *Refresh tokens:* single-use, rotated on every `/auth/refresh`; a reused
  token revokes its whole session.
- *Google and Apple sign-in:* the app's ID token is checked against the
  provider's keys and your client IDs; a verified email links to an existing
  account, an unverified one never does.
- With **email**: verification links and password reset (`/auth/email/…`,
  `/auth/password/…`), and `CurrentVerifiedUser`.

**Security** (`docs/SECURITY.md`): rate limiting per client in Redis (tight on
the auth paths), an append-only audit log module (auth events go in it too),
`Idempotency-Key` on writes, security headers with strict CORS in production,
and account lockout (423 `account_locked`, with the minutes left).

**Background & realtime:** a broker question (`none | rabbitmq | redis`)
gives a [taskiq](https://taskiq-python.github.io/) worker
(`docs/BACKGROUND.md`); *Scheduled tasks* add a scheduler, which purges
expired refresh tokens nightly when there are any. *WebSockets* (`/ws`, the
access token in the first message) and *server-sent events* (`/events`) share
a broadcaster over Redis pub/sub (`docs/REALTIME.md`).

**Services** (`docs/SERVICES.md`): email over SMTP (Mailpit in
docker-compose), a Redis cache of Pydantic models, file storage on disk or any
S3-compatible bucket (MinIO in docker-compose), push notifications through
FCM's HTTP v1 API, OpenTelemetry tracing, Sentry and Prometheus `/metrics`.

**The modules:** each business area (orders, billing, users) is a package in
`modules/` with its own tables, rules and endpoints. Other modules may import
only its `public.py`, which hands out schemas and functions, never models. An
[import-linter](https://pypi.org/project/import-linter/) contract in
`pyproject.toml` enforces it: `uv run lint-imports` (in CI and pre-commit)
fails when a module reaches into another's internals. Its wildcards cover
every module, so a new module needs no config change.

**Mock responses:** set `MOCK_RESPONSES=true` and every module answers from
the sample data in its `mocks.py` instead of the database: the same URLs,
schemas and 404s, nothing stored, and an `X-Mock-Response: true` header. A
client app can be built and tested before any real data exists, or with no
database running. The settings refuse it in production.

**The layers**, inside each module: `router → service → repository → session`. Routers speak HTTP
and return schemas; services hold the rules and commit; repositories are the
only code that queries, and only flush. See the generated
`docs/ARCHITECTURE.md`.

**Ruff everywhere:** the same Ruff version (from `uv.lock`) and rules
(`[tool.ruff]`) format and lint on save in VS Code, in pre-commit and in CI,
and moarch-py formats every file it writes, so a fresh project passes
`ruff format --check` and `ruff check` on day one.

**Packages are never pinned by moarch:** `init` runs `uv add`, so every new
project starts on the newest compatible releases, locked in `uv.lock`.

### The AI agent guide

`AGENTS.md` (read by Codex, Cursor, Copilot, Gemini CLI) states the project's
rules; `CLAUDE.md` imports it for Claude Code. `.agents/skills/` holds
step-by-step skills, with pointers in `.claude/skills/`:

| Skill | For |
| --- | --- |
| `moarch-add-module` | A new business module through every layer and its public.py, with its migration and tests |
| `moarch-write-tests` | API and service tests on the in-memory database |
| `moarch-fix-bug` | Reproduce with a failing test first, fix in the owning layer |
| `moarch-review` | Review a diff against the architecture rules |
| `moarch-make-readable` | Clear names, one job per function, comments that explain why |
| `moarch-explain` | Teaches the Python, FastAPI, SQLAlchemy and Pydantic behind the code, step by step, with links |

## Contributing

See [AGENTS.md](AGENTS.md) for the architecture, and `.agents/skills/` for the
procedures (add a template, try a real scaffold, release).

```bash
uv sync
uv run python -m pytest                 # every option, preset and combination, a few seconds
uv run python -m pytest -m scaffold     # real projects: install, ruff, mypy, pytest
```

## License

MIT

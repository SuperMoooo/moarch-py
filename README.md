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

moarch-py create module orders     # public.py, model, schemas, repository, service, router, tests
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
moarch-py init --dry-run            # list every file it would write
moarch-py init --no-install         # write the files, skip `uv add`

moarch-py create module <name>      # a module: public.py + every layer, registered at the # moarch: anchors
moarch-py create module <name> -p path/to/project --dry-run
moarch-py create model <module> <name>   # another model inside a module: class, schemas, repository, test
```

Coming next, with the same syntax as the Flutter moarch:
`create auth --google --apple --github`, `create worker`, `create version v2`,
`create tests`, `update [name|group]`, `doctor [--fix]`, `release bump`, and
`init --preset`.

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
│   └── modules/<name>/    public · models · schemas · repository · service · router · dependencies
└── tests/                 a fresh in-memory database per test; no server needed
```

Each option in the wizard can be switched off: migrations, Docker, CI,
pre-commit, and the AI guide.

**The modules:** each business area (orders, billing, users) is a package in
`modules/` with its own tables, rules and endpoints. Other modules may import
only its `public.py`, which hands out schemas and functions, never models. An
[import-linter](https://pypi.org/project/import-linter/) contract in
`pyproject.toml` enforces it: `uv run lint-imports` (in CI and pre-commit)
fails when a module reaches into another's internals. Its wildcards cover
every module, so a new module needs no config change.

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
uv run python -m pytest                 # every option combination, about a second
uv run python -m pytest -m scaffold     # real projects: install, ruff, mypy, pytest
```

## License

MIT

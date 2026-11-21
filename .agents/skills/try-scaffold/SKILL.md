---
name: try-scaffold
description: "Generate real FastAPI projects from this moarch-py checkout and check they install, format, lint, type-check, migrate and test clean. Use after changing a template, before a release, or to reproduce a bug a user reported in a generated project."
---

# Scaffold a real project

The fast tests check that templates render and parse; only a real project
checks that the result installs, passes ruff and mypy, and runs. Work in a
temporary directory, never inside this repository.

## Automated

```bash
uv run python -m pytest -m scaffold
```

generates a Postgres and a SQLite project with `--all`, adds a feature, and
runs `ruff format --check`, `ruff check`, `mypy src` and `pytest` in each.

## By hand (for an option off by default, or migrations and Docker)

```bash
cd "$(mktemp -d)"
uv run --project <repo> python -m moarch_py init demo-api --all --db postgres
cd demo-api
uv run --project <repo> python -m moarch_py create feature orders
uv run --project <repo> python -m moarch_py create feature order_items
uv run python -m ruff format --check . && uv run python -m ruff check . && uv run python -m mypy src && uv run python -m pytest
```

Migrations, against SQLite when no database server is running:

```bash
DATABASE_URL=sqlite+aiosqlite:///./check.db uv run python -m alembic revision --autogenerate -m "init"
DATABASE_URL=sqlite+aiosqlite:///./check.db uv run python -m alembic upgrade head
DATABASE_URL=sqlite+aiosqlite:///./check.db uv run python -m alembic check
uv run python -m ruff check migrations
```

Docker (needs the Docker daemon):

```bash
docker compose up --build -d
curl http://localhost:8000/health/ready      # {"status": "ok", "database": "ok"}
docker compose down -v
```

Behind a TLS-intercepting proxy, export `UV_SYSTEM_CERTS=1` first.

## Report

Each failure with the generated file and line and the template it came from.
Fix the **template**, never the generated file, and run again from the start.

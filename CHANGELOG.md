# Changelog

## 0.1.0 — unreleased

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

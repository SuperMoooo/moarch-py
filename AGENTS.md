# AGENTS.md

Guidance for coding agents (Claude Code, Codex, Cursor, Copilot, Gemini CLI)
working in this repository. `CLAUDE.md` imports this file; step-by-step
procedures for the common changes are in `.agents/skills/` (see
[Skills](#skills)).

## What this is

`moarch-py` (PyPI) is a Python CLI that scaffolds **feature-first FastAPI
projects** on uv, SQLAlchemy 2 async, Alembic and Pydantic v2. It is the
Python sibling of the Flutter CLI
(`moarch`, https://pub.dev/packages/moarch) and **must keep the same command grammar**:
`init`, `create <thing>`, `update [name|group]`, `doctor [--fix]`,
`release bump`, with `--all`, `--preset`, `--dry-run`, `--list`, `--diff`,
`# moarch:<anchor>` comments and a `.moarch-py.yaml` manifest. Before naming a
command or flag, check the Flutter README and reuse its word.

Every file the CLI generates is a **Jinja template** in
`src/moarch_py/templates/`. Editing a template changes what other people's
projects get, so treat template text as production code.

## Commands

```bash
uv sync
uv run python -m pytest                          # fast suite (every option combination, no network)
uv run python -m pytest -m scaffold              # generates real projects and runs their checks (slow)
uv run python -m pytest tests/test_scaffold.py -k feature
uv run python -m ruff format .
uv run python -m ruff check .
uv run python -m moarch_py <args>                   # run this checkout's CLI
uv tool install --editable .           # install this checkout as `moarch-py`
```

Behind a TLS-intercepting proxy, uv needs `UV_SYSTEM_CERTS=1`.

**Run tools as `python -m <tool>`, never the `.venv/Scripts/*.exe` launchers**
(`uv run pytest`, `uv run python -m mypy`…). On the maintainer's Windows machine, AVG's
Auto-Sandbox sandboxes every such launcher and can freeze the PC; `python.exe`
is not flagged. For the same reason the `scaffold` tests (which build fresh
venvs) are skipped locally unless `MOARCH_PY_SCAFFOLD=1`; CI runs them.

## Architecture

`cli.py` (Typer) → `commands.py` (disk, uv, git, output) → `scaffold.py`
(pure: options → `FilePlan`) → `render.py` (Jinja) + `catalog.py`.

- **Generation is pure.** `scaffold.plan_project` / `plan_feature` return a
  `FilePlan` (path → content) and never touch disk or run processes. That is
  what makes `--dry-run` exact and lets `tests/test_scaffold.py` render all 96
  option combinations in about a second. Side effects live only in `commands.py`.
- **Plan, check, then write.** `FilePlan.write` checks every conflict before
  writing the first file, so a failed command leaves nothing half-written.
  `plan.edit()` marks an intended change to an existing file (an anchor
  insert), which is never a conflict.
- **The catalog is the registry.** `catalog.CATALOG` lists every file `init`
  writes as a `ScaffoldSpec` (slug, path, template, group, `when`). **A new
  generated file is a template plus a catalog entry**; miss the entry and it
  is never written, and `update` can never refresh it. Slugs are unique
  (tested).
- **Options are one dataclass.** `options.ProjectOptions` holds every
  answer; `options.CHECKLIST` is the wizard's checklist. A new checklist
  option is a field there, a `ChecklistOption`, and `when=` predicates in the
  catalog; the combination test picks it up on its own.
- **Anchors.** `file_plan.insert_at_anchor` inserts above a
  `# moarch:<name>` line with its indentation, idempotently; a missing anchor
  raises `AnchorNotFoundError` carrying the snippet to paste by hand.
- **Dependencies are not pinned here.** `dependencies.py` lists names;
  `init` runs `uv add`, which writes the newest compatible versions as lower
  bounds and the exact ones to `uv.lock`.
- **The manifest** (`manifest.py`, `.moarch-py.yaml`) records each generated
  file's hash *after* ruff formats it, so `update` can tell untouched files
  from edited ones.
- **Generated projects target Python 3.12** (`scaffold.PYTHON_VERSION`), the
  most used version; `requires-python` is a floor.

## Rules for templates

- Generated code must pass, in the generated project: `ruff format --check`,
  `ruff check` (the rule set in `pyproject_file._ruff_config`), `mypy --strict`
  and its own `pytest`. The `scaffold` tests check exactly that.
- `StrictUndefined` is on: a misspelt variable fails the render.
- `${{ }}` (GitHub Actions) and Mako's `${}` go inside `{% raw %}`.
- A literal `{` next to a Jinja expression (an f-string, a path parameter) is
  written `{% raw %}{{% endraw %}`.
- Generated code follows the rules it teaches (`templates/ai/AGENTS.md.j2`):
  names in the product's words, one job per function, comments that say why,
  a docstring on every public class and function.

## Code you can read

The same standard applies to this repo's own code: names that say what a
thing is, one job per function, early returns, comments for the why, and a
docstring on every public module, class and function. Follow
`make-readable` for a cleanup pass.

## Done when

```bash
uv run python -m ruff format --check .
uv run python -m ruff check .
uv run python -m pytest
```

pass, and for a template change, `uv run python -m pytest -m scaffold` too (or the
`try-scaffold` skill).

## After every change, tell the user

1. **What changed:** the files, and what each change does.
2. **What happens now** when it runs: the path through the code, step by step.
3. **Concepts used:** any Python or library idea the change relies on, one
   sentence and a link to its official docs.
4. **How to see it:** the command to run to watch it work.

When asked how something works, follow `explain`.

## Skills

| Skill | For |
|---|---|
| [`add-template`](.agents/skills/add-template/SKILL.md) | A new generated file or checklist option |
| [`try-scaffold`](.agents/skills/try-scaffold/SKILL.md) | Generate real projects and check they build, lint, type-check and test clean |
| [`release`](.agents/skills/release/SKILL.md) | Bump the version, changelog, publish to PyPI |
| [`make-readable`](.agents/skills/make-readable/SKILL.md) | Clearer names, smaller functions, comments that explain why |
| [`explain`](.agents/skills/explain/SKILL.md) | Teach how this CLI works, step by step, with links |

Claude Code reads `.claude/skills/`, whose files point here.

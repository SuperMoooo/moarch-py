---
name: explain
description: "Explain what the moarch-py CLI does, step by step, and teach the Python behind it with this repo's own code as the example: traces a command from the terminal through cli.py, commands.py, scaffold.py and the templates to the files on disk, names each concept with a short explanation and a link to the official docs, and ends with a way to see it happen. Use when asked how something works, why it is written that way, what happens when…, or to learn Python, Typer, Jinja or uv."
---

# Explain the code and teach the Python behind it

The user should leave knowing **what happens, in what order, and why** — and
next time, need you a little less. Do not change code while explaining unless
asked; if the code is what makes it hard to follow, offer `make-readable`.

## 1. Answer first, then show the path

One or two plain sentences, then the path through the files in the order it
runs, quoting the lines that matter as `path:line`, numbered.

| What happens | Starts at | Then |
|---|---|---|
| `moarch-py init shop-api` | `cli.py` → `init()` | `commands.run_init` → `resolve_project_root` → `collect_options` (flags or `wizard.py`) → `scaffold.plan_project` (each `catalog` spec → `render`) → `pyproject_file.build_pyproject` → `FilePlan.write` → `uv add` → `ruff format` → `git init` → `.moarch-py.yaml` |
| `moarch-py create module orders` | `cli.py` → `create_module()` | `commands.run_create_module` → `load_manifest` → `ModuleName.parse` → `scaffold.plan_module` (module templates + `insert_at_anchor` ×3) → write → format → manifest |
| `moarch-py create model orders order_lines` | `cli.py` → `create_model()` | `commands.run_create_model` → `ModelName.parse` → `scaffold.plan_model` (model snippets + `insert_at_anchor` ×5) → `_write_and_record` |
| A name becomes identifiers | `naming.py` | `ProjectName.parse` / `ModuleName.parse` → every form the templates use |
| A file conflicts | `FilePlan.conflicts` | `FileConflictError` before anything is written → `cli._run` prints it, exit 1 |

Draw anything with more than three steps.

## 2. Name every concept you pass

First time a concept comes up: one plain sentence, why it is used here, and
the link. Skip what the user already knows.

| Concept | In one sentence | Read more |
|---|---|---|
| `dataclass(frozen=True)` | A class whose fields are set once — options and names cannot change halfway through a run. | [docs.python.org](https://docs.python.org/3/library/dataclasses.html) |
| `StrEnum` | An enum whose values are strings, so `Database.POSTGRES == "postgres"` and Typer can parse it. | [docs.python.org](https://docs.python.org/3/library/enum.html#enum.StrEnum) |
| Type hints, `Annotated` | Hints document and check types; `Annotated` attaches extra info (Typer's option help) to one. | [docs.python.org](https://docs.python.org/3/library/typing.html#typing.Annotated) |
| `pathlib.Path` | Paths as objects (`root / "src"`), the same on Windows and Linux. | [docs.python.org](https://docs.python.org/3/library/pathlib.html) |
| `subprocess.run` | Runs another program (uv, git) and collects its output and exit code. | [docs.python.org](https://docs.python.org/3/library/subprocess.html) |
| Exceptions as control flow | Expected failures are custom exception classes, caught once in `cli._run`. | [docs.python.org](https://docs.python.org/3/tutorial/errors.html) |
| Typer commands | A function's parameters become the command's arguments and options. | [typer.tiangolo.com](https://typer.tiangolo.com/tutorial/) |
| Jinja templates | Text with `{{ variables }}` and `{% if %}` blocks, rendered into each file. | [jinja.palletsprojects.com](https://jinja.palletsprojects.com/en/stable/templates/) |
| `PackageLoader` | Loads templates from inside the installed package, so they ship in the wheel. | [jinja.palletsprojects.com](https://jinja.palletsprojects.com/en/stable/api/#jinja2.PackageLoader) |
| tomlkit | Edits TOML while keeping comments and order — for an existing `pyproject.toml`. | [tomlkit docs](https://tomlkit.readthedocs.io/) |
| uv, `uv add`, `uv.lock` | uv resolves packages; `add` records a lower bound in pyproject and the exact version in the lock. | [docs.astral.sh/uv](https://docs.astral.sh/uv/concepts/projects/dependencies/) |
| Entry points (`[project.scripts]`) | How installing the package creates the `moarch-py` command. | [packaging.python.org](https://packaging.python.org/en/latest/specifications/entry-points/) |
| pytest `parametrize`, `tmp_path` | One test run for many inputs; a fresh temp folder per test. | [docs.pytest.org](https://docs.pytest.org/en/stable/how-to/parametrize.html) |

Tie each concept to *this* code, and read a library's docs or source before
answering about it — never guess an API.

## 3. Let them see it happen

- `uv run python -m moarch_py init demo --all --dry-run` lists every file without writing;
- `uv run python -c "from moarch_py.naming import ModuleName; print(ModuleName.parse('order_items'))"`;
- add a `breakpoint()` in `scaffold.plan_module` and run
  `uv run python -m pytest tests/test_scaffold.py -k module`, then `p plan.files.keys()`.

## 4. Check, then go one step further

End with one short question that checks the key idea ("why is the manifest
hashed after ruff runs, not before?") and offer the next thing worth learning.

## After changing code

Whenever you change code for this user, end with: **what changed**, **what
happens now** step by step, **new concepts** with a link each, and **how to
see it** yourself.

---
name: add-template
description: "Add a file that moarch-py generates, or a new checklist option for `moarch-py init`, end to end: the Jinja template, its catalog entry, the option and its `when`, and the tests. Use when a generated project should get a new file, or a choice the wizard should offer."
---

# Add a generated file or an init option

## A new generated file

1. **Template.** Write `src/moarch_py/templates/<area>/<file>.j2`. It can read
   everything `scaffold.project_context` provides: `name` (`.distribution`,
   `.package`, `.title`), `options`, `database`, `python_version`,
   `uv_version`, `moarch_version`, `skills`. A misspelt variable fails the
   render (`StrictUndefined`).
   - `${{ }}` and Mako `${}` go inside `{% raw %}…{% endraw %}`.
   - A literal `{` beside an expression is `{% raw %}{{% endraw %}`.
   - Generated Python follows `templates/ai/AGENTS.md.j2`: typed, docstrings,
     comments that say why.
2. **Catalog entry** in `src/moarch_py/catalog.py`: a `ScaffoldSpec(slug, path,
   template, group, when)`. The `slug` is unique and is what
   `moarch-py update <slug>` will take; `group` is the batch `update <group>`
   refreshes; `when` is a predicate on `ProjectOptions` (leave it out for
   "always").
3. **Test** in `tests/test_scaffold.py`: assert the content that matters
   (not the whole file). The combination test already parses every `.py`,
   `.yml` and `.json` for the 96 core option sets; `test_options.py` covers the rest.
4. If the AI guide should mention it, update `templates/ai/AGENTS.md.j2`
   and the skill that covers the task.

## A new checklist option

1. A field on `ProjectOptions` and a `ChecklistOption(key, label, default)`
   in `options.CHECKLIST` (`key` equals the field name; it is what
   `.moarch-py.yaml` records under `stack`).
2. Its packages in `dependencies.dependencies_for`.
3. Its files: catalog entries with `when=lambda options: options.<key>`
   (as a named module-level function, like `_docker`).
4. Anything it changes in shared files (`docker-compose.yml`, `ci.yml`,
   `README.md`, `AGENTS.md`) as `{% if options.<key> %}` blocks.
5. Tests: one that it is present when on, and the existing
   `test_switched_off_options_leave_no_files` extended for "off".

## An option beyond "What to generate" (auth, security, worker, realtime, services)

1. The option: a field on `ProjectOptions` and a `ChecklistOption` in its
   `Checklist` (with `needs=` if it cannot work alone); a name in
   `commands.CREATE_TARGETS` if a `create` command adds it.
2. Its files: `_file(...)` entries in `option_catalog.py` with `when=_on("<key>")`.
3. What it adds to a shared file (`main.py`, `config.py`, `.env.example`,
   `docker-compose.yml`, `conftest.py`, `README.md`, `AGENTS.md`, a module's
   `models.py`…): `_insert(slug, path, anchor, when, text=… | template=…)`,
   never an `{% if %}` in the shared template. Something that only exists
   with a second option is an insert whose `when` is `_on("a", "b")`.
4. Its packages in `dependencies._option_packages`, its guide section, its
   tests (with fakes, so no server is needed).
5. `tests/test_options.py` picks it up: it renders it alone, with every other
   option, and checks that adding it later equals ticking it at `init`.

## Done when

`uv run python -m pytest` passes, then `try-scaffold` for the option on and off.

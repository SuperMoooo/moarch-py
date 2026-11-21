---
name: make-readable
description: "Make code in the moarch-py CLI or its templates easier to read without changing what it does: names that say what a variable, function or class is, functions that do one thing, and comments that explain why wherever the logic is not obvious. Use when asked to clean up, clarify, rename, document or comment code, or when code is hard to follow."
---

# Make code readable

The goal is code someone new can follow on the first read. Behaviour does not
change: the same command writes the same files, and every test that passed
before passes after.

## 0. Before touching anything

- Read the code **and its callers** (search for each name you might change).
- Run `uv run python -m pytest` once, so you know what "still passes" means.
- Keep a readability change apart from a behaviour change; report a bug you
  find separately.
- In a template, remember there are two readers: the person editing the
  template here, and the person reading the generated file in their project.
  Generated output matters more.

## 1. Names

A name says **what the thing is**, in the words of the domain (projects,
features, templates, anchors, the manifest), not how it is stored.

| Instead of | Write | Why |
|---|---|---|
| `data`, `info`, `obj`, `tmp`, `res`, `ctx` | `plan`, `manifest`, `feature`, `template_context` | Says what it holds |
| `files_list`, `spec_dict` | `generated_files`, `specs_by_slug` | Plural for collections; no type in the name |
| `flag`, `check`, `ok` (a bool) | `is_installed`, `has_anchor`, `take_defaults` | A bool reads as a yes/no question |
| `handle()`, `process()`, `do()` | `plan_feature()`, `insert_at_anchor()` | A verb for what it does |
| `get_x()` that also writes | `write_manifest()` | No hidden side effects |
| `cfg`, `opts`, `p`, `s` | `settings`, `options`, `path`, `source` | No abbreviations (`id`, `url`, `uv`, `db` are fine) |
| `not_disabled` | `is_enabled` | No double negatives |
| `TemplateManager`, `helpers.py` | `render.py`, `catalog.py` | Name the job, not "manager" or "helper" |

PEP 8: `PascalCase` classes, `snake_case` everything else, `UPPER_SNAKE`
constants, `_private` for module-internal names. A rename of anything a
template reads (`name.package`, `options.docker`) must be made in every
template too — search `src/moarch_py/templates/`.

## 2. Structure

- **One job per function**; split anything you need "and" to describe.
- **Pure first:** generation (`scaffold.py`) stays free of disk and
  subprocesses; side effects belong in `commands.py`.
- **Return early** instead of nesting; give complex conditions a name.
- **No magic values:** a named constant (`PYTHON_VERSION`, `MANIFEST_FILE`).
- Delete commented-out code and unused imports.

## 3. Comments and docstrings

Code says what; a comment says **why**, wherever a reader would stop: an
order that matters ("hash after ruff formats, or update sees an edit"), a
platform quirk ("cp1252 consoles cannot print ✓"), a Jinja trick
(`{% raw %}`), a choice that looks odd. Every public module, class and
function gets a one-line docstring. Never a comment that repeats the code;
never one that is no longer true.

## 4. Report

1. Renames as `old → new`, with why where not obvious.
2. What you split, moved or commented, by `path:line`.
3. What you left alone on purpose (a name templates or `.moarch-py.yaml` depend on).

## Done when

`uv run python -m ruff format --check .`, `uv run python -m ruff check .` and `uv run python -m pytest` pass.

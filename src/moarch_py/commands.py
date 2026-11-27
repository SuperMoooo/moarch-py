"""What `init` and each `create` command do, step by step, including disk and uv."""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from moarch_py.dependencies import dependencies_for
from moarch_py.file_plan import FilePlan
from moarch_py.manifest import MANIFEST_FILE, ProjectManifest, hash_content
from moarch_py.naming import ModelName, ModuleName, ProjectName
from moarch_py.options import (
    OPTIONS_BY_KEY,
    Broker,
    Database,
    OptionsError,
    ProjectOptions,
    default_keys,
    resolve_needs,
)
from moarch_py.presets import PRESETS_BY_SLUG, InitPreset
from moarch_py.pyproject_file import build_pyproject, read_project_name
from moarch_py.scaffold import (
    PYTHON_VERSION,
    load_manifest,
    options_from_manifest,
    plan_model,
    plan_module,
    plan_options,
    plan_project,
)
from moarch_py.terminal import FAILED, OK, WARNING, console
from moarch_py.uv_runner import CommandFailedError, run, uv_version
from moarch_py.wizard import ask_checklists, ask_database, ask_preset

# `python -m ruff`, not the `.venv/Scripts/ruff.exe` launcher: antivirus
# heuristics (AVG/Avast Auto-Sandbox) treat every new launcher in a fresh venv
# as an unknown program and sandbox it, which can freeze a Windows machine.
# python.exe is a known, signed binary, so running tools through it is not flagged.
RUFF = ["uv", "run", "python", "-m", "ruff"]


class UsageError(Exception):
    """A problem with how the command was called; shown without a traceback."""


@dataclass(frozen=True)
class InitRequest:
    """Everything `moarch-py init` was called with."""

    name: str | None
    take_defaults: bool
    database: Database | None
    dry_run: bool
    force: bool
    install: bool
    preset: str | None = None
    broker: Broker | None = None


def resolve_project_root(name: str | None) -> tuple[Path, ProjectName]:
    """Where the project goes and what it is called.

    With a name, a new folder of that name. Without one, the current folder,
    named by its existing pyproject.toml (after `uv init`) or by the folder.
    """
    if name:
        project_name = ProjectName.parse(name)
        root = Path.cwd() / project_name.distribution
        if root.exists() and any(root.iterdir()):
            raise UsageError(
                f"{root} already exists and is not empty. Run `moarch-py init` inside it "
                "to scaffold it in place, or pick another name."
            )
        return root, project_name
    root = Path.cwd()
    if (root / MANIFEST_FILE).exists():
        raise UsageError(f"{root} is already a moarch-py project ({MANIFEST_FILE} exists).")
    existing_name = read_project_name(root)
    return root, ProjectName.parse(existing_name or root.name)


def _find_preset(slug: str | None) -> InitPreset | None:
    if slug is None:
        return None
    if slug not in PRESETS_BY_SLUG:
        raise UsageError(f"No preset '{slug}'. Choose one of: {', '.join(PRESETS_BY_SLUG)}.")
    return PRESETS_BY_SLUG[slug]


def collect_options(project_name: ProjectName, request: InitRequest) -> ProjectOptions:
    """The answers: from flags with `--all` or a preset off a terminal, otherwise the wizard."""
    if request.take_defaults and request.preset:
        raise UsageError("--all and --preset cannot be combined: a preset is its own defaults.")
    preset = _find_preset(request.preset)
    database = request.database or (Database.POSTGRES if not sys.stdin.isatty() else None)
    try:
        if request.take_defaults:
            return ProjectOptions.from_checklist(
                project_name,
                request.database or Database.POSTGRES,
                default_keys(),
                broker=request.broker or Broker.NONE,
            )
        if preset is not None and not sys.stdin.isatty():
            return ProjectOptions.from_checklist(
                project_name,
                database or Database.POSTGRES,
                preset.ticked,
                broker=request.broker or preset.broker,
            )
        if not sys.stdin.isatty():
            raise UsageError("No terminal to ask questions in. Pass --all or --preset <slug>.")
        preset = preset or ask_preset()
        database = request.database or ask_database()
        ticked, broker = ask_checklists(preset, request.broker)
        return ProjectOptions.from_checklist(project_name, database, ticked, broker=broker)
    except OptionsError as error:
        raise UsageError(str(error)) from error


def run_init(request: InitRequest) -> None:
    """`moarch-py init`: plans every file, writes them, installs, formats, records."""
    root, project_name = resolve_project_root(request.name)
    options = collect_options(project_name, request)
    detected_uv = uv_version()
    if request.install and detected_uv is None:
        raise UsageError(
            "uv is not installed: https://docs.astral.sh/uv/getting-started/installation/ "
            "(or pass --no-install to only write the files)."
        )

    plan, manifest = plan_project(root, options, uv_version=detected_uv)
    dependencies = dependencies_for(options)
    pyproject_path = root / "pyproject.toml"
    existing_pyproject = (
        pyproject_path.read_text(encoding="utf-8") if pyproject_path.exists() else None
    )
    plan.edit(
        "pyproject.toml",
        build_pyproject(
            existing_pyproject,
            options,
            python_version=PYTHON_VERSION,
            # Without `uv add`, list the names so the file still says what to install.
            unpinned_dependencies=None
            if request.install
            else (dependencies.runtime, dependencies.development),
        ),
    )
    if not (root / ".env").exists():
        plan.add(".env", plan.files[".env.example"])

    if request.dry_run:
        _print_plan(plan, title=f"Would create {project_name.distribution} in {root}")
        console.print(f"Runtime packages: {', '.join(dependencies.runtime)}")
        console.print(f"Dev packages:     {', '.join(dependencies.development)}")
        return

    root.mkdir(parents=True, exist_ok=True)
    plan.write(force=request.force)
    console.print(f"{OK} Wrote {len(plan.files)} files in {root}")

    if request.install:
        _install(root, dependencies.runtime, dependencies.development)
    _init_git(root)

    # Hash what is on disk *after* formatting, so `moarch-py update` does not
    # mistake ruff's reflow for a user's edit.
    on_disk = {path: (root / path).read_text(encoding="utf-8") for path in manifest.files}
    manifest.record(on_disk)
    (root / MANIFEST_FILE).write_text(manifest.render(), encoding="utf-8", newline="\n")
    _print_next_steps(root, options, installed=request.install, named=request.name is not None)


def _install(root: Path, runtime: list[str], development: list[str]) -> None:
    """Adds the packages with uv (newest compatible versions), then formats the code."""
    try:
        with console.status("Resolving and installing packages with uv..."):
            run(["uv", "add", *runtime], cwd=root)
            run(["uv", "add", "--dev", *development], cwd=root)
        console.print(f"{OK} Installed packages, wrote uv.lock")
        # Templates are readable at any line length; ruff makes them match
        # the project's own style, so `ruff format --check` passes from day one.
        run([*RUFF, "format", "."], cwd=root)
        run([*RUFF, "check", "--fix", "--quiet", "."], cwd=root)
        console.print(f"{OK} Formatted with ruff")
    except CommandFailedError as error:
        console.print(f"{FAILED} {error}")
        console.print(
            "The files are written. Fix the problem above, then run in the project:\n"
            f"  uv add {' '.join(runtime)}\n  uv add --dev {' '.join(development)}"
        )
        raise SystemExit(1) from error


def _init_git(root: Path) -> None:
    """Starts a git repository unless the folder is already inside one."""
    if shutil.which("git") is None:
        return
    try:
        run(["git", "rev-parse", "--is-inside-work-tree"], cwd=root)
    except CommandFailedError:
        run(["git", "init", "--quiet"], cwd=root)
        console.print(f"{OK} Started a git repository")


def _print_plan(plan: FilePlan, *, title: str) -> None:
    console.print(f"[bold]{title}[/]")
    for path in sorted(plan.files):
        marker = "~" if path in plan.edits and (plan.root / path).exists() else "+"
        console.print(f"  {marker} {path}")


def _print_next_steps(root: Path, options: ProjectOptions, *, installed: bool, named: bool) -> None:
    steps = []
    if named:
        steps.append(f"cd {root.name}")
    if not installed:
        steps.append("uv sync")
    if options.migrations and options.database.runs_in_container:
        steps.append("docker compose up -d db        # or point DATABASE_URL in .env at yours")
    if options.migrations:
        steps.append("uv run alembic upgrade head")
    steps.append(f"uv run fastapi dev src/{options.name.package}/main.py")
    steps.append("moarch-py create module orders    # your first module")
    console.print("\n[bold]Next:[/]")
    for step in steps:
        console.print(f"  {step}")


@dataclass(frozen=True)
class CreateModuleRequest:
    """Everything `moarch-py create module` was called with."""

    name: str
    project_root: Path
    dry_run: bool
    force: bool


def run_create_module(request: CreateModuleRequest) -> None:
    """`moarch-py create module <name>`: public.py, six layers and tests, registered."""
    root = request.project_root.resolve()
    manifest = load_manifest(root)
    module = ModuleName.parse(request.name)
    if module.package in manifest.modules and not request.force:
        raise UsageError(f"Module '{module.package}' already exists (--force to regenerate it).")

    plan = plan_module(root, manifest, module)
    if request.dry_run:
        _print_plan(plan, title=f"Would create module {module.package}")
        return
    if module.package not in manifest.modules:
        manifest.modules.append(module.package)
    _write_and_record(root, manifest, plan, force=request.force)

    console.print(f"{OK} Created module [bold]{module.package}[/] ({len(plan.files)} files)")
    console.print(f"  route: /api/v1/{module.url_path}   model: {module.model_class}")
    module_dir = f"src/{manifest.package}/modules/{module.package}"
    console.print(f"  other modules import only {module_dir}/public.py")
    console.print("\n[bold]Next:[/]")
    console.print(f"  edit the columns in {module_dir}/models.py")
    if "migrations" in manifest.stack:
        console.print(f'  uv run alembic revision --autogenerate -m "create {module.table}"')
        console.print("  uv run alembic upgrade head")
    console.print("  uv run pytest")
    console.print("  uv run lint-imports              # modules talk only through public.py")


def _format_if_possible(root: Path, paths: list[str]) -> None:
    """Formats [paths] with the project's ruff when its environment exists."""
    # ruff formats Python only; handed a Markdown or YAML path it fails, and
    # the import sorting after it would never run.
    paths = [path for path in paths if path.endswith(".py")]
    if not paths or not (root / ".venv").exists():
        return
    try:
        run([*RUFF, "format", *paths], cwd=root)
        run([*RUFF, "check", "--fix", "--quiet", *paths], cwd=root)
    except CommandFailedError as error:
        console.print(f"{WARNING} Could not format the new files: {error}")


def _write_and_record(
    root: Path, manifest: ProjectManifest, plan: FilePlan, *, force: bool
) -> None:
    """Writes [plan], formats it, and records the hashes in `.moarch-py.yaml`."""
    # Decided before writing: an anchor file still exactly as moarch-py left it
    # stays "untouched" after this edit; one the user changed stays "edited".
    untouched_edits = {
        path
        for path in plan.edits
        if manifest.files.get(path) == hash_content((root / path).read_text(encoding="utf-8"))
    }
    plan.write(force=force)
    _format_if_possible(root, list(plan.files))

    recorded = [path for path in plan.files if path not in plan.edits or path in untouched_edits]
    manifest.record({path: (root / path).read_text(encoding="utf-8") for path in recorded})
    (root / MANIFEST_FILE).write_text(manifest.render(), encoding="utf-8", newline="\n")


@dataclass(frozen=True)
class CreateModelRequest:
    """Everything `moarch-py create model` was called with."""

    module: str
    name: str
    project_root: Path
    dry_run: bool


def run_create_model(request: CreateModelRequest) -> None:
    """`moarch-py create model <module> <name>`: a second model inside an existing module."""
    root = request.project_root.resolve()
    manifest = load_manifest(root)
    module_package = ModuleName.parse(request.module).package
    model = ModelName.parse(request.name)

    plan = plan_model(root, manifest, module_package, model)
    if request.dry_run:
        _print_plan(plan, title=f"Would add {model.model_class} to module {module_package}")
        return
    # Every file but the new test is an anchor edit, so there is nothing to force.
    _write_and_record(root, manifest, plan, force=False)

    module_dir = f"src/{manifest.package}/modules/{module_package}"
    console.print(
        f"{OK} Added [bold]{model.model_class}[/] to module {module_package} "
        f"(table {model.table}): model, schemas, repository and a test"
    )
    console.print("\n[bold]Next:[/]")
    console.print(f"  edit the columns in {module_dir}/models.py")
    console.print('  link it to its parent with a ForeignKey("<table>.id") column there')
    console.print(f"  use {model.model_class}Repository from {module_dir}/service.py")
    if "migrations" in manifest.stack:
        console.print(f'  uv run alembic revision --autogenerate -m "create {model.table}"')
        console.print("  uv run alembic upgrade head")
    console.print("  uv run pytest")


# What `create security|realtime|service|observability <name>` accepts, and the options each
# name adds. Names use dashes, as on the command line; keys are option fields.
CREATE_TARGETS: dict[str, dict[str, tuple[str, ...]]] = {
    "security": {
        "rate-limit": ("rate_limit",),
        "audit-log": ("audit_log",),
        "idempotency": ("idempotency",),
        "headers": ("security_headers",),
        "lockout": ("lockout",),
        "integrity": ("integrity",),
    },
    "realtime": {
        "websockets": ("websockets",),
        "sse": ("sse",),
    },
    "service": {
        "email": ("email",),
        "cache": ("cache",),
        "storage": ("storage",),
        "push": ("push",),
        "moderation": ("moderation",),
        "purchases": ("purchases",),
        # Before the Observability checklist these were services; kept so
        # existing scripts still work. `create observability` is the home now.
        "tracing": ("tracing",),
        "sentry": ("sentry",),
        "metrics": ("metrics",),
        "observability": ("tracing", "sentry", "metrics"),
    },
    "observability": {
        "tracing": ("tracing",),
        "sentry": ("sentry",),
        "metrics": ("metrics",),
        "all": ("tracing", "sentry", "metrics"),
    },
}


def keys_for(group: str, names: list[str]) -> set[str]:
    """The option keys that `create <group> <names…>` adds; UsageError for an unknown name."""
    targets = CREATE_TARGETS[group]
    unknown = [name for name in names if name not in targets]
    if unknown or not names:
        raise UsageError(
            f"Choose what to add: moarch-py create {group} <{'|'.join(targets)}> "
            f"(unknown: {', '.join(unknown) or 'none given'})."
        )
    return {key for name in names for key in targets[name]}


@dataclass(frozen=True)
class AddOptionsRequest:
    """Everything a `create <option>` command was called with."""

    keys: set[str]
    project_root: Path
    dry_run: bool
    install: bool
    broker: Broker | None = None


def run_add_options(request: AddOptionsRequest) -> None:
    """Adds checklist options to an existing project, as if `init` had ticked them.

    The same planner as `init` (scaffold.plan_options) writes the options'
    files and puts their snippets at the shared files' anchors, so a project
    that adds an option later ends the same as one that ticked it at `init`.
    """
    root = request.project_root.resolve()
    manifest = load_manifest(root)
    current = options_from_manifest(manifest)
    if request.broker and current.has_worker and request.broker is not current.broker:
        raise UsageError(
            f"This project's worker already uses {current.broker.value}; a project has one broker."
        )
    try:
        updated = current.with_added(request.keys, broker=request.broker)
    except OptionsError as error:
        raise UsageError(str(error)) from error
    if updated == current:
        console.print(f"{OK} Nothing to add: the project already has all of that.")
        return

    plan = plan_options(root, updated, previous=current, uv_version=uv_version())
    old_packages = dependencies_for(current)
    new_packages = dependencies_for(updated)
    runtime = [name for name in new_packages.runtime if name not in old_packages.runtime]
    development = [
        name for name in new_packages.development if name not in old_packages.development
    ]
    added = [key for key in updated.enabled if key not in current.enabled]
    if request.dry_run:
        _print_plan(plan, title=f"Would add {', '.join(added)}")
        console.print(f"Runtime packages: {', '.join(runtime) or 'none'}")
        console.print(f"Dev packages:     {', '.join(development) or 'none'}")
        return

    manifest.stack = updated.enabled
    manifest.broker = updated.broker.value
    _write_and_record(root, manifest, plan, force=False)
    console.print(f"{OK} Added {', '.join(OPTIONS_BY_KEY[key].label for key in added)}")
    _, needed_by = resolve_needs(request.keys | set(current.enabled))
    for key, by in sorted(needed_by.items()):
        if key in added:
            console.print(f"  + {OPTIONS_BY_KEY[key].label} (needed by {', '.join(by)})")
    if request.install and (runtime or development):
        _add_packages(root, runtime, development)
    _print_option_next_steps(root, updated)


def _add_packages(root: Path, runtime: list[str], development: list[str]) -> None:
    """`uv add` for what the new options need."""
    try:
        with console.status("Adding packages with uv..."):
            if runtime:
                run(["uv", "add", *runtime], cwd=root)
            if development:
                run(["uv", "add", "--dev", *development], cwd=root)
        console.print(f"{OK} Added {', '.join([*runtime, *development])}")
    except CommandFailedError as error:
        console.print(f"{FAILED} {error}")
        console.print(
            "The files are written. Add the packages by hand:\n"
            f"  uv add {' '.join(runtime)}\n  uv add --dev {' '.join(development)}"
        )
        raise SystemExit(1) from error


def _print_option_next_steps(root: Path, options: ProjectOptions) -> None:
    console.print("\n[bold]Next:[/]")
    if (root / ".env").exists():
        console.print("  copy the new keys from .env.example into your .env")
    if options.migrations:
        console.print('  uv run alembic revision --autogenerate -m "add <what you added>"')
        console.print("  uv run alembic upgrade head")
    console.print("  uv run pytest")
    console.print("  the guides in docs/ explain each part")

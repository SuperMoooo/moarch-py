"""Turns options into the files of a project or a module. No disk writes, no subprocesses.

Keeping generation pure is what lets `--dry-run` show exactly what a real run
writes, and lets the tests check every option combination in milliseconds.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from moarch_py import __version__
from moarch_py.catalog import PROJECT_SKILLS, ScaffoldSpec, specs_for
from moarch_py.file_plan import FilePlan, insert_at_anchor
from moarch_py.manifest import MANIFEST_FILE, ProjectManifest
from moarch_py.naming import ModelName, ModuleName, ProjectName
from moarch_py.options import Database, ProjectOptions
from moarch_py.render import render

# The version generated projects target. 3.12 is the most widely used Python
# in production (JetBrains/PSF Python Developers Survey 2025); a newer
# interpreter still runs these projects, since requires-python is a floor.
PYTHON_VERSION = "3.12"

# Used in the Dockerfile when uv's version cannot be detected.
FALLBACK_UV_IMAGE_TAG = "latest"


def project_context(options: ProjectOptions, *, uv_version: str | None) -> dict[str, Any]:
    """The variables every project template can read."""
    return {
        "name": options.name,
        "options": options,
        "database": options.database,
        "python_version": PYTHON_VERSION,
        "uv_version": uv_version or FALLBACK_UV_IMAGE_TAG,
        "moarch_version": __version__,
        "skills": PROJECT_SKILLS,
    }


def render_spec(spec: ScaffoldSpec, context: dict[str, Any]) -> str:
    """One catalog entry's file content."""
    return render(spec.template, {**context, **spec.extra})


def plan_project(
    root: Path, options: ProjectOptions, *, uv_version: str | None
) -> tuple[FilePlan, ProjectManifest]:
    """Every file `init` writes for [options] (pyproject.toml excepted), and its manifest."""
    context = project_context(options, uv_version=uv_version)
    plan = FilePlan(root)
    for spec in specs_for(options):
        plan.add(spec.path_for(options.name.package), render_spec(spec, context))
    manifest = ProjectManifest.new(
        package=options.name.package,
        database=options.database.value,
        stack=options.enabled,
    )
    manifest.record(plan.files)
    return plan, manifest


# The files `moarch-py create module` writes, relative to the module folder,
# with the template that renders each.
_MODULE_FILES: tuple[tuple[str, str], ...] = (
    ("__init__.py", "module/package_init.py.j2"),
    ("public.py", "module/public.py.j2"),
    ("models.py", "module/models.py.j2"),
    ("schemas.py", "module/schemas.py.j2"),
    ("repository.py", "module/repository.py.j2"),
    ("service.py", "module/service.py.j2"),
    ("mocks.py", "module/mocks.py.j2"),
    ("dependencies.py", "module/dependencies.py.j2"),
    ("router.py", "module/router.py.j2"),
)

# Its tests, relative to `tests/modules/<module>/`; `{module}` is the module's package.
_MODULE_TESTS: tuple[tuple[str, str], ...] = (
    ("test_{module}_api.py", "module/test_api.py.j2"),
    ("test_{module}_public.py", "module/test_public.py.j2"),
    ("test_{module}_mocks.py", "module/test_mocks.py.j2"),
)


class NotAMoarchProjectError(Exception):
    """Raised when a command that needs `.moarch-py.yaml` runs outside a moarch-py project."""


def load_manifest(root: Path) -> ProjectManifest:
    """The project's manifest, or NotAMoarchProjectError with what to do instead."""
    manifest = ProjectManifest.load(root)
    if manifest is None:
        raise NotAMoarchProjectError(
            f"No {MANIFEST_FILE} in {root}. Run this inside a project made by "
            "`moarch-py init`, or run `moarch-py init` here first."
        )
    return manifest


def plan_module(root: Path, manifest: ProjectManifest, module: ModuleName) -> FilePlan:
    """The module's files and tests, plus its registration at the two anchors."""
    project = ProjectName.parse(manifest.package)
    context = {
        "name": project,
        "module": module,
        "database": Database(manifest.database),
    }
    package_dir = f"src/{project.package}"
    module_dir = f"{package_dir}/modules/{module.package}"

    plan = FilePlan(root)
    for file_name, template in _MODULE_FILES:
        plan.add(f"{module_dir}/{file_name}", render(template, context))
    for test_name, template in _MODULE_TESTS:
        test_file = test_name.format(module=module.package)
        plan.add(f"tests/modules/{module.package}/{test_file}", render(template, context))

    router_path = f"{package_dir}/api/v1/router.py"
    router_source = (root / router_path).read_text(encoding="utf-8")
    module_import_path = f"{project.package}.modules.{module.package}"
    router_alias = f"{module.package}_router"
    router_source = insert_at_anchor(
        router_source,
        "router-imports",
        f"from {module_import_path}.router import router as {router_alias}",
        relative_path=router_path,
    )
    router_source = insert_at_anchor(
        router_source,
        "routers",
        f"api_router.include_router({router_alias})",
        relative_path=router_path,
    )
    plan.edit(router_path, router_source)

    models_path = f"{package_dir}/db/models.py"
    models_source = (root / models_path).read_text(encoding="utf-8")
    models_source = insert_at_anchor(
        models_source,
        "models",
        # Imported only so Base.metadata registers the table, hence the noqa.
        f"from {module_import_path}.models import {module.model_class}  # noqa: F401",
        relative_path=models_path,
    )
    plan.edit(models_path, models_source)
    return plan


# Where `create model` adds to a module's files: anchor → snippet template.
# Each snippet uses only imports its file already has, except the repository,
# which also gets the new model's import at `repository-imports`.
_MODEL_SNIPPETS: tuple[tuple[str, str, str], ...] = (
    ("models.py", "module-models", "model/models_snippet.py.j2"),
    ("schemas.py", "module-schemas", "model/schemas_snippet.py.j2"),
    ("repository.py", "module-repositories", "model/repository_snippet.py.j2"),
)


class UnknownModuleError(Exception):
    """Raised when `create model` names a module the project does not have."""


class ModelExistsError(Exception):
    """Raised when the module's models.py already defines a class of that name."""


def plan_model(
    root: Path, manifest: ProjectManifest, module_package: str, model: ModelName
) -> FilePlan:
    """A new model inside an existing module: its class, schemas, repository and test.

    It adds to the module's own files at their `# moarch:` anchors rather than
    making new ones, because the models of one module change together and
    belong side by side. No service or router: how the model is used (often
    through the module's main service) is the module's decision.
    """
    project = ProjectName.parse(manifest.package)
    module_dir = f"src/{project.package}/modules/{module_package}"
    if not (root / module_dir).is_dir():
        raise UnknownModuleError(
            f"No module '{module_package}' in {root / module_dir}. "
            f"Create it first: moarch-py create module {module_package}"
        )
    models_source = (root / module_dir / "models.py").read_text(encoding="utf-8")
    if f"class {model.model_class}(" in models_source:
        raise ModelExistsError(f"{module_dir}/models.py already defines {model.model_class}.")

    context = {"name": project, "model": model, "module_package": module_package}
    plan = FilePlan(root)
    for file_name, anchor, template in _MODEL_SNIPPETS:
        path = f"{module_dir}/{file_name}"
        source = plan.files.get(path) or (root / path).read_text(encoding="utf-8")
        plan.edit(
            path,
            insert_at_anchor(source, anchor, render(template, context), relative_path=path),
        )

    module_import_path = f"{project.package}.modules.{module_package}"
    repository_path = f"{module_dir}/repository.py"
    plan.edit(
        repository_path,
        insert_at_anchor(
            plan.files[repository_path],
            "repository-imports",
            f"from {module_import_path}.models import {model.model_class}",
            relative_path=repository_path,
        ),
    )

    registry_path = f"src/{project.package}/db/models.py"
    plan.edit(
        registry_path,
        insert_at_anchor(
            (root / registry_path).read_text(encoding="utf-8"),
            "models",
            # Imported only so Base.metadata registers the table, hence the noqa.
            f"from {module_import_path}.models import {model.model_class}  # noqa: F401",
            relative_path=registry_path,
        ),
    )
    plan.add(
        f"tests/modules/{module_package}/test_{model.table}_repository.py",
        render("model/test_repository.py.j2", context),
    )
    return plan

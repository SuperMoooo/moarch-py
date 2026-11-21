"""What `init` and `create module` generate, for each option, without touching uv."""

import ast
import itertools
import json
from pathlib import Path

import pytest
import yaml

from moarch_py.catalog import CATALOG, PROJECT_SKILLS
from moarch_py.naming import ModuleName, ProjectName
from moarch_py.options import CHECKLIST, Database, ProjectOptions
from moarch_py.scaffold import plan_module, plan_project

NAME = ProjectName.parse("shop-api")


def _plan(tmp_path: Path, **overrides: object) -> dict[str, str]:
    options = ProjectOptions.with_defaults(NAME, Database.POSTGRES)
    options = ProjectOptions(**{**options.__dict__, **overrides})  # type: ignore[arg-type]
    plan, _ = plan_project(tmp_path, options, uv_version="0.12.11")
    return plan.files


def test_catalog_slugs_are_unique() -> None:
    slugs = [spec.slug for spec in CATALOG]
    assert len(slugs) == len(set(slugs))


# Every combination of database and checklist: 3 x 2^5 = 96 projects.
_COMBINATIONS = [
    (database, ticked)
    for database in Database
    for count in range(len(CHECKLIST) + 1)
    for ticked in itertools.combinations([o.key for o in CHECKLIST], count)
]


@pytest.mark.parametrize(("database", "ticked"), _COMBINATIONS)
def test_every_combination_renders_valid_python_yaml_and_json(
    tmp_path: Path, database: Database, ticked: tuple[str, ...]
) -> None:
    options = ProjectOptions.from_checklist(NAME, database, set(ticked))
    plan, _ = plan_project(tmp_path, options, uv_version=None)

    for path, content in plan.files.items():
        if path.endswith(".py"):
            ast.parse(content, filename=path)
        elif path.endswith((".yml", ".yaml")):
            yaml.safe_load(content)
        elif path.endswith(".json"):
            # VS Code's files are JSONC: drop the `//` comment lines first.
            lines = [line for line in content.splitlines() if not line.strip().startswith("//")]
            json.loads("\n".join(lines))
        if path.endswith("SKILL.md"):
            frontmatter = content.split("---")[1]
            assert yaml.safe_load(frontmatter)["name"].startswith("moarch-")


def test_switched_off_options_leave_no_files(tmp_path: Path) -> None:
    files = _plan(tmp_path, migrations=False, docker=False, ci=False, pre_commit=False, ai=False)

    unexpected = [
        path
        for path in files
        if path.startswith(("migrations/", ".github/", ".agents/", ".claude/"))
        or path in {"alembic.ini", "Dockerfile", "docker-compose.yml", "AGENTS.md", "CLAUDE.md"}
    ]
    assert unexpected == []


def test_the_ai_guide_ships_every_skill_for_both_agent_folders(tmp_path: Path) -> None:
    files = _plan(tmp_path)

    for slug, _ in PROJECT_SKILLS:
        assert f".agents/skills/moarch-{slug}/SKILL.md" in files
        pointer = files[f".claude/skills/moarch-{slug}/SKILL.md"]
        assert f".agents/skills/moarch-{slug}/SKILL.md" in pointer
    assert "@AGENTS.md" in files["CLAUDE.md"]
    assert "moarch-make-readable" in files["AGENTS.md"]
    assert "moarch-explain" in files["AGENTS.md"]


def test_ruff_is_the_editor_formatter_and_linter(tmp_path: Path) -> None:
    settings = _plan(tmp_path)[".vscode/settings.json"]

    assert '"editor.defaultFormatter": "charliermarsh.ruff"' in settings
    assert '"source.fixAll.ruff"' in settings
    assert "charliermarsh.ruff" in _plan(tmp_path)[".vscode/extensions.json"]


def test_the_dockerfile_targets_the_project_python_and_uv(tmp_path: Path) -> None:
    dockerfile = _plan(tmp_path)["Dockerfile"]

    assert "FROM python:3.12-slim AS builder" in dockerfile
    assert "ghcr.io/astral-sh/uv:0.12.11" in dockerfile
    assert '"shop_api.main:app"' in dockerfile
    assert "USER app" in dockerfile


def test_sqlite_projects_get_no_database_service(tmp_path: Path) -> None:
    compose = yaml.safe_load(_plan(tmp_path, database=Database.SQLITE)["docker-compose.yml"])

    assert set(compose["services"]) == {"api"}


def test_postgres_compose_waits_for_a_healthy_database(tmp_path: Path) -> None:
    compose = yaml.safe_load(_plan(tmp_path)["docker-compose.yml"])

    assert compose["services"]["api"]["depends_on"]["db"]["condition"] == "service_healthy"
    assert "@db:5432/shop_api" in compose["services"]["api"]["environment"]["DATABASE_URL"]


def _write_project(root: Path) -> None:
    from moarch_py.manifest import ProjectManifest

    options = ProjectOptions.with_defaults(NAME, Database.POSTGRES)
    plan, manifest = plan_project(root, options, uv_version=None)
    plan.write()
    (root / ".moarch-py.yaml").write_text(manifest.render(), encoding="utf-8")
    assert ProjectManifest.load(root) is not None


def test_a_module_writes_every_layer_and_registers_at_both_anchors(tmp_path: Path) -> None:
    from moarch_py.manifest import ProjectManifest

    _write_project(tmp_path)
    manifest = ProjectManifest.load(tmp_path)
    assert manifest is not None

    plan = plan_module(tmp_path, manifest, ModuleName.parse("order_items"))

    module_dir = "src/shop_api/modules/order_items"
    for layer in ("public", "models", "schemas", "repository", "service", "dependencies", "router"):
        ast.parse(plan.files[f"{module_dir}/{layer}.py"])
    assert "tests/modules/order_items/test_order_items_api.py" in plan.files
    ast.parse(plan.files["tests/modules/order_items/test_order_items_public.py"])
    router = plan.files["src/shop_api/api/v1/router.py"]
    assert "api_router.include_router(order_items_router)" in router
    models = plan.files["src/shop_api/db/models.py"]
    assert "from shop_api.modules.order_items.models import OrderItem" in models
    assert '@router.get("/{order_item_id}")' in plan.files[f"{module_dir}/router.py"]


def test_public_hands_out_a_schema_and_never_the_model(tmp_path: Path) -> None:
    from moarch_py.manifest import ProjectManifest

    _write_project(tmp_path)
    manifest = ProjectManifest.load(tmp_path)
    assert manifest is not None

    public = plan_module(tmp_path, manifest, ModuleName.parse("orders")).files[
        "src/shop_api/modules/orders/public.py"
    ]

    assert '__all__ = ["OrderRead", "find_order"]' in public
    assert "-> OrderRead | None:" in public
    assert ".models import" not in public
    assert "commit" not in public.split('"""', 2)[2].replace("never commits", "")


def test_the_import_contract_covers_every_module_without_listing_them() -> None:
    import tomllib

    from moarch_py.pyproject_file import build_pyproject

    options = ProjectOptions.with_defaults(NAME, Database.POSTGRES)
    pyproject = tomllib.loads(build_pyproject(None, options, python_version="3.12"))

    import_linter = pyproject["tool"]["importlinter"]
    assert import_linter["root_packages"] == ["shop_api"]
    (contract,) = import_linter["contracts"]
    assert contract["type"] == "independence"
    assert contract["modules"] == ["shop_api.modules.*"]
    assert contract["ignore_imports"] == ["shop_api.modules.** -> shop_api.modules.*.public"]
    assert contract["unmatched_ignore_imports_alerting"] == "none"


def test_ci_and_pre_commit_check_the_module_boundaries(tmp_path: Path) -> None:
    files = _plan(tmp_path)

    steps = yaml.safe_load(files[".github/workflows/ci.yml"])["jobs"]["quality"]["steps"]
    assert {"name": "Module boundaries", "run": "uv run lint-imports"} in steps
    hooks = yaml.safe_load(files[".pre-commit-config.yaml"])["repos"][0]["hooks"]
    assert any(hook["id"] == "lint-imports" and not hook["pass_filenames"] for hook in hooks)


def test_import_linter_is_a_dev_dependency() -> None:
    from moarch_py.dependencies import dependencies_for

    options = ProjectOptions.with_defaults(NAME, Database.SQLITE)
    assert "import-linter" in dependencies_for(options).development


def test_a_0_1_0_manifest_with_features_still_loads_its_modules(tmp_path: Path) -> None:
    from moarch_py.manifest import ProjectManifest

    (tmp_path / ".moarch-py.yaml").write_text(
        "version: 0.1.0\npackage: shop_api\ndatabase: postgres\nfeatures: [orders]\n",
        encoding="utf-8",
    )

    manifest = ProjectManifest.load(tmp_path)

    assert manifest is not None
    assert manifest.modules == ["orders"]
    assert "modules:" in manifest.render()


def _write_project_with_orders(root: Path) -> None:
    """A project on disk with the orders module written, as `create module` leaves it."""
    from moarch_py.manifest import ProjectManifest

    _write_project(root)
    manifest = ProjectManifest.load(root)
    assert manifest is not None
    plan_module(root, manifest, ModuleName.parse("orders")).write()


def test_a_model_joins_its_module_files_at_their_anchors(tmp_path: Path) -> None:
    from moarch_py.manifest import ProjectManifest
    from moarch_py.naming import ModelName
    from moarch_py.scaffold import plan_model

    _write_project_with_orders(tmp_path)
    manifest = ProjectManifest.load(tmp_path)
    assert manifest is not None

    plan = plan_model(tmp_path, manifest, "orders", ModelName.parse("order_lines"))

    module_dir = "src/shop_api/modules/orders"
    for layer in ("models", "schemas", "repository"):
        source = plan.files[f"{module_dir}/{layer}.py"]
        ast.parse(source)
        assert f"# moarch:module-{'repositories' if layer == 'repository' else layer}" in source
    assert "class Order(" in plan.files[f"{module_dir}/models.py"]
    assert '__tablename__ = "order_lines"' in plan.files[f"{module_dir}/models.py"]
    assert "class OrderLineRead(BaseModel):" in plan.files[f"{module_dir}/schemas.py"]
    repository = plan.files[f"{module_dir}/repository.py"]
    assert "from shop_api.modules.orders.models import OrderLine\n" in repository
    assert "class OrderLineRepository(BaseRepository[OrderLine]):" in repository
    registry = plan.files["src/shop_api/db/models.py"]
    assert "from shop_api.modules.orders.models import OrderLine  # noqa: F401" in registry
    ast.parse(plan.files["tests/modules/orders/test_order_lines_repository.py"])
    assert plan.edits == set(plan.files) - {"tests/modules/orders/test_order_lines_repository.py"}


def test_a_model_needs_an_existing_module(tmp_path: Path) -> None:
    from moarch_py.manifest import ProjectManifest
    from moarch_py.naming import ModelName
    from moarch_py.scaffold import UnknownModuleError, plan_model

    _write_project(tmp_path)
    manifest = ProjectManifest.load(tmp_path)
    assert manifest is not None

    with pytest.raises(UnknownModuleError, match="moarch-py create module billing"):
        plan_model(tmp_path, manifest, "billing", ModelName.parse("invoices"))


def test_a_model_the_module_already_has_is_refused(tmp_path: Path) -> None:
    from moarch_py.manifest import ProjectManifest
    from moarch_py.naming import ModelName
    from moarch_py.scaffold import ModelExistsError, plan_model

    _write_project_with_orders(tmp_path)
    manifest = ProjectManifest.load(tmp_path)
    assert manifest is not None

    with pytest.raises(ModelExistsError):
        plan_model(tmp_path, manifest, "orders", ModelName.parse("orders"))


def test_a_module_without_the_anchor_gets_the_snippet_to_paste(tmp_path: Path) -> None:
    from moarch_py.file_plan import AnchorNotFoundError
    from moarch_py.manifest import ProjectManifest
    from moarch_py.naming import ModelName
    from moarch_py.scaffold import plan_model

    _write_project_with_orders(tmp_path)
    models_path = tmp_path / "src/shop_api/modules/orders/models.py"
    models_path.write_text(
        models_path.read_text(encoding="utf-8").replace("# moarch:module-models", ""),
        encoding="utf-8",
    )
    manifest = ProjectManifest.load(tmp_path)
    assert manifest is not None

    with pytest.raises(AnchorNotFoundError, match="class OrderLine"):
        plan_model(tmp_path, manifest, "orders", ModelName.parse("order_lines"))

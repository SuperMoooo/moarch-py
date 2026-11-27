---
name: release
description: "Release a new moarch-py version to PyPI: pick the semver bump, update pyproject.toml and CHANGELOG.md, run every check, tag, and publish. Use when asked to release, publish, bump the version or cut a tag."
---

# Release

1. **Pick the bump** from what changed since the last tag
   (`git log $(git describe --tags --abbrev=0)..HEAD --oneline`):
   - patch: fixes to templates or the CLI, no new option or command;
   - minor: a new command, option, generated file or skill;
   - major: a command, flag or generated layout that works differently.
2. **Version**, usually bumped already: every change bumps it (AGENTS.md →
   *Every change bumps the version*); confirm it is past the last tag.
   It lives in `pyproject.toml` only (`moarch_py.__version__` reads it from
   the installed metadata): `uv version --bump <major|minor|patch>`.
   Skip the bump when no tag exists yet and `uv version --short` is already
   the version to release (the first release): bumping then makes the tag
   and `pyproject.toml` disagree, and `release.yml` refuses to publish.
   Before tagging, check `uv version --short` equals the tag without its `v`.
3. **CHANGELOG.md**: a newest-first `## <version> — <date>` entry, written for
   users: what they can now do, what changed in generated projects, and what
   to run (`moarch-py update …`) to get it.
4. **Checks:** `uv run python -m ruff format --check .`, `uv run python -m ruff check .`,
   `uv run python -m pytest`, `uv run python -m pytest -m scaffold`, then `uv build` and inspect
   that the wheel contains `moarch_py/templates/` (`unzip -l dist/*.whl`).
5. **Hand over, as in the Flutter moarch:** stop here, do not commit. The
   maintainer commits the bump and the changelog.
6. **Tag and push the tag** once that commit exists:
   `git tag v<version> <commit> && git push origin v<version>`. Pushing the
   tag runs `.github/workflows/release.yml` (PyPI trusted publishing), so it
   is the publish step: push only the tag, and only for a commit the
   maintainer made for this release. Never run `uv publish` from a laptop
   with a token.

"""`.moarch-py.yaml`: the record moarch-py leaves in a project of what it generated.

It answers the one question a scaffolder otherwise cannot: is a generated file
still the one moarch-py wrote, or has someone edited it? `moarch-py update` compares
the hash recorded here with the file on disk and refreshes only untouched
files. The format matches the Flutter moarch's `.moarch.yaml`, so both tools read
the same way. Nothing here is needed for the project to run.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import yaml

from moarch_py import __version__

MANIFEST_FILE = ".moarch-py.yaml"


def hash_content(content: str) -> str:
    """A stable hash of a file's text, blind to CRLF versus LF.

    Normalising line endings means a Windows checkout of an untouched file
    (git may convert it to CRLF) is not mistaken for an edit.
    """
    normalised = content.replace("\r\n", "\n")
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()[:16]


@dataclass
class ProjectManifest:
    """The parsed `.moarch-py.yaml`."""

    version: str
    """The moarch-py version that last wrote the manifest."""

    generated_with: str
    """The moarch-py version `init` ran with; never restamped by later commands."""

    generated_at: str
    """When the manifest was last written, ISO 8601 in UTC."""

    package: str
    """The project's Python package under `src/`, so commands need not guess it."""

    database: str
    stack: list[str] = field(default_factory=list)
    """The checklist options `init` was given."""

    modules: list[str] = field(default_factory=list)
    """Every module made by `moarch-py create module`, in creation order."""

    files: dict[str, str] = field(default_factory=dict)
    """Project-relative path → `hash_content` of the file as moarch-py wrote it."""

    @classmethod
    def new(cls, *, package: str, database: str, stack: list[str]) -> ProjectManifest:
        """A manifest for a project `init` is generating now."""
        return cls(
            version=__version__,
            generated_with=__version__,
            generated_at=_now(),
            package=package,
            database=database,
            stack=stack,
        )

    @classmethod
    def load(cls, project_root: Path) -> ProjectManifest | None:
        """Reads the manifest, or returns None for a project moarch-py did not make."""
        path = project_root / MANIFEST_FILE
        if not path.exists():
            return None
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls(
            version=str(data.get("version", "")),
            generated_with=str(data.get("generated_with", data.get("version", ""))),
            generated_at=str(data.get("generated_at", "")),
            package=str(data["package"]),
            database=str(data.get("database", "")),
            stack=list(data.get("stack", [])),
            # 0.1.0 called them features; reading that key keeps those projects working.
            modules=list(data.get("modules", data.get("features", []))),
            files=dict(data.get("files", {})),
        )

    def record(self, files: dict[str, str]) -> None:
        """Remembers the hash of each file a command just wrote."""
        for relative_path, content in files.items():
            self.files[relative_path] = hash_content(content)

    def render(self) -> str:
        """The manifest as YAML, restamped with this moarch-py version."""
        self.version = __version__
        self.generated_at = _now()
        header = (
            "# Written by moarch-py — https://pypi.org/project/moarch-py/\n"
            "# Lets `moarch-py update` tell untouched generated files from edited ones.\n"
            "# Do not edit by hand.\n"
        )
        body = yaml.safe_dump(
            {
                "version": self.version,
                "generated_with": self.generated_with,
                "generated_at": self.generated_at,
                "package": self.package,
                "database": self.database,
                "stack": self.stack,
                "modules": self.modules,
                "files": dict(sorted(self.files.items())),
            },
            sort_keys=False,
        )
        return header + body


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()

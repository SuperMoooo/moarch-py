"""Files to write, collected in memory and checked before anything touches disk.

Every command builds a `FilePlan` first and writes it last. A conflict (a file
that already exists and was not made by moarch-py) is found while nothing has
been written yet, so a failed command never leaves a half-generated project.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


class FileConflictError(Exception):
    """Raised when a planned file already exists and `--force` was not given."""

    def __init__(self, paths: list[str]) -> None:
        self.paths = paths
        listed = "\n  ".join(paths)
        super().__init__(f"These files already exist (use --force to overwrite):\n  {listed}")


@dataclass
class FilePlan:
    """Project-relative path → content, in the order the files were planned."""

    root: Path
    files: dict[str, str] = field(default_factory=dict)
    edits: set[str] = field(default_factory=set)
    """Paths planned as edits of an existing file (an anchor insert), never a conflict."""

    def add(self, relative_path: str, content: str) -> None:
        """Plans a new file: [content] at [relative_path] (forward slashes on every OS)."""
        self.files[relative_path] = content

    def edit(self, relative_path: str, content: str) -> None:
        """Plans the new [content] of a file that exists and is meant to change."""
        self.files[relative_path] = content
        self.edits.add(relative_path)

    def conflicts(self) -> list[str]:
        """Planned paths that already exist on disk with different content."""
        clashing = []
        for relative_path, content in self.files.items():
            if relative_path in self.edits:
                continue
            target = self.root / relative_path
            if target.exists() and target.read_text(encoding="utf-8") != content:
                clashing.append(relative_path)
        return clashing

    def write(self, *, force: bool = False) -> list[str]:
        """Writes every planned file and returns the paths written.

        Raises `FileConflictError` before writing anything if a file would be
        overwritten and [force] is false.
        """
        clashing = self.conflicts()
        if clashing and not force:
            raise FileConflictError(clashing)
        for relative_path, content in self.files.items():
            target = self.root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            # newline="\n": generated files use LF on Windows too, so a
            # project committed from Windows has no CRLF churn in git.
            target.write_text(content, encoding="utf-8", newline="\n")
        return list(self.files)


class AnchorNotFoundError(Exception):
    """Raised when a file no longer has the `# moarch:<name>` line to insert at."""

    def __init__(self, relative_path: str, anchor: str, snippet: str) -> None:
        self.relative_path = relative_path
        self.anchor = anchor
        self.snippet = snippet
        super().__init__(
            f"'# moarch:{anchor}' is missing from {relative_path}. "
            f"Add this by hand where it belongs:\n\n{snippet}"
        )


def insert_at_anchor(source: str, anchor: str, snippet: str, *, relative_path: str) -> str:
    """Returns [source] with [snippet] inserted on the lines above `# moarch:<anchor>`.

    Markdown files mark the spot with `<!-- moarch:<anchor> -->` instead, since
    a `#` line there would be a heading. The snippet takes the anchor's
    indentation, so an anchor inside a function body gets indented code.
    Inserting the same snippet twice is a no-op, which makes `create` safe to
    re-run.
    """
    markers = {f"# moarch:{anchor}", f"<!-- moarch:{anchor} -->"}
    lines = source.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.strip() not in markers:
            continue
        indent = line[: len(line) - len(line.lstrip())]
        snippet_lines = [f"{indent}{text}\n" if text else "\n" for text in snippet.splitlines()]
        already_there = "".join(snippet_lines) in "".join(lines[:index])
        if already_there:
            return source
        return "".join([*lines[:index], *snippet_lines, *lines[index:]])
    raise AnchorNotFoundError(relative_path, anchor, snippet)

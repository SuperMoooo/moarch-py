"""Runs uv (and other tools) in the generated project."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path


class ToolMissingError(Exception):
    """Raised when uv is not on PATH."""


class CommandFailedError(Exception):
    """Raised when a command in the generated project exits non-zero."""

    def __init__(self, command: list[str], output: str) -> None:
        self.command = command
        self.output = output
        super().__init__(f"`{' '.join(command)}` failed:\n{output}")


def uv_version() -> str | None:
    """The installed uv's version (`0.12.11`), or None when uv is not installed."""
    if shutil.which("uv") is None:
        return None
    output = subprocess.run(["uv", "--version"], capture_output=True, text=True, check=False).stdout
    match = re.search(r"\d+\.\d+\.\d+", output)
    return match.group(0) if match else None


def run(command: list[str], *, cwd: Path) -> str:
    """Runs [command] in [cwd] and returns its output; raises CommandFailedError on failure."""
    if shutil.which(command[0]) is None:
        raise ToolMissingError(f"`{command[0]}` is not installed or not on PATH.")
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    output = (completed.stdout + completed.stderr).strip()
    if completed.returncode != 0:
        raise CommandFailedError(command, output)
    return output

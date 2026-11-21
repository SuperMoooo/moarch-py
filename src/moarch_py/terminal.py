"""Console output that works on every terminal, legacy Windows consoles included."""

from __future__ import annotations

import sys

from rich.console import Console


def make_output_safe() -> None:
    """Never crash on a character the console cannot show.

    A legacy Windows console encodes output as cp1252, which has no `✓` or
    `…`; without `errors="replace"`, printing one raises UnicodeEncodeError
    after the files are already written.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="replace")


def _supports_unicode() -> bool:
    encoding = (getattr(sys.stdout, "encoding", None) or "").lower()
    return encoding.replace("-", "") in {"utf8", "utf16", "utf32"}


_UNICODE = _supports_unicode()

OK = "[green]✓[/]" if _UNICODE else "[green]+[/]"
FAILED = "[red]✗[/]" if _UNICODE else "[red]x[/]"
WARNING = "[yellow]![/]"

console = Console()
error_console = Console(stderr=True)

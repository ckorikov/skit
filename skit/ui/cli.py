"""CLI: the command surface and its rendering.

Pure UI — each command parses its arguments, calls a core state operation,
and turns the outcome (success or a typed error) into console output and an
exit code. No model logic lives here.
"""

from pathlib import Path
from typing import NoReturn

import typer
from rich.console import Console
from rich.table import Table

from skit.core.storage import MANIFEST, State

_C = typer.Option(
    [],
    "-C",
    metavar="<path>",
    help="Run as if skit was started in <path> instead of the current directory.",
)


def _root(paths: list[Path]) -> Path:
    """Resolve the working directory from repeated ``-C`` options.

    Each non-absolute path is taken relative to the preceding one; an
    absolute path replaces it, and an empty path leaves it unchanged.
    """
    root = Path.cwd()
    for path in paths:
        root = root / path
    return root.resolve()


def register(app: typer.Typer, out: Console, err: Console) -> None:
    """Attach every CLI command onto the host's Typer app."""

    @app.command()
    def init(
        description: str = typer.Option(
            None, "--description", "-d", help="Free-text description."
        ),
        c: list[Path] = _C,
    ) -> None:
        """Create an empty curriculum here (a fresh ``curriculum.json``)."""
        root = _root(c)
        try:
            State.create(root, description)
        except FileExistsError:
            _fail(err, f"curriculum already exists in {root}")
        out.print(f"[green]Initialized curriculum in[/green] {root}")

    @app.command()
    def status(c: list[Path] = _C) -> None:
        """Show a summary of the curriculum here."""
        root = _root(c)
        try:
            state = State.load(root)
        except FileNotFoundError:
            _fail(err, f"no {MANIFEST} in {root} — run `skit init` first")
        _render(out, root, state)


def _render(out: Console, root: Path, state: State) -> None:
    """Print a curriculum's name (its directory), description, and counts."""
    out.print(f"[bold]{root.name}[/bold]")
    if state.curriculum.description:
        out.print(state.curriculum.description)

    table = Table(show_header=False, box=None, pad_edge=False)
    for name, count in state.summary().items():
        table.add_row(name, str(count))
    table.add_row("active syllabus", state.active_syllabus or "—")
    out.print(table)


def _fail(err: Console, message: str) -> NoReturn:
    """Print an error and abort the command."""
    err.print(f"[red]{message}[/red]")
    raise typer.Exit(1)

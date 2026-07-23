"""Host: composition root.

Wires the pieces together: builds the shared consoles and the Typer app,
registers the CLI commands, and exposes the entry point. State lives in the
core, presentation in the CLI; this module only assembles them.
"""

import typer
from rich.console import Console

from skit.ui import cli

app = typer.Typer(
    help="skit — build study plans from a curriculum.", no_args_is_help=True
)
cli.register(app, out=Console(), err=Console(stderr=True))


def main() -> None:
    app()


if __name__ == "__main__":
    main()

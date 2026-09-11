"""Typer command-line interface for gen_example_env."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from gen_example_env import __version__
from gen_example_env.core import Mode, generate_example

app = typer.Typer(
    add_completion=False,
    help="Generate a .env.example file from an existing .env file.",
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"gen_example_env {__version__}")
        raise typer.Exit()


@app.command()
def main(
    input_file: Annotated[
        Path,
        typer.Argument(
            help="Path to the .env file to read.",
            show_default=True,
        ),
    ] = Path(".env"),
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Where to write the example file. Defaults to .env.example next to the input.",
        ),
    ] = None,
    mode: Annotated[
        Mode,
        typer.Option(
            "--mode",
            "-m",
            help=(
                "blank: KEY=  |  placeholder: KEY=<KEY>  |  "
                "keep-safe: keep values whose key does not look secret."
            ),
            case_sensitive=False,
        ),
    ] = Mode.BLANK,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite the output file if it exists."),
    ] = False,
    to_stdout: Annotated[
        bool,
        typer.Option("--stdout", help="Print the result instead of writing a file."),
    ] = False,
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-V",
            help="Show the version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """Generate a .env.example from INPUT_FILE with values stripped or replaced."""
    if not input_file.is_file():
        typer.secho(f"Error: input file not found: {input_file}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    text = input_file.read_text(encoding="utf-8")
    rendered = generate_example(text, mode=mode)

    if to_stdout:
        typer.echo(rendered, nl=False)
        return

    target = output if output is not None else input_file.parent / ".env.example"
    if target.exists() and not force:
        typer.secho(
            f"Error: {target} already exists. Use --force to overwrite.",
            err=True,
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    target.write_text(rendered, encoding="utf-8")
    count = sum(1 for line in rendered.splitlines() if "=" in line and not line.lstrip().startswith("#"))
    typer.secho(f"Wrote {target} ({count} variables, mode={mode.value})", fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()

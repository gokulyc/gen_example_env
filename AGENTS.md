# AGENTS.md

Guidance for coding agents when working in this repository.

## What this is

`gen_example_env` is a small Typer CLI that reads a `.env` file and writes a `.env.example` with values
blanked or replaced, preserving comments, blank lines and `export` prefixes. See `README.md` for usage.

## Layout

- `src/lib.rs` – the Rust (PyO3) implementation of parsing, `looks_secret` and rendering; built as
  `gen_example_env._core`. No I/O here; keep it pure and testable.
- `src/gen_example_env/core.py` – thin Python layer: the `Mode` enum (Typer needs it) and wrappers that
  pass `mode.value` to `_core`; re-exports `Line`, `parse_env_lines`, `looks_secret`.
- `src/gen_example_env/cli.py` – the Typer app (`app`) and the single `main` command. Only argument
  handling, file I/O and messaging live here.
- `src/gen_example_env/__init__.py` – exports `__version__` only.
- `tests/test_core.py` – unit tests for parsing and each render mode.
- `tests/test_cli.py` – end-to-end tests via `typer.testing.CliRunner`.

## Toolchain

Everything goes through `uv` (Python 3.12+, `maturin` backend, so a Rust toolchain is required; `.python-version` pins 3.13 as the local default):

```bash
uv sync                    # create .venv and install runtime + dev deps
uv run gen_example_env ... # run the CLI from the checkout
uv run pytest -q           # run tests
uv add <pkg>               # add a runtime dependency
uv add --dev <pkg>         # add a dev dependency
just                       # list shortcuts (test, run, build, bump, set-version, untag)
```

After changing `src/lib.rs`, `uv run` rebuilds automatically; `uv sync --reinstall-package gen_example_env` forces it.

The console script is declared in `pyproject.toml` as `gen_example_env = "gen_example_env.cli:app"`.
The version lives only in `pyproject.toml` (`__version__` reads package metadata). Change it with `just bump`
/ `uv version`; pushing a changed `pyproject.toml` to `main` makes `.github/workflows/tag.yml` create tag `v<version>`.

## Conventions

- New behaviour that changes how values are rewritten belongs in `core.py` as a new `Mode` member (Python) plus a
  matching variant and branch in `src/lib.rs` (`Mode::parse` and `render`), with a test in `tests/test_core.py` and, if it adds a flag, `tests/test_cli.py`.
- Keep the CLI a single command; do not add subcommands without a reason.
- Never commit real `.env` files. `.env` is git-ignored; `.env.example` is meant to be tracked.
- Run `uv run pytest -q` before finishing any change.

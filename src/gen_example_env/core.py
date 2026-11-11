"""Parsing and rendering of .env files. The work happens in the Rust extension ``_core``."""

from __future__ import annotations

from enum import StrEnum

from gen_example_env import _core
from gen_example_env._core import Line, looks_secret, parse_env_lines

__all__ = ["Line", "Mode", "generate_example", "looks_secret", "parse_env_lines", "render_example"]


class Mode(StrEnum):
    """How assignment values are rewritten in the generated example."""

    BLANK = "blank"
    PLACEHOLDER = "placeholder"
    KEEP_SAFE = "keep-safe"


def render_example(lines: list[Line], *, mode: Mode = Mode.PLACEHOLDER) -> str:
    """Re-emit ``lines`` as .env.example text with values rewritten per ``mode``."""
    return _core.render_example(lines, Mode(mode).value)


def generate_example(text: str, *, mode: Mode = Mode.PLACEHOLDER) -> str:
    """Convenience wrapper: parse ``text`` and render the example in one step."""
    return _core.generate_example(text, Mode(mode).value)

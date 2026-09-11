"""Parsing and rendering of .env files. Free of any CLI dependencies."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class Mode(StrEnum):
    """How assignment values are rewritten in the generated example."""

    BLANK = "blank"
    PLACEHOLDER = "placeholder"
    KEEP_SAFE = "keep-safe"


@dataclass(frozen=True, slots=True)
class Line:
    """One line of a .env file, preserving enough to re-emit it faithfully."""

    raw: str
    key: str | None = None
    value: str | None = None
    export: bool = False
    quoted: bool = False
    comment: str = ""

    @property
    def is_assignment(self) -> bool:
        return self.key is not None


_ASSIGNMENT = re.compile(
    r"""^\s*(?P<export>export\s+)?(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=(?P<rest>.*)$"""
)
_SECRET_KEY = re.compile(
    r"SECRET|TOKEN|PASSWORD|PASSWD|PRIVATE|CREDENTIAL|AUTH|API|KEY", re.IGNORECASE
)


def _split_value(rest: str) -> tuple[str, bool, str]:
    """Split the text after ``=`` into (value, quoted, trailing_comment)."""
    stripped = rest.lstrip()
    if stripped and stripped[0] in ("'", '"'):
        quote = stripped[0]
        end = stripped.find(quote, 1)
        while end != -1 and stripped[end - 1] == "\\":
            end = stripped.find(quote, end + 1)
        if end != -1:
            value = stripped[1:end]
            tail = stripped[end + 1 :].strip()
            comment = tail if tail.startswith("#") else ""
            return value, True, comment
    # Unquoted: an inline comment starts at " #" (whitespace before the hash).
    match = re.search(r"\s#", stripped)
    if match:
        return stripped[: match.start()].rstrip(), False, stripped[match.start() :].strip()
    return stripped.strip(), False, ""


def parse_env_lines(text: str) -> list[Line]:
    """Parse ``text`` into ``Line`` objects, one per input line, in order."""
    lines: list[Line] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            lines.append(Line(raw=raw))
            continue
        match = _ASSIGNMENT.match(raw)
        if match is None:
            lines.append(Line(raw=raw))
            continue
        value, quoted, comment = _split_value(match.group("rest"))
        lines.append(
            Line(
                raw=raw,
                key=match.group("key"),
                value=value,
                export=match.group("export") is not None,
                quoted=quoted,
                comment=comment,
            )
        )
    return lines


def looks_secret(line: Line) -> bool:
    """Heuristic: quoted values or keys with secret-ish names are treated as secrets."""
    assert line.key is not None
    return line.quoted or _SECRET_KEY.search(line.key) is not None


def _example_value(line: Line, mode: Mode) -> str:
    assert line.key is not None
    match mode:
        case Mode.BLANK:
            return ""
        case Mode.PLACEHOLDER:
            return f"<{line.key}>"
        case Mode.KEEP_SAFE:
            return "" if looks_secret(line) else (line.value or "")
    raise ValueError(f"unknown mode: {mode!r}")


def render_example(lines: list[Line], *, mode: Mode = Mode.PLACEHOLDER) -> str:
    """Re-emit ``lines`` as .env.example text with values rewritten per ``mode``."""
    out: list[str] = []
    for line in lines:
        if not line.is_assignment:
            out.append(line.raw)
            continue
        prefix = "export " if line.export else ""
        rendered = f"{prefix}{line.key}={_example_value(line, mode)}"
        if line.comment:
            rendered = f"{rendered}  {line.comment}"
        out.append(rendered)
    return "\n".join(out) + ("\n" if out else "")


def generate_example(text: str, *, mode: Mode = Mode.PLACEHOLDER) -> str:
    """Convenience wrapper: parse ``text`` and render the example in one step."""
    return render_example(parse_env_lines(text), mode=mode)

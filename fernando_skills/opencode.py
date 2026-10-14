from __future__ import annotations

import re

from .frontmatter import get_field, parse_frontmatter, yaml_scalar

INJECTION_PATTERN = re.compile(r"!`([^`]+)`")
INJECTION_REPLACEMENT = r"Run `\1` now and use its actual output as this value."

ARGUMENT_NOTE = (
    "> **Arguments:** `$ARGUMENTS` in this skill refers to the arguments passed "
    "with the slash command (e.g. `/spec-impl 01-mvp-arkanoid`). If the command "
    "was invoked with no arguments, treat `$ARGUMENTS` as empty."
)


def translate_frontmatter(fields: list[tuple[str, str]]) -> str:
    name = get_field(fields, "name") or ""
    description = get_field(fields, "description") or ""
    lines = [
        "---",
        f"name: {yaml_scalar(name)}",
        f"description: {yaml_scalar(description)}",
        "license: MIT",
        "metadata:",
        '  opencode/slash: "true"',
        '  opencode/autoinvoke: "false"',
        "---",
    ]
    return "\n".join(lines) + "\n"


def translate_body(body: str) -> str:
    body = INJECTION_PATTERN.sub(INJECTION_REPLACEMENT, body)
    lines = body.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.startswith("# "):
            lines.insert(index + 1, "\n" + ARGUMENT_NOTE + "\n")
            return "".join(lines)
    return ARGUMENT_NOTE + "\n\n" + body


def translate_skill(text: str) -> str:
    fields, body = parse_frontmatter(text)
    return translate_frontmatter(fields) + translate_body(body)

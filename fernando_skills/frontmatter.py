from __future__ import annotations

FRONTMATTER_DELIMITER = "---"


def parse_frontmatter(text: str) -> tuple[list[tuple[str, str]], str]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        return [], text
    fields: list[tuple[str, str]] = []
    body_start: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        stripped = line.strip()
        if stripped == FRONTMATTER_DELIMITER:
            body_start = index + 1
            break
        if not stripped:
            continue
        key, separator, value = stripped.partition(":")
        if not separator:
            continue
        fields.append((key.strip(), value.strip()))
    if body_start is None:
        return [], text
    return fields, "".join(lines[body_start:])


def get_field(fields: list[tuple[str, str]], name: str) -> str | None:
    for key, value in fields:
        if key == name:
            return value
    return None


def yaml_scalar(value: str) -> str:
    if not value:
        return '""'
    if value.startswith(("#", "!", "&", "*", "[", "]", "{", "}", ">", "|", '"', "'", "%", "@", "`")) or ": " in value or value.endswith(":"):
        escaped = value.replace("\\", "\\\\").replace("'", "\\'")
        return f"'{escaped}'"
    return value

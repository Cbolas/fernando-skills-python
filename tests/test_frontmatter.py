from __future__ import annotations

from fernando_skills.frontmatter import get_field, parse_frontmatter, yaml_scalar
from tests.conftest import REPO_ROOT


def read_skill(skill_name: str) -> str:
    path = (
        REPO_ROOT
        / "fernando_skills"
        / "skills"
        / "engineering"
        / skill_name
        / "SKILL.md"
    )
    return path.read_text(encoding="utf-8")


def test_parses_required_frontmatter_fields():
    for skill_name in ("spec", "spec-impl"):
        fields, body = parse_frontmatter(read_skill(skill_name))
        assert get_field(fields, "name") == skill_name
        assert get_field(fields, "description")
        assert get_field(fields, "disable-model-invocation") == "true"
        assert get_field(fields, "argument-hint")
        assert get_field(fields, "allowed-tools")


def test_body_starts_after_frontmatter():
    fields, body = parse_frontmatter(read_skill("spec"))
    assert not body.startswith("---")
    assert body.lstrip().startswith("# /spec")
    assert "## Session context" in body


def test_frontmatter_not_found_returns_full_text():
    fields, body = parse_frontmatter("# no frontmatter here\n")
    assert fields == []
    assert body == "# no frontmatter here\n"


def test_yaml_scalar_quotes_only_when_needed():
    assert yaml_scalar("plain value") == "plain value"
    assert yaml_scalar('says "Approved" plainly') == 'says "Approved" plainly'
    assert yaml_scalar("has: colon") == "'has: colon'"
    assert yaml_scalar("'quoted'") == "'\\'quoted\\''"
    assert yaml_scalar("") == '""'
    assert yaml_scalar("ends with:") == "'ends with:'"

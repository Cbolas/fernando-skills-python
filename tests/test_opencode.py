from __future__ import annotations

from fernando_skills.frontmatter import get_field, parse_frontmatter
from fernando_skills.installer import install
from fernando_skills.opencode import translate_skill
from tests.conftest import tree_files


def read_source_skill(skill_name: str) -> str:
    from tests.conftest import REPO_ROOT

    return (
        REPO_ROOT
        / "fernando_skills"
        / "skills"
        / "engineering"
        / skill_name
        / "SKILL.md"
    ).read_text(encoding="utf-8")


def test_translated_frontmatter_for_spec():
    fields, _ = parse_frontmatter(read_source_skill("spec"))
    translated = translate_skill(read_source_skill("spec"))
    frontmatter = translated.split("---")[1]
    assert 'name: spec' in frontmatter
    assert f"description: {get_field(fields, 'description')}" in frontmatter
    assert "license: MIT" in frontmatter
    assert 'opencode/slash: "true"' in frontmatter
    assert 'opencode/autoinvoke: "false"' in frontmatter
    assert "argument-hint" not in frontmatter
    assert "disable-model-invocation" not in frontmatter
    assert "allowed-tools" not in frontmatter


def test_translated_body_has_no_injections_and_keeps_arguments():
    translated = translate_skill(read_source_skill("spec-impl"))
    assert "!`" not in translated
    assert "Run `git status --short` now" in translated
    assert "Run `git branch --show-current` now" in translated
    assert "$ARGUMENTS" in translated
    assert "**Arguments:**" in translated


def test_translated_spec_body_converts_date_injection():
    translated = translate_skill(read_source_skill("spec"))
    assert "Run `date +%F` now" in translated


def test_argument_note_lands_after_h1():
    translated = translate_skill(read_source_skill("spec"))
    lines = translated.splitlines()
    h1_index = next(i for i, line in enumerate(lines) if line.startswith("# /spec"))
    assert lines[h1_index + 1] == ""
    assert lines[h1_index + 2].startswith("> **Arguments:**")


def test_install_opencode_writes_translated_skills_and_verbatim_companions(
    target_repo, skills
):
    actions = install("opencode", target_repo)
    assert len(actions) == len(skills)
    root = target_repo / ".opencode" / "skills"
    for skill in skills:
        installed = (root / skill.name / "SKILL.md").read_text(encoding="utf-8")
        assert installed == translate_skill(skill.read())
        assert "!`" not in installed
    source_spec = next(skill for skill in skills if skill.name == "spec")
    source_template = (source_spec.path / "template.md").read_bytes()
    assert (root / "spec" / "template.md").read_bytes() == source_template


def test_install_opencode_is_idempotent(target_repo):
    install("opencode", target_repo)
    first = tree_files(target_repo / ".opencode")
    install("opencode", target_repo)
    second = tree_files(target_repo / ".opencode")
    assert first == second

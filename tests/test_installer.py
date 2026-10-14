from __future__ import annotations

import subprocess

import pytest

from fernando_skills import installer
from fernando_skills.installer import (
    CODEX_BLOCK_START,
    is_own_repository,
    list_skills,
    skills_destination,
)
from tests.conftest import REPO_ROOT, SKILLS_SCRIPT, tree_files

BASH_PARITY_AGENTS = ("claude", "cursor", "codex", "antigravity")


def test_discover_finds_both_skills_sorted(skills):
    assert [skill.name for skill in skills] == ["spec", "spec-impl"]
    spec = next(skill for skill in skills if skill.name == "spec")
    assert (spec.path / "template.md").is_file()


def test_list_skills_uses_relative_paths():
    listed = list_skills()
    assert listed == [
        "engineering/spec/SKILL.md",
        "engineering/spec-impl/SKILL.md",
    ]


def test_is_own_repository():
    assert is_own_repository(REPO_ROOT)
    assert not is_own_repository(REPO_ROOT.parent)


def test_install_claude_copies_skills_verbatim(target_repo, skills):
    actions = installer.install("claude", target_repo)
    assert len(actions) == len(skills)
    root = target_repo / ".claude" / "skills"
    for skill in skills:
        installed = tree_files(root / skill.name)
        source = tree_files(skill.path)
        assert installed == source


def test_install_antigravity_copies_skills_verbatim(target_repo, skills):
    installer.install("antigravity", target_repo)
    root = target_repo / ".antigravity" / "skills"
    for skill in skills:
        assert tree_files(root / skill.name) == tree_files(skill.path)


def test_install_refuses_inside_own_repository():
    with pytest.raises(installer.OwnRepositoryError):
        installer.install("claude", REPO_ROOT)


def test_install_codex_creates_block_and_copies(target_repo, skills):
    actions = installer.install("codex", target_repo)
    agents_md = target_repo / "AGENTS.md"
    text = agents_md.read_text(encoding="utf-8")
    assert text.startswith(CODEX_BLOCK_START)
    for skill in skills:
        assert f"- **{skill.name}** — " in text
        assert f"`.codex/skills/{skill.name}/SKILL.md`" in text
        assert tree_files(target_repo / ".codex" / "skills" / skill.name) == tree_files(skill.path)


def test_install_codex_is_idempotent_and_preserves_surrounding_text(target_repo):
    agents_md = target_repo / "AGENTS.md"
    agents_md.write_text("# Project rules\n\nUse conventional commits.\n", encoding="utf-8")
    installer.install("codex", target_repo)
    installer.install("codex", target_repo)
    text = agents_md.read_text(encoding="utf-8")
    assert text.count(CODEX_BLOCK_START) == 1
    assert text.startswith("# Project rules")
    assert "Use conventional commits." in text


def test_uninstall_codex_removes_block_and_dirs(target_repo):
    agents_md = target_repo / "AGENTS.md"
    agents_md.write_text("# Project rules\n\nUse conventional commits.\n", encoding="utf-8")
    installer.install("codex", target_repo)
    actions = installer.uninstall("codex", target_repo)
    assert actions
    assert not (target_repo / ".codex" / "skills" / "spec").exists()
    text = agents_md.read_text(encoding="utf-8")
    assert CODEX_BLOCK_START not in text
    assert "Use conventional commits." in text


def test_uninstall_never_removes_dirs_without_skill_md(target_repo):
    installer.install("opencode", target_repo)
    destination = skills_destination("opencode", target_repo)
    (destination / "spec" / "SKILL.md").unlink()
    installer.uninstall("opencode", target_repo)
    assert (destination / "spec").is_dir()
    assert not (destination / "spec-impl").exists()


def test_install_global_opencode_uses_home_config(target_repo, tmp_path, monkeypatch):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    installer.install("opencode", target_repo, global_install=True)
    skills_root = fake_home / ".config" / "opencode" / "skills"
    assert (skills_root / "spec" / "SKILL.md").is_file()
    assert not (target_repo / ".opencode").exists()


def test_install_global_claude_uses_home_config(target_repo, tmp_path, monkeypatch):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    installer.install("claude", target_repo, global_install=True)
    assert (fake_home / ".claude" / "skills" / "spec" / "SKILL.md").is_file()


def test_skills_destination_rejects_unknown_agent(tmp_path):
    with pytest.raises(ValueError):
        skills_destination("vim", tmp_path)


@pytest.mark.skipif(not SKILLS_SCRIPT.exists(), reason="bash installer not available")
@pytest.mark.parametrize("agent", BASH_PARITY_AGENTS)
def test_python_installer_matches_bash_installer(agent, tmp_path, skills):
    bash_target = tmp_path / "bash-target"
    python_target = tmp_path / "python-target"
    bash_target.mkdir()
    python_target.mkdir()
    subprocess.run(
        ["bash", str(SKILLS_SCRIPT), agent],
        cwd=bash_target,
        check=True,
        capture_output=True,
    )
    installer.install(agent, python_target)
    bash_tree = tree_files(bash_target)
    python_tree = tree_files(python_target)
    assert bash_tree == python_tree

from __future__ import annotations

import pytest

from fernando_skills import cli
from tests.conftest import REPO_ROOT


def test_list_prints_skills(capsys):
    assert cli.main(["list"]) == 0
    out = capsys.readouterr().out
    assert "engineering/spec/SKILL.md" in out
    assert "engineering/spec-impl/SKILL.md" in out


def test_install_and_uninstall_roundtrip(target_repo, monkeypatch, capsys):
    monkeypatch.chdir(target_repo)
    assert cli.main(["install", "opencode"]) == 0
    assert (target_repo / ".opencode" / "skills" / "spec" / "SKILL.md").is_file()
    assert cli.main(["uninstall", "opencode"]) == 0
    assert not (target_repo / ".opencode" / "skills" / "spec").exists()


def test_install_refuses_inside_own_repository(monkeypatch, capsys):
    monkeypatch.chdir(REPO_ROOT)
    assert cli.main(["install", "claude"]) == 1
    assert "target repo" in capsys.readouterr().err


def test_global_rejected_for_project_only_agents(target_repo, monkeypatch, capsys):
    monkeypatch.chdir(target_repo)
    assert cli.main(["install", "cursor", "--global"]) == 2


def test_unknown_agent_exits_with_usage_error(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["install", "vim"])
    assert excinfo.value.code == 2


def test_missing_command_exits_with_usage_error(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.main([])
    assert excinfo.value.code == 2

from __future__ import annotations

import os
from pathlib import Path

import pytest

from fernando_skills import installer

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_SCRIPT = REPO_ROOT / "scripts" / "install-to-agent.sh"


@pytest.fixture
def target_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "target-repo"
    repo.mkdir()
    return repo


@pytest.fixture
def skills() -> list[installer.Skill]:
    found = installer.discover_skills()
    assert found, "no skills found in the package"
    return found


def tree_files(root: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for dirpath, _dirnames, filenames in os.walk(root, followlinks=True):
        for filename in filenames:
            path = Path(dirpath) / filename
            if path.is_file():
                files[str(path.relative_to(root))] = path.read_bytes()
    return files

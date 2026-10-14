from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .frontmatter import get_field, parse_frontmatter
from .opencode import translate_skill

AGENTS = ("opencode", "claude", "cursor", "codex", "antigravity")
GLOBAL_AGENTS = ("opencode", "claude")
CODEX_BLOCK_START = "<!-- fernando-skills:start -->"
CODEX_BLOCK_END = "<!-- fernando-skills:end -->"
CODEX_BLOCK_INTRO = (
    "Installed from https://github.com/Klerith/fernando-skills. "
    "Each entry is a workflow you can invoke by reading the linked file "
    "and following its steps."
)


class InstallerError(Exception):
    pass


class OwnRepositoryError(InstallerError):
    pass


@dataclass(frozen=True)
class Skill:
    name: str
    path: Path

    def read(self) -> str:
        return self.path.joinpath("SKILL.md").read_text(encoding="utf-8")


def skills_root() -> Path:
    return Path(__file__).resolve().parent / "skills"


def discover_skills() -> list[Skill]:
    root = skills_root()
    skills: list[Skill] = []
    for skill_md in sorted(root.rglob("SKILL.md")):
        parts = skill_md.relative_to(root).parts
        if "node_modules" in parts or "deprecated" in parts:
            continue
        skills.append(Skill(name=skill_md.parent.name, path=skill_md.parent))
    skills.sort(key=lambda skill: skill.name)
    return skills


def list_skills() -> list[str]:
    root = skills_root()
    return [str(skill.path.relative_to(root) / "SKILL.md") for skill in discover_skills()]


def is_own_repository(target: Path) -> bool:
    source_root = Path(__file__).resolve().parent.parent
    return target.resolve() == source_root


def skills_destination(agent: str, target: Path, global_install: bool = False) -> Path:
    if agent == "opencode":
        base = Path.home() / ".config" / "opencode" if global_install else target / ".opencode"
        return base / "skills"
    if agent == "claude":
        base = Path.home() / ".claude" if global_install else target / ".claude"
        return base / "skills"
    if agent == "cursor":
        return target / ".cursor" / "rules"
    if agent == "codex":
        return target / ".codex" / "skills"
    if agent == "antigravity":
        return target / ".antigravity" / "skills"
    raise ValueError(f"unknown agent: {agent}")


def install(agent: str, target: Path, global_install: bool = False) -> list[str]:
    if not global_install and is_own_repository(target):
        raise OwnRepositoryError(
            "run this from the target repo, not the fernando-skills repo."
        )
    skills = discover_skills()
    if not skills:
        raise InstallerError("no SKILL.md files found in this package.")
    if agent == "cursor":
        return _install_cursor(skills, target)
    if agent == "codex":
        return _install_codex(skills, target)
    if agent == "opencode":
        return _install_opencode(skills, skills_destination(agent, target, global_install))
    if agent in ("claude", "antigravity"):
        destination = skills_destination(agent, target, global_install)
        return _install_copy(skills, destination)
    raise ValueError(f"unknown agent: {agent}")


def uninstall(agent: str, target: Path, global_install: bool = False) -> list[str]:
    if not global_install and is_own_repository(target):
        raise OwnRepositoryError(
            "run this from the target repo, not the fernando-skills repo."
        )
    skills = discover_skills()
    if not skills:
        raise InstallerError("no SKILL.md files found in this package.")
    if agent == "codex":
        return _uninstall_codex(skills, target)
    if agent == "cursor":
        return _uninstall_cursor(skills, target)
    destination = skills_destination(agent, target, global_install)
    return _uninstall_copy(skills, destination)


def _fresh_copy(skill: Skill, destination: Path) -> Path:
    target_dir = destination / skill.name
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(skill.path, target_dir)
    return target_dir


def _install_copy(skills: list[Skill], destination: Path) -> list[str]:
    destination.mkdir(parents=True, exist_ok=True)
    actions: list[str] = []
    for skill in skills:
        target_dir = _fresh_copy(skill, destination)
        actions.append(f"copied {skill.name} -> {target_dir}")
    return actions


def _install_cursor(skills: list[Skill], target: Path) -> list[str]:
    destination = target / ".cursor" / "rules"
    destination.mkdir(parents=True, exist_ok=True)
    actions: list[str] = []
    for skill in skills:
        fields, body = parse_frontmatter(skill.read())
        description = get_field(fields, "description") or ""
        content = (
            "---\n"
            f"description: {description}\n"
            "alwaysApply: false\n"
            "---\n"
            "\n"
            f"{body}"
        )
        if not content.endswith("\n"):
            content += "\n"
        out = destination / f"{skill.name}.mdc"
        out.write_text(content, encoding="utf-8")
        actions.append(f"wrote {out}")
    actions.append("")
    actions.append("Cursor rules written. They are 'manual' rules — invoke with @<skill-name>.")
    return actions


def _codex_block(skills: list[Skill]) -> str:
    lines = [
        CODEX_BLOCK_START,
        "## Skills (fernando-skills)",
        "",
        CODEX_BLOCK_INTRO,
        "",
    ]
    for skill in skills:
        fields, _ = parse_frontmatter(skill.read())
        description = get_field(fields, "description") or ""
        lines.append(f"- **{skill.name}** — {description}")
        lines.append(f"  - Workflow: `.codex/skills/{skill.name}/SKILL.md`")
    lines.append("")
    lines.append(CODEX_BLOCK_END)
    return "\n".join(lines) + "\n"


def _replace_block(text: str, block: str) -> str:
    lines = text.splitlines(keepends=True)
    start_index: int | None = None
    end_index: int | None = None
    for index, line in enumerate(lines):
        if start_index is None and CODEX_BLOCK_START in line:
            start_index = index
        elif start_index is not None and CODEX_BLOCK_END in line:
            end_index = index
            break
    if start_index is None:
        raise InstallerError("start marker not found")
    if end_index is None:
        lines[start_index:] = [block]
    else:
        lines[start_index : end_index + 1] = [block]
    return "".join(lines)


def _remove_block(text: str) -> str:
    lines = text.splitlines(keepends=True)
    start_index: int | None = None
    end_index: int | None = None
    for index, line in enumerate(lines):
        if start_index is None and CODEX_BLOCK_START in line:
            start_index = index
        elif start_index is not None and CODEX_BLOCK_END in line:
            end_index = index
            break
    if start_index is None:
        return text
    if end_index is None:
        del lines[start_index:]
    else:
        del lines[start_index : end_index + 1]
    return "".join(lines)


def _install_codex(skills: list[Skill], target: Path) -> list[str]:
    destination = target / ".codex" / "skills"
    destination.mkdir(parents=True, exist_ok=True)
    actions: list[str] = []
    for skill in skills:
        target_dir = _fresh_copy(skill, destination)
        actions.append(f"copied {skill.name} -> {target_dir}")
    block = _codex_block(skills)
    agents_md = target / "AGENTS.md"
    if agents_md.exists():
        text = agents_md.read_text(encoding="utf-8")
        if CODEX_BLOCK_START in text:
            agents_md.write_text(_replace_block(text, block), encoding="utf-8")
            actions.append(f"updated skills block in {agents_md}")
        else:
            with agents_md.open("a", encoding="utf-8") as handle:
                handle.write("\n" + block)
            actions.append(f"appended skills block to {agents_md}")
    else:
        agents_md.write_text(block, encoding="utf-8")
        actions.append(f"wrote {agents_md}")
    actions.append("updated AGENTS.md and copied skills into .codex/skills/")
    return actions


def _install_opencode(skills: list[Skill], destination: Path) -> list[str]:
    destination.mkdir(parents=True, exist_ok=True)
    actions: list[str] = []
    for skill in skills:
        target_dir = _fresh_copy(skill, destination)
        skill_md = target_dir / "SKILL.md"
        skill_md.write_text(translate_skill(skill.read()), encoding="utf-8")
        actions.append(f"copied {skill.name} -> {target_dir} (frontmatter translated for OpenCode)")
    return actions


def _uninstall_copy(skills: list[Skill], destination: Path) -> list[str]:
    actions: list[str] = []
    for skill in skills:
        target_dir = destination / skill.name
        skill_md = target_dir / "SKILL.md"
        if skill_md.is_file():
            shutil.rmtree(target_dir)
            actions.append(f"removed {target_dir}")
    return actions


def _uninstall_cursor(skills: list[Skill], target: Path) -> list[str]:
    actions: list[str] = []
    for skill in skills:
        rule = target / ".cursor" / "rules" / f"{skill.name}.mdc"
        if rule.is_file():
            rule.unlink()
            actions.append(f"removed {rule}")
    return actions


def _uninstall_codex(skills: list[Skill], target: Path) -> list[str]:
    actions: list[str] = []
    for skill in skills:
        target_dir = target / ".codex" / "skills" / skill.name
        if target_dir.joinpath("SKILL.md").is_file():
            shutil.rmtree(target_dir)
            actions.append(f"removed {target_dir}")
    agents_md = target / "AGENTS.md"
    if agents_md.is_file():
        text = agents_md.read_text(encoding="utf-8")
        if CODEX_BLOCK_START in text:
            agents_md.write_text(_remove_block(text), encoding="utf-8")
            actions.append(f"removed skills block from {agents_md}")
    return actions

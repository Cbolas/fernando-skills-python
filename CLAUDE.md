# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repo is a workspace for authoring slash-command skills for OpenCode, Claude Code, and other LLM agents, specifically for a spec-driven development workflow. Skills are written in **English**, and they instruct the agent to reply in whatever language the user's prompt used.

`reference/` is a vendored copy of `mattpocock/skills` kept as a structural/style reference — do not edit it during normal work. Its own `reference/CLAUDE.md` governs that subtree.

## Skill authoring conventions

Each skill lives under `fernando_skills/skills/<bucket>/<name>/` (e.g. `fernando_skills/skills/engineering/spec/`) as a directory containing at minimum a `SKILL.md`. A `skills` symlink at the repo root points there, so both paths work. Buckets group skills by domain (`engineering/`, future: `productivity/`, `misc/`, etc.). The YAML frontmatter of `SKILL.md` must declare:

```yaml
---
name: skill-name
description: One-line description (in Spanish)
disable-model-invocation: true
argument-hint: [hint]
---
```

Use `allowed-tools` in frontmatter to restrict what Bash commands a skill may run (see `fernando_skills/skills/engineering/spec-impl/SKILL.md` for an example that limits to read-only git/fs).

Use `!`command``shell snippets inside`SKILL.md` to inject live repo state at skill-load time (e.g., current branch, available specs). Embed them at the top of the skill body before the instructions.

Companion files (e.g., `template.md`) sit next to `SKILL.md` and are referenced by relative path within the skill body.

## The spec workflow

This repo encodes a two-skill pair:

### `/spec`

Guides the user through 4 phases: read project context → clarify with questions (blocks of 3–5) → draft each spec section one at a time with user confirmation → save to `specs/NN-slug.md`.

On save, it also seeds `specs/.spec-config.yml` (default `AutoCreateBranch: true`) **only if the file is missing** — an existing config is never overwritten. This is how the `AutoCreateBranch` flag that `/spec-impl` reads gets created without the user knowing the file exists.

Output file format: `specs/NN-slug.md` with a header block:

```
> **Status:** Draft
> **Depends on:** SPEC 01
> **Date:** YYYY-MM-DD
> **Objective:** One sentence.
```

The date comes from a `!`date +%F`` snippet injected at skill-load time — never from the model's own sense of the date.

**Status** after saving is always `Draft`. State transitions are human-driven — Claude must never change `**Status:**` automatically.

Valid states: `Draft` → `In review` → `Approved` → `Implemented` · `Obsolete`. Equivalents in any language are accepted (Spanish `Borrador` / `En revisión` / `Aprobado` / `Implementado` / `Obsoleto`, etc.); `/spec-impl` matches by meaning, and `/spec` follows whatever wording the existing specs in the repo already use.

### `/spec-impl`

Accepts `<NN-slug>` as argument. Phases:

1. Locate `specs/<NN-slug>.md`.
2. Read the status line — abort with a standard error message if it does not mean `Approved` in some language.
3. Check the working tree is clean, then create and switch to branch `spec-NN-slug`. If the branch already exists, treat it as a resume and propose a starting step from `git log`.
4. Implement the spec's plan step-by-step, pausing after each step for diff review. **It never commits** — that stays a human action.

Branch creation in step 3 is gated by the `AutoCreateBranch` flag, read at skill-load time from `specs/.spec-config.yml` via a `!`cat``snippet. Default (file or value absent) is`true`→ branch is created automatically. An explicit`false`makes the skill ask`[y/N]` before creating the branch; on decline it implements on the current branch. There is still no runtime config infra — the flag is just a value injected into the prompt and interpreted by the model.

At completion, remind the user to verify acceptance criteria and mark the spec `Implementado` manually before merging.

## Distribution

The repo ships as a Python package (no Node anywhere) and is consumed by users in two ways:

1. **Python CLI (canonical)** — `pip install git+https://github.com/Cbolas/fernando-skills-python.git` provides `fernando-skills install <agent>` (`opencode`, `claude`, `cursor`, `codex`, `antigravity`; `opencode`/`claude` also accept `--global`). The `opencode` target copies into `.opencode/skills/` and translates the frontmatter (`metadata.opencode/slash: "true"` makes `/spec` and `/spec-impl` real TUI commands; `!`command`` injections become run-it-now instructions). Sources: `fernando_skills/cli.py`, `fernando_skills/installer.py`, `fernando_skills/opencode.py`.
2. **Bash fallback** (`scripts/install-to-agent.sh <agent>`) — zero dependencies (git + bash); same behavior for `claude`/`cursor`/`codex`/`antigravity` (tests enforce byte parity). No `opencode` target — for OpenCode use the Python CLI. Run from the _target_ repo, not this one.

When changing installer behavior, update both `fernando_skills/installer.py` and `scripts/install-to-agent.sh` together — `tests/test_installer.py::test_python_installer_matches_bash_installer` fails if they drift.

`scripts/link-skills.sh` symlinks every skill into `~/.claude/skills` for local development (OpenCode reads that directory too).

## Build and test commands

```bash
python3 -m pip install -e .          # editable install; gives you the fernando-skills CLI
python3 -m pytest                    # test suite (installer parity, opencode translation, uninstall)
bash -n scripts/*.sh                 # syntax-check the bash scripts after editing them
```

Runtime dependencies: none (stdlib only). Dev dependencies: `pytest`. Bump the version in `pyproject.toml` and `fernando_skills/__init__.py` together when releasing — release-please does not manage the Python package version.

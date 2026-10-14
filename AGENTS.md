# AGENTS.md

Guidance for coding agents working in this repository.

## What this repo is

Authoring repo for spec-driven slash-command skills (`/spec`, `/spec-impl`) plus the `fernando-skills` Python CLI that installs them into agent configs (OpenCode, Claude Code, Cursor, Codex, Antigravity). Node-free fork of `Klerith/fernando-skills`. `CLAUDE.md` holds the same conventions for Claude Code; keep the two files consistent when conventions change.

## Layout

- `fernando_skills/skills/<bucket>/<name>/SKILL.md` — one skill per directory (currently `engineering/spec`, `engineering/spec-impl`). Companion files (e.g. `spec/template.md`) sit next to `SKILL.md` and are referenced by relative path. The root `skills` symlink points at `fernando_skills/skills`, so both paths work.
- `fernando_skills/` — pip-installable CLI, stdlib only (zero runtime deps): `cli.py`, `installer.py`, `frontmatter.py`, `opencode.py`.
- `tests/` — pytest suite, including byte-parity tests against the bash installer.
- `scripts/` — bash fallback installer + dev helpers (below).
- `reference/` — vendored copy of `mattpocock/skills`, gitignored (may not exist locally). Read-only style/structure reference — never edit or commit it.

## Commands

```bash
python3 -m pip install -e .   # editable install; provides the fernando-skills CLI
python3 -m pytest             # test suite
bash -n scripts/*.sh           # syntax-check bash scripts after editing them
```

## Skill authoring rules

- `SKILL.md` frontmatter must declare `name`, `description`, `disable-model-invocation: true`, and `argument-hint`. Use `allowed-tools` to whitelist Bash commands (see `spec-impl` for a read-only git/fs example).
- `!`command`` snippets inject live repo state at skill-load time in Claude Code (branch, spec list, date). Place them at the top of the body under a "Session context" heading. Spec dates must come from an injected `!`date +%F`` — never from the model.
- Skills are written in English and instruct the agent to reply in the user's prompt language. Spec status labels (`Draft`, `Approved`, …) are matched **by meaning in any language** — never hardcode English-only matching in `/spec-impl`.
- Behavioral invariants baked into the skills — preserve them when editing:
  - `/spec` saves specs as `specs/NN-slug.md` with status `Draft`, never proposes implementation afterwards, and seeds `specs/.spec-config.yml` (`AutoCreateBranch: true`) only if the file is missing — never overwrites it.
  - `/spec-impl` proceeds only when the spec status means Approved, never commits, and never changes `**Status:**` — state transitions are human-driven.

## Installer behavior (two implementations, keep in sync)

- Canonical: `fernando-skills install <agent> [--global]` (`opencode`/`claude` support `--global`). All targets **copy** (never symlink) so a pip uninstall can't break an installed skill; `fernando-skills uninstall <agent>` removes them.
- Fallback: `scripts/install-to-agent.sh` covers `claude`/`cursor`/`codex`/`antigravity` only (no `opencode`), refuses to run inside this repo.
- Changing installer behavior means editing **both** `fernando_skills/installer.py` and `scripts/install-to-agent.sh` — `tests/test_installer.py::test_python_installer_matches_bash_installer` fails if they drift.
- OpenCode target translation (`fernando_skills/opencode.py`): drops Claude-only frontmatter, adds `license: MIT` plus `metadata.opencode/slash: "true"` (exposes `/spec`, `/spec-impl` as TUI commands) and `opencode/autoinvoke: "false"`; rewrites `!`cmd`` injections into run-it-now instructions and inserts a `$ARGUMENTS` adapter note after the H1.
- `scripts/link-skills.sh` symlinks each skill into `~/.claude/skills` for local dev (OpenCode reads that directory too). `scripts/list-skills.sh` lists every SKILL.md.

## Docs and releases

- `README.md` and `README-es.md` are maintained in parallel — update both together.
- Releases are automated via release-please. Commits must follow Conventional Commits: `feat:` bumps minor, `fix:` bumps patch, `feat!:`/`fix!:` bumps major, `docs:`/`chore:`/`refactor:` no bump.
- `CHANGELOG.md` and `.github/.release-please-manifest.json` are generated — never edit them by hand.
- release-please does not manage the Python package version — bump `pyproject.toml` and `fernando_skills/__init__.py` together, manually.

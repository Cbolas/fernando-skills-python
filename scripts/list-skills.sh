#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"

cd "$REPO"
find fernando_skills/skills -name SKILL.md -not -path '*/node_modules/*' | sort

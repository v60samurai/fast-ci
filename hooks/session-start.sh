#!/usr/bin/env bash
# Claude Code SessionStart hook. Prints a fast-ci instruction when this repo lacks its CI baseline.
# Silent outside a Git repo and in a repo that is already set up.
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0
root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
cd "$root" || exit 0
if [ ! -f .ci-baseline ]; then
  why="has no .ci-baseline"
elif [ -d .fast-ci-proposed ]; then
  why="has an unmerged fast-ci proposal in .fast-ci-proposed/"
elif [ -f lefthook.yml ] && [ ! -f "$(git rev-parse --git-path hooks/pre-push)" ]; then
  why="has no pre-push hook installed"
else
  exit 0
fi
echo "This repo $why. Before any other work, use the fast-ci skill to run its setup."

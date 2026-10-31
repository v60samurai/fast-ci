#!/usr/bin/env bash
# Static checks, no network: SKILL.md states each rollout rule, and the templates default
# test concurrency to half the runner's cores.
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
pass() { echo "PASS $*"; }
fail() { echo "FAIL $*"; exit 1; }
has() { grep -qF -- "$2" "$here/$1" || fail "$1 lacks: $2"; }

has SKILL.md "push only the top branch"
has SKILL.md "Never re-push every branch at once"
pass "skill: stacked PRs push the top branch only"

has SKILL.md "run the suite 3 times at the new level"
has SKILL.md "lower the concurrency before you loosen a timeout"
has SKILL.md "half the runner's cores"
pass "skill: raising parallelism needs 3 passing runs"

has SKILL.md "Do not subscribe an agent to PR or CI webhooks"
has SKILL.md 'gh run watch <id>'
pass "skill: agents do not watch CI events"

has templates/ci.yml "--maxWorkers=50%"
grep -qE -- '--maxWorkers=[0-9]+([^0-9%]|$)' "$here/templates/ci.yml" && fail "templates/ci.yml: a fixed --maxWorkers count is left"
# shellcheck disable=SC2016 # the literal text, not an expansion
has templates/ci.yml '-n $(( $(nproc) / 2 ))'
pass "templates: Vitest and pytest-xdist default to half the cores"

#!/usr/bin/env bash
# Static checks, no network: SKILL.md and playbook.md state each rollout rule, and the templates default
# test concurrency to half the runner's cores.
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
pass() { echo "PASS $*"; }
fail() { echo "FAIL $*"; exit 1; }
has() { grep -qF -- "$2" "$here/$1" || fail "$1 lacks: $2"; }

has SKILL.md "push only the top branch"
has SKILL.md "Never re-push every branch at once"
pass "skill: stacked PRs push the top branch only"

has SKILL.md "run the suite 5 times in a row at the new level"
has SKILL.md "lower the concurrency before you loosen a timeout"
has SKILL.md "half the runner's cores"
pass "skill: raising parallelism needs 5 passing runs"

has SKILL.md "Do not subscribe an agent to PR or CI webhooks"
has SKILL.md 'gh run watch <id>'
pass "skill: agents do not watch CI events"

has SKILL.md "Invoking this branch is the user's approval"
has SKILL.md "Never switch to paid runners"
has SKILL.md "Never remove, skip or weaken a test or a required check"
has SKILL.md "Never force-push the default branch"
has SKILL.md "revert the merge at once"
has SKILL.md "fast af"
pass "skill: Speedup runs alone inside its guardrails and ends on the numbers"

for item in "a. Seed the cache" "b. Blobless clone" "c. Fastest linter" "d. Fastest typechecker" "e. Test files share a worker" \
  "f. More cores before more shards" "g. Match concurrency to cores" "h. Everything in parallel" "i. Only run what a PR touches" \
  "j. Checks before every push" "k. Keep every test"; do has playbook.md "## $item"; done
has playbook.md "confirm the run fails"
pass "playbook: every item a to k, and the skip logic is tested"

has templates/ci.yml "--maxWorkers=50%"
grep -qE -- '--maxWorkers=[0-9]+([^0-9%]|$)' "$here/templates/ci.yml" && fail "templates/ci.yml: a fixed --maxWorkers count is left"
# shellcheck disable=SC2016 # the literal text, not an expansion
has templates/ci.yml '-n $(( $(nproc) / 2 ))'
pass "templates: Vitest and pytest-xdist default to half the cores"

grep -rn 'TODO(fast-ci)' "$here/templates" "$here/SKILL.md" && fail "a TODO(fast-ci) default is left"
has SKILL.md "504s to 206s"
has templates/ci.yml "steps.js.outputs.node-version"
has templates/ci.yml "steps.js.outputs.bun-version"
pass "defaults: no TODO left, each backed by a measured rollout"

#!/usr/bin/env bash
# Static checks, no network: SKILL.md states each rule and guardrail, the playbook catalog is complete, and the templates default
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
has SKILL.md "Never switch to paid, bigger or faster runners"
has SKILL.md "Never remove, skip or weaken a test or a required check"
has SKILL.md "Never force-push the default branch"
has SKILL.md "revert the merge at once"
has SKILL.md "fast af"
pass "skill: Speedup runs alone inside its guardrails and ends on the numbers"

has SKILL.md "Never land a report-only entry"
has SKILL.md "Every job keeps a \`timeout-minutes\`"
has SKILL.md "Agent CI rounds are bounded"
has SKILL.md "Rerun a failed job only for an infrastructure failure"
has SKILL.md "minutes saved per day"
has SKILL.md "## Refresh"
pass "skill: guardrails for timeouts, agent rounds, retries and report-only entries"

# The catalog: every entry complete, every report-only entry locked, every StarSling technique present.
python3 -I - "$here" <<'PY' || fail "playbook catalog"
import pathlib, re, sys
root = pathlib.Path(sys.argv[1])
fields = ["applies when", "how", "estimate", "verify", "risk", "mode", "evidence"]
reasons = {"paid-runner", "after-merge", "merge-gate", "weakens-check", "agent-workflow", "needs-infra"}
cats = re.findall(r"\(playbook/([a-z-]+)\.md\)", (root / "playbook.md").read_text())
bad, modes = [], {}
assert len(set(cats)) == 8, f"playbook.md links {len(set(cats))} category files, want 8"
for cat in sorted(set(cats)):
    for e in re.split(r"(?m)^### ", (root / "playbook" / f"{cat}.md").read_text())[1:]:
        m = re.match(r"([a-z0-9-]+): \S", e)
        if not m:
            bad.append(f"{cat}: heading {e.splitlines()[0]!r}"); continue
        i = m.group(1)
        if i in modes: bad.append(f"{i}: duplicate id")
        if re.findall(r"(?m)^- \*\*([a-z ]+):\*\*", e) != fields: bad.append(f"{i}: fields not exactly {fields}")
        v = dict(re.findall(r"(?m)^- \*\*([a-z ]+):\*\* (.*)$", e))
        if v.get("risk") not in ("low", "medium", "high"): bad.append(f"{i}: risk {v.get('risk')!r}")
        mode = v.get("mode", "")
        r = re.fullmatch(r"report-only \(([a-z-]+)\)", mode)
        if mode != "auto" and not (r and r.group(1) in reasons): bad.append(f"{i}: mode {mode!r}")
        if "`" not in v.get("applies when", ""): bad.append(f"{i}: applies when names no signal")
        if "starsling.dev" not in v.get("evidence", "") and not i.startswith("fc-"): bad.append(f"{i}: no StarSling evidence")
        modes[i] = "auto" if mode == "auto" else "report-only"
locked = {l.strip() for l in (root / "tests/report-only.txt").read_text().splitlines() if l.strip() and not l.startswith("#")}
bad += [f"{i}: locked report-only but {modes.get(i, 'missing')}" for i in sorted(locked) if modes.get(i) != "report-only"]
bad += [f"{i}: report-only but not in tests/report-only.txt" for i, m in sorted(modes.items()) if m == "report-only" and i not in locked]
index = set(re.findall(r"(?m)^### ([a-z0-9-]+)$", (root / "research/starsling-index.md").read_text()))
bad += [f"{i}: in the StarSling index but not the catalog" for i in sorted(index - set(modes))]
print("\n".join(bad)); sys.exit(1 if bad else 0)
PY
pass "playbook: every entry has every field, report-only entries stay report-only, every StarSling technique is in"

grep -n '—' "$here/SKILL.md" "$here/playbook.md" "$here"/playbook/*.md "$here/README.md" && fail "an em dash is left"
python3 -I -c 'import ast, sys; ast.parse(open(sys.argv[1]).read())' "$here/audit.py" || fail "audit.py does not parse"
pass "docs: no em dashes; audit.py parses"

python3 -I "$here/tests/audit_test.py" | grep -c '^PASS audit.py' | grep -qx 2 || fail "tests/audit_test.py"
pass "audit.py: signal rules hold on fixture data"

# Claude Code replaces $0, $1, ... in a skill body with the invocation's words, so "$4,300" became "af,300".
grep -nE '\$[0-9]' "$here/SKILL.md" && fail "SKILL.md: a dollar sign before a digit is replaced by a skill argument"
pass "skill: no text that skill arguments can replace"

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

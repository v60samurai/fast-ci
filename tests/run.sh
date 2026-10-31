#!/usr/bin/env bash
# Runs tests/rules.sh first. Then end-to-end proof in a throwaway Bun + TypeScript + Vitest repo, deleted on exit:
#   1. a first Claude Code session gets the hook message and runs fast-ci setup on its own
#   2. setup wrote the workflow, lefthook.yml, the Git hook and .ci-baseline, and a second run changes nothing
#   3. a push with a type error is blocked locally; a clean push goes through
#   4. a second session gets no message
# Needs bun, claude, jq and network access. MODEL picks the session model (default sonnet).
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
bash "$here/tests/rules.sh"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
pass() { echo "PASS $*"; }
fail() { echo "FAIL $*"; exit 1; }

# Claude Code with only this hook and this skill: user settings and skills stay out.
printf '{"hooks":{"SessionStart":[{"hooks":[{"type":"command","command":"bash %s/hooks/session-start.sh"}]}]}}\n' "$here" > "$tmp/settings.json"
session() {
  (cd "$tmp/app" && claude -p "$1" --model "${MODEL:-sonnet}" --setting-sources project --settings "$tmp/settings.json" \
    --include-hook-events --output-format stream-json --verbose \
    --allowedTools "Skill Bash Read Edit Write Glob Grep" --max-turns 40) > "$tmp/$2.jsonl"
  jq -r 'select(.type=="system" and .subtype=="hook_response" and .hook_event=="SessionStart") | .stdout' "$tmp/$2.jsonl"
}

echo "== throwaway repo: $tmp/app"
git init -q --bare "$tmp/origin.git"
mkdir "$tmp/app" && cd "$tmp/app"
git init -q -b main && git remote add origin "$tmp/origin.git"
bun init -y >/dev/null 2>&1
bun add -d vitest >/dev/null 2>&1
mkdir src
printf 'export const add = (a: number, b: number): number => a + b;\n' > src/math.ts
printf 'import { expect, test } from "vitest";\nimport { add } from "./math";\n\ntest("add", () => {\n  expect(add(1, 2)).toBe(3);\n});\n' > src/math.test.ts
# The skill as a project skill, kept out of Git.
mkdir -p .claude/skills && ln -s "$here" .claude/skills/fast-ci && printf '.claude/\n' >> .git/info/exclude
git add -A && git commit -qm init && git push -q -u origin main

echo "== session 1"
out=$(session "Add a subtract function to src/math.ts." s1)
echo "hook said: $out"
grep -q "no .ci-baseline" <<<"$out" || fail "session 1: hook did not fire"
pass "session 1: hook fired"
jq -r 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use") | "  tool: \(.name) \(.input.command // .input.skill // .input.file_path // "")"' "$tmp/s1.jsonl" | head -20

for f in .github/workflows/ci.yml lefthook.yml .ci-baseline "$(git rev-parse --git-path hooks/pre-push)"; do
  [ -f "$f" ] || fail "setup: $f missing"
done
pass "setup: workflow, lefthook.yml, Git hook and marker present"
echo "--- .ci-baseline"; cat .ci-baseline
command -v actionlint >/dev/null && { actionlint .github/workflows/ci.yml && pass "actionlint: workflow is valid"; }
grep -qF -- "--maxWorkers=50%" .github/workflows/ci.yml || fail "setup: workflow does not default Vitest to half the cores"
bunx vitest run --maxWorkers=50% --passWithNoTests >/dev/null || fail "vitest: rejected --maxWorkers=50%"
pass "setup: Vitest workers default to half the cores, and Vitest accepts it"

before=$(git status --porcelain; cat .ci-baseline)
bash "$here/setup.sh" >/dev/null
[ "$before" = "$(git status --porcelain; cat .ci-baseline)" ] || fail "setup: second run changed the repo"
pass "setup: second run changed nothing"

git add -A && git commit -qm "fast-ci baseline" && git push -q origin main 2>&1 | tail -5
pass "push: clean push went through"

printf 'export const bad: number = "not a number";\n' > src/bad.ts
git add -A && git commit -qm "type error"
if git push origin main > "$tmp/push.log" 2>&1; then fail "push: type error was pushed"; fi
grep -E "typecheck|error TS" "$tmp/push.log" | head -5
[ "$(git rev-parse origin/main)" = "$(git -C "$tmp/origin.git" rev-parse main)" ] && [ "$(git rev-parse HEAD)" != "$(git -C "$tmp/origin.git" rev-parse main)" ] \
  || fail "push: remote moved"
pass "push: type error blocked locally, remote unchanged"

echo "== session 2"
out=$(session "Reply with the single word OK." s2)
[ -z "$out" ] || fail "session 2: hook printed: $out"
pass "session 2: hook silent"

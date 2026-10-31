#!/usr/bin/env bash
# fast-ci setup. Run from anywhere inside the target Git repo. Safe to run again.
#   setup.sh          detect the stack, write CI and the pre-push hook, install the hook, write .ci-baseline
#   setup.sh --skip   mark a repo with no code to check, so the session hook stops asking
# Exit 2: nothing to detect yet (no package.json or pyproject.toml at the repo root).
set -euo pipefail

VERSION=1.0.0
skill=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
root=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "fast-ci: not inside a Git repository" >&2; exit 1; }
cd "$root"
marker=.ci-baseline
proposed=.fast-ci-proposed

write_marker() { printf 'fast-ci %s\ndate %s\nstack %s\n' "$VERSION" "$(date +%F)" "$1" > "$marker"; }

if [ "${1:-}" = --skip ]; then
  write_marker none
  echo "fast-ci: wrote $marker (stack none)"
  exit 0
fi

# Parts select the marked blocks kept from the templates. The "template" block is never kept.
# shortcut: reads only the repo root, so a monorepo's packages are not detected; extend when one needs it.
parts=""
if [ -f package.json ]; then
  parts+=" js"
  [ -f tsconfig.json ] && parts+=" ts"
  grep -q '"vitest"' package.json && parts+=" vitest"
  grep -q '"build"[[:space:]]*:' package.json && parts+=" build"
  if [ -f bun.lock ] || [ -f bun.lockb ]; then
    parts+=" bun"; install="bun install --frozen-lockfile"; run="bun run"; exec="bunx"; add="bun add -d"
  else
    parts+=" node"
    if [ -f pnpm-lock.yaml ]; then install="pnpm install --frozen-lockfile"; run="pnpm run"; exec="pnpm exec"; add="pnpm add -D"
    elif [ -f yarn.lock ]; then install="yarn install --immutable"; run="yarn run"; exec="yarn"; add="yarn add -D"
    else install="npm ci"; run="npm run"; exec="npx"; add="npm install -D"
    fi
  fi
fi
[ -f pyproject.toml ] && parts+=" py"
if [ -z "$parts" ]; then
  echo "fast-ci: no package.json or pyproject.toml at $root yet. Scaffold the project, then run setup again." >&2
  exit 2
fi
has() { [[ " $parts " == *" $1 "* ]]; }

render() {
  local out
  out=$(cat "$1")
  for part in template js ts vitest build bun node py; do
    has "$part" || out=$(sed "/# >>> $part\$/,/# <<< $part\$/d" <<<"$out")
  done
  sed -e '/# >>> /d' -e '/# <<< /d' \
    -e "s|__INSTALL__|${install:-}|g" -e "s|__RUN__|${run:-}|g" -e "s|__EXEC__|${exec:-}|g" <<<"$out"
}

# Write $2 from template $1, or, when $2 already exists and differs, leave it alone and propose.
place() {
  local template=$1 target=$2 new
  new=$(render "$skill/templates/$template")
  if [ ! -f "$target" ]; then
    mkdir -p "$(dirname "$target")"
    printf '%s\n' "$new" > "$target"
    echo "fast-ci: wrote $target"
  elif [ "$new" != "$(cat "$target")" ]; then
    mkdir -p "$proposed"
    printf '%s\n' "$new" > "$proposed/$template"
    echo "fast-ci: $target exists. Proposed baseline is $proposed/$template. Diff (existing -> baseline):"
    diff -u "$target" "$proposed/$template" || true
  fi
}

if [ ! -f "$marker" ]; then
  # Merge into the workflow that already runs on PRs, if there is one.
  ci=.github/workflows/ci.yml
  [ -f "$ci" ] || ci=$(grep -l 'pull_request' .github/workflows/*.y*ml 2>/dev/null | head -1 || true)
  place ci.yml "${ci:-.github/workflows/ci.yml}"
  place lefthook.yml lefthook.yml

  if has js; then
    missing=""
    for dep in lefthook oxlint oxfmt; do grep -q "\"$dep\"" package.json || missing+=" $dep"; done
    # shellcheck disable=SC2086 # word splitting is intended
    [ -n "$missing" ] && $add $missing
    if has ts && [ "$(npm pkg get scripts.typecheck)" = "{}" ]; then
      npm pkg set scripts.typecheck="tsc --noEmit"
      echo "fast-ci: added scripts.typecheck"
    fi
  fi
  write_marker "${parts# }"
  echo "fast-ci: wrote $marker"
fi

# Always (re)install the Git hook: a fresh clone has the marker but not the hook.
if has js; then
  $exec lefthook install
elif command -v lefthook >/dev/null; then
  lefthook install
elif command -v brew >/dev/null; then
  brew install lefthook && lefthook install
else
  echo "fast-ci: install lefthook (https://lefthook.dev), then run setup again." >&2
  exit 1
fi

if [ -d "$proposed" ]; then
  echo "fast-ci: NEXT merge each file in $proposed/ into the file it names above, then delete $proposed/."
fi

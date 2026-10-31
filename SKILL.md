---
name: fast-ci
description: Fast CI and a pre-push hook for a Git repo, and an audit for slow CI. Use for a new project or repo, when setting up CI, when CI is slow, or when a repo has no .ci-baseline.
---

# fast-ci

Agents write every PR: they push, wait for CI, fix the red check and push again. CI time is the length of that loop, so every second of waiting, setup and running costs every PR. This skill is the one source for how a repo gets fast CI. `.ci-baseline` at the repo root marks a repo that has it.

## Setup

1. Run `bash <this skill's directory>/setup.sh` from inside the repo. It detects the stack, writes `.github/workflows/ci.yml` and `lefthook.yml`, adds `lefthook`, `oxlint` and `oxfmt` to a JS repo, installs the pre-push hook and writes `.ci-baseline`.
   - Exit 2 means there is nothing to detect yet. In a new repo, scaffold first and run setup before the task ends. In a repo with no code to check, ask Harshit, and on his yes run `setup.sh --skip`.
2. If setup printed a diff, merge each file in `.fast-ci-proposed/` into the existing file it names. Keep every existing job and check; add the fast-ci pieces it lacks (parallel jobs, `seed-cache`, the `node_modules` cache, blobless checkout, the `ci-ok` gate). Then delete `.fast-ci-proposed/`.
3. If the repo already has a formatter, point the `format` command in `lefthook.yml` and the `lint` job at it. Otherwise run `oxfmt` once over the repo.
4. Turn on every Oxlint category the code passes, in `.oxlintrc.json`. Strict rules cost an agent nothing.
5. Point the `typecheck` script at the fastest checker the repo passes on, and switch whenever a faster one ships.
6. In a Vitest repo, set `test.isolate: false` so test files share a worker. Add a `setupFiles` hook that resets shared state after every file (database rows, mocks, timers, module singletons), and write in `AGENTS.md` what a test must clean up.
7. Leave each `TODO(fast-ci)` at its default. Harshit sets them from measured runs.

Setup is done when `.ci-baseline` exists, `.fast-ci-proposed/` is gone, `lefthook run pre-push --all-files` passes, and `actionlint` passes on the workflow. Report the `TODO(fast-ci)` lines left.

## Harshit's call

Ask before any change that raises cost or changes what the tests check:

- Cost: paid runners (the commented `runs-on` lines), bigger machines, more shards, more scheduled runs. Owen Gretzinger's bill went from $230 to $4,300 a month from these.
- Checks: deleting, skipping or quarantining tests, narrowing the affected-test selection, dropping an existing CI job or lint rule (replacing ESLint with Oxlint included).

## Audit a slow repo

1. Pull the jobs of the last ~150 runs: `gh run list --limit 150 --json databaseId --jq '.[].databaseId' | xargs -I% gh api 'repos/{owner}/{repo}/actions/runs/%/jobs' --paginate`.
2. Split every job into **waiting** (`created_at` to `started_at`), **setup** (checkout, toolchain, cache restore, install) and **running** (the project's own commands), using the step timestamps.
3. Find the critical path: the PR's slowest job sets its time.
4. Rank fixes by measured seconds saved on the critical path, per PR. Look where the time usually hides:
   - Waiting: runner queue time. A 5-second job that waits 10 minutes for a machine is a 10-minute job. Faster runners cost money.
   - Setup: cache misses on PR runs (no cache seeded from main), installs that a `node_modules` restore would replace, shallow or full clones where a blobless one fits, worker counts above the runner's cores.
   - Running: bigger machines before more shards, test files sharing a worker, extra work moved off the slowest job, affected-only tests.
5. Apply the free fixes and measure again. Bring the paid ones and anything under "Harshit's call" to him with their measured saving and cost.

The audit is done when every fix in the ranking carries a measured saving, and each free fix is applied and re-measured.

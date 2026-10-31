---
name: fast-ci
description: Fast CI and a pre-push hook for a Git repo, and an audit for slow CI. Use for a new project or repo, when setting up CI, when CI is slow, or when a repo has no .ci-baseline.
---

# fast-ci

Agents write every PR: they push, wait for CI, fix the red check and push again. CI time is the length of that loop, so every second of waiting, setup and running costs every PR. This skill is the one source for how a repo gets fast CI. `.ci-baseline` at the repo root marks a repo that has it.

## Setup

1. Run `bash <this skill's directory>/setup.sh` from inside the repo. It detects the stack, writes `.github/workflows/ci.yml` and `lefthook.yml`, adds `lefthook`, `oxlint` and `oxfmt` to a JS repo, installs the pre-push hook and writes `.ci-baseline`.
   - Exit 2 means there is nothing to detect yet. In a new repo, scaffold first and run setup before the task ends. In a repo with no code to check, ask the user, and on their yes run `setup.sh --skip`.
2. If setup printed a diff, merge each file in `.fast-ci-proposed/` into the existing file it names. Keep every existing job and check; add the fast-ci pieces it lacks (parallel jobs, `seed-cache`, the `node_modules` cache, blobless checkout, the `ci-ok` gate). Then delete `.fast-ci-proposed/`.
3. If the repo already has a formatter, point the `format` command in `lefthook.yml` and the `lint` job at it. Otherwise run `oxfmt` once over the repo.
4. Turn on every Oxlint category the code passes, in `.oxlintrc.json`. Strict rules cost an agent nothing.
5. Point the `typecheck` script at the fastest checker the repo passes on, and switch whenever a faster one ships.
6. In a Vitest repo, set `test.isolate: false` so test files share a worker. Add a `setupFiles` hook that resets shared state after every file (database rows, mocks, timers, module singletons), and write in `AGENTS.md` what a test must clean up.
7. Keep the defaults below. Add to the full-run list any file the tests read without importing it (fixtures, demo data, codegen sources).

Setup is done when `.ci-baseline` exists, `.fast-ci-proposed/` is gone, `lefthook run pre-push --all-files` passes, and `actionlint` passes on the workflow.

## Defaults

Each comes from a measured rollout. Change one only from this repo's own measured runs.

- Shards: 4, because 4 shards took BDM Meeting Insights CI from 504s to 206s at p50, and a 2-vCPU runner is one physical core, so more runners is the free way to more cores.
- Workers per runner: half the vCPUs, which is one per physical core, because 2 workers on BDM's 2-vCPU runner made timing tests flaky and one per core was the safe level on Listing QA (CI 45.4 to 13.3 min at p50).
- Full test run: a change to a lockfile, `package.json`, `pnpm-workspace.yaml`, `.npmrc`, `.node-version`, `.nvmrc`, `tsconfig*.json`, Vite or Vitest config, `.env*`, `.github/`, `patches/` or the shared test setup runs every test, because Vitest's import graph cannot see those files.
- `node_modules` cache key: OS, architecture, runtime version and a hash of the lockfiles, `pnpm-workspace.yaml`, `.npmrc` and `patches/`, so the cache misses exactly when an install would produce different files.

## Needs the user's call

Ask before any change that raises cost or changes what the tests check:

- Cost: paid runners (the commented `runs-on` lines), bigger machines, more shards, more scheduled runs. Owen Gretzinger's bill went from $230 to $4,300 a month from these.
- Checks: deleting, skipping or quarantining tests, narrowing the affected-test selection, dropping an existing CI job or lint rule (replacing ESLint with Oxlint included).

## Push and wait

- When a fix lands low in a stack of PRs, rebase the stack locally and push only the top branch, then let CI run once. Never re-push every branch at once. That starts one run per branch, and the parallel runs overload the runners and cause new failures.
- Do not subscribe an agent to PR or CI webhooks. Cancelled duplicate runs fire events too, so every event wakes the agent for nothing. Check CI status when the user asks, or wait on a single run with `gh run watch <id>`.

## Raise parallelism

Workers per runner (Vitest `--maxWorkers`, pytest-xdist `-n`) start at half the runner's cores, not all of them. When you raise test concurrency (workers or shards), run the suite 3 times at the new level before you call it done. If a timing-based test fails, lower the concurrency before you loosen a timeout. A level that passes every time beats a faster one that fails now and then. Record the setting you chose and why in a comment next to it.

## Audit a slow repo

1. Pull the jobs of the last ~150 runs: `gh run list --limit 150 --json databaseId --jq '.[].databaseId' | xargs -I% gh api 'repos/{owner}/{repo}/actions/runs/%/jobs' --paginate`.
2. Split every job into **waiting** (`created_at` to `started_at`), **setup** (checkout, toolchain, cache restore, install) and **running** (the project's own commands), using the step timestamps.
3. Find the critical path: the PR's slowest job sets its time.
4. Rank fixes by measured seconds saved on the critical path, per PR. Look where the time usually hides:
   - Waiting: runner queue time. A 5-second job that waits 10 minutes for a machine is a 10-minute job. Faster runners cost money.
   - Setup: cache misses on PR runs (no cache seeded from main), installs that a `node_modules` restore would replace, shallow or full clones where a blobless one fits, worker counts above half the runner's cores.
   - Running: bigger machines before more shards, test files sharing a worker, extra work moved off the slowest job, affected-only tests.
5. Apply the free fixes and measure again. Bring the paid ones and anything under "Needs the user's call" to the user with their measured saving and cost.

The audit is done when every fix in the ranking carries a measured saving, and each free fix is applied and re-measured.

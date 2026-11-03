---
name: fast-ci
description: Fast CI for a Git repo. Use when the user says make CI fast (or "fast af"), when CI is slow, when setting up CI or a pre-push hook in a new repo, or when a repo has no .ci-baseline.
---

# fast-ci

Agents push, wait for CI, fix the red check and push again. CI time is the length of that loop, so treat CI like a product: make it as fast as possible while it stays exactly as trustworthy. The playbook comes from Owen Gretzinger's "How I made our CI 20x faster" (https://x.com/owengretzinger/status/2116291924219060319), where PR CI went from 40 minutes to 2.

## Pick the branch

- **Baseline.** The session hook says the repo has no `.ci-baseline`, or the repo is new, or the user asks only for CI or a pre-push hook. Run the Baseline steps and stop.
- **Speedup.** The user says make CI fast, or CI is slow. Run the Speedup steps end to end. A repo with no `.ci-baseline` runs Baseline first and lands it as the Speedup's first PR.

## Baseline

1. Run `bash <this skill's directory>/setup.sh` from inside the repo. It detects the stack, writes `.github/workflows/ci.yml` and `lefthook.yml`, adds `lefthook`, `oxlint` and `oxfmt` to a JS repo, installs the pre-push hook and writes `.ci-baseline`.
   - Exit 2 means there is nothing to detect yet. In a new repo, scaffold first and run setup before the task ends. In a repo with no code to check, ask the user, and on their yes run `setup.sh --skip`.
2. If setup printed a diff, merge each file in `.fast-ci-proposed/` into the existing file it names. Keep every existing job and check, and add the fast-ci pieces it lacks (parallel jobs, `seed-cache`, the `node_modules` cache, blobless checkout, the `ci-ok` gate). Then delete `.fast-ci-proposed/`.
3. If the repo already has a formatter, point the `format` command in `lefthook.yml` and the `lint` job at it. Otherwise run `oxfmt` once over the repo.
4. Keep the Defaults below. Add to the full-run list any file the tests read without importing it (fixtures, demo data, codegen sources).

Baseline is done when `.ci-baseline` exists, `.fast-ci-proposed/` is gone, `lefthook run pre-push --all-files` passes, and `actionlint` passes on the workflow.

## Speedup

Invoking this branch is the user's approval for everything the loop does: branches, pushes, PRs, merges, and reverts of its own merges. Work alone from start to finish. Make every call yourself, fix your own failures, and report once, at the end. A review loop, merge guard or other gate the host or repo sets is part of the step: run it and keep going.

1. **Map the repo.** Find the languages, package manager, monorepo tool, test runner, linter, typechecker, CI provider, workflow files, required checks, branch protection and existing hooks. List every speedup already in place so you skip it.
2. **Audit.** This is where the biggest win hides. Pull the jobs of the last 150 runs:
   `gh run list --limit 150 --json databaseId --jq '.[].databaseId' | xargs -I% gh api 'repos/{owner}/{repo}/actions/runs/%/jobs' --paginate`
   Split every job into **wait** (`created_at` to `started_at`), **setup** (checkout, toolchain, cache restore, install) and **run** (the project's own commands), using step timestamps. Name the critical path (a PR takes as long as its slowest job) and measure the dependency cache hit rate on PR runs against default-branch runs. Setup is the part nobody watches, so read it step by step. Keep the result as the **baseline** in a working file outside the repo: p50 PR time, the per-job wait, setup and run table, and the hit rates. Done when every job has all three numbers.
3. **Rank.** Read [`playbook.md`](playbook.md). Mark every item do, already done, or no fit for this stack, and order the do items by seconds saved on the critical path, then by lowest risk.
4. **Land one change at a time.** For each do item:
   1. Branch off the latest default branch and make the change as a small diff.
   2. Run the checks locally. Push and open a PR whose description gives the baseline time and the saving you expect.
   3. Watch its run with `gh run watch <id>` until it ends. On red, find the root cause and fix it. Every test and check keeps its strength through the fix.
   4. After 3 real fix attempts that leave it red, flaky or slower than the baseline, close the PR, delete the branch, record why, and take the next item.
   5. Once it is green and measurably faster, merge it the way recent merged PRs in this repo were merged, passing the full commit SHA when a merge guard asks. Then watch the default branch's push run. If it goes red, revert the merge at once and count the change as failed.
   6. Record the before and after times from real runs.
5. **Finish.** Pull the last 20 runs and compare them with the baseline. If one job is still clearly the bottleneck and a playbook item could still fix it, go back to step 4. Done when no remaining item fits the bottleneck, every worktree and branch you created is gone, and the default branch is green.
6. **Report**, as below.

## Guardrails

Trust stays exactly where it was. These hold for every change, and each one you hit goes in the report:

- Never switch to paid runners. Estimate them instead (see the report).
- Never remove, skip or weaken a test or a required check, and never change branch protection.
- Never touch other people's branches, other open PRs, or the user's untracked files.
- Never force-push the default branch.

## Push and wait

- When a fix lands low in a stack of PRs, rebase the stack locally and push only the top branch, then let CI run once. Never re-push every branch at once. That starts one run per branch, and the parallel runs overload the runners and cause new failures.
- Do not subscribe an agent to PR or CI webhooks. Cancelled duplicate runs fire events too, so every event wakes the agent for nothing. Wait on a single run with `gh run watch <id>`.

## Defaults

Each comes from a measured rollout. Change one only from this repo's own measured runs.

- Shards: 4, because 4 shards took BDM Meeting Insights CI from 504s to 206s at p50, and a 2-vCPU runner is one physical core, so more runners is the free way to more cores.
- Workers per runner: half the runner's cores, one per physical core, because 2 workers on BDM's 2-vCPU runner made timing tests flaky and one per core was the safe level on Listing QA (CI 45.4 to 13.3 min at p50).
- Raising concurrency (workers, shards, or test files sharing a worker): run the suite 5 times in a row at the new level before you call it done. If a timing-based test fails, lower the concurrency before you loosen a timeout. Record the setting and why in a comment next to it.
- Full test run: a change to a lockfile, `package.json`, `pnpm-workspace.yaml`, `.npmrc`, `.node-version`, `.nvmrc`, `tsconfig*.json`, Vite or Vitest config, `.env*`, `.github/`, `patches/` or the shared test setup runs every test, because Vitest's import graph cannot see those files.
- `node_modules` cache key: OS, architecture, runtime version and a hash of the lockfiles, `pnpm-workspace.yaml`, `.npmrc` and `patches/`, so the cache misses exactly when an install would produce different files.

## Style

Docs, commits and PR descriptions use plain English with no em dashes, in the style of Theo's t3code repo. A commit title is Conventional Commits with a scope that states the outcome, such as `perf(ci): PRs restore the dependency cache main saved`. A PR body opens with a paragraph on what was slow and why, then "Now ..." with what changed and the measured times.

## Report

Send it once, after Finish. Emojis are welcome here.

- 🔍 The stack and CI setup you found, and what was already in place.
- ⏱️ PR CI time before and after (p50), and a per-job table of wait, setup and run, before and after.
- ✅ Each merged PR with its link and its own before and after times.
- 🧹 What you skipped or reverted, and why, including every guardrail you hit.
- 💸 The paid runner estimate, for the user to decide on: the wait time it would save per PR (from the audit), and the monthly cost at this repo's run volume at the provider's current per-minute price. Every job has to move, because a 5-second job that waits 10 minutes for a machine is a 10-minute job. Owen moved to Blacksmith with one line per job (`runs-on: blacksmith-4vcpu-ubuntu-2204`), which took his queue from 11 minutes to 8 seconds and his bill from 230 to 4,300 dollars a month. Vercel CI and boat.dev are alternatives.

End with one hype line of your own that carries the real numbers, like `🏎️💨 PR CI went from 14m to 2m10s. It's fast af now, boiiii 🔥`. When the time barely moved, end with the honest number and what blocks it, still with the emojis.

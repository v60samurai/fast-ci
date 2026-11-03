# fast-ci playbook

The Speedup's menu, read at its Rank step. Do every item that fits this stack, is not already done, and saves real time on the critical path. Owen Gretzinger's measured results set the expected size of each win:

| Change | Before | After |
|---|---|---|
| Runners that are not GitHub's (paid, see the report) | up to 11 min waiting for a machine | 8 s |
| Oxlint instead of ESLint | 2 min | 5 s |
| tsc to TypeScript 7 to bun check | 70 s | under 5 s |
| Test files share a worker | 100 s per shard | 35 s |
| Cache seeded from main | half of PR runs missed | 1% |
| Server test job setup fixes | 168 s | 74 s |
| node_modules cache vs install | 33 s install | 13 s restore |
| Blobless clone vs shallow | 36 s checkout | 12 s |

## a. Seed the cache from the default branch

GitHub scopes PR caches to their own branch, so unless the default branch saves one, most PRs start cold. Run the cache-saving job on pushes to the default branch so PR caches restore from it. Cache the installed dependencies (`node_modules`, `.venv` or the equivalent) keyed on the lockfile, beyond the package manager's download cache. The Baseline template's `seed-cache` job does this.

## b. Blobless clone

Use `actions/checkout` with `filter: blob:none`, and `fetch-depth: 0` where history is needed. A shallow clone breaks anything that reads git history.

## c. Fastest linter

For JS and TS, replace ESLint with Oxlint, keeping ESLint only for rules Oxlint cannot cover yet. Use Biome if the repo already does. For Python, use Ruff. Keep every rule enforced today, and turn on every other rule the code passes for free (for Oxlint, every category in `.oxlintrc.json`). Strict rules make the wrong thing hard to write and cost an agent nothing. Fix the new lint errors it finds.

## d. Fastest typechecker

For TS, benchmark `tsc` against TypeScript 7 (`tsgo`, from `@typescript/native-preview`) and, in a Bun project, `bun check`. Point the `typecheck` script at the fastest one whose errors match `tsc`'s on this repo. Note any faster local-only option in the report. Switch again whenever a faster one ships.

## e. Test files share a worker

Vitest gives every test file a fresh worker by default, so every file reloads the app. Set `test.isolate: false` (Jest: `isolateModules` off; pytest: reuse xdist workers). Add a `setupFiles` hook that resets shared state after every file: database rows, mocks, globals, timers and module singletons. Write in `AGENTS.md` what a test has to clean up. Keep the change only if the suite is green 5 runs in a row.

## f. More cores before more shards

If tests are the critical path, find where the CPU goes. Owen's shards spent most of their time loading modules, so cores helped more than shard count. A bigger machine counts only when it costs nothing more (a larger runner the org already has, or a self-hosted one); otherwise it goes in the paid estimate. Shard across parallel jobs, each with its own database, only if sharding still helps after item e. Owen used 6.

## g. Match concurrency to cores

A 4-vCPU job runs 2 to 4 tasks, never 8. Owen halved his concurrency with no slowdown, and it killed a flaky test. The Defaults in `SKILL.md` give the level to start at.

## h. Everything in parallel

Lint, typecheck, build and tests run as separate parallel jobs, so a PR takes as long as the slowest one. Then read what else the slowest job does (migration checks, other apps' tests) and move each piece into its own job. That alone saved Owen 2 minutes.

## i. Only run what a PR touches

Use the monorepo tool's affected command (`nx affected`, `turbo --filter=...[origin/main]`, `pnpm --filter ...[origin/main]`) or a path-based selector, and run the full suite on the default branch every night. The Baseline template runs Vitest's affected tests on PRs behind a `ci-ok` gate. Then test the skip logic itself: on purpose, make a change the selector would miss, and confirm the run fails. A skipped required job reports green only when the change truly needed nothing it skipped.

## j. Checks before every push

A pre-push hook (lefthook, husky, or a plain git hook installed by the repo's setup script) runs format, lint and typecheck on the changed files only, in under 10 seconds. Owen's takes 9. Time it. It lives in a hook because agents skip steps written in `AGENTS.md`. The Baseline's `lefthook.yml` is this hook.

## k. Keep every test

Owen had an agent audit 20,000 test cases and found almost nothing worth cutting, because the time was never in the tests. Look for it in wait, setup and module loading.

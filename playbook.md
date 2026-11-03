# fast-ci playbook

The Speedup's catalog of CI techniques, read at its Rank step. It holds every technique from StarSling's CI playbooks (https://starsling.dev/ci-playbooks), plus fast-ci's own items from Owen Gretzinger's "How I made our CI 20x faster" (https://x.com/owengretzinger/status/2116291924219060319). The raw source list is [`research/starsling-index.md`](research/starsling-index.md).

## Categories

Open the file for each bottleneck the audit found. A technique lives in one file, under the bottleneck it fixes first.

| File | Bottleneck | Read it when the audit shows |
|---|---|---|
| [`playbook/caching.md`](playbook/caching.md) | Caching and setup | setup is a large share of a job, PR cache misses, slow checkout or installs |
| [`playbook/unnecessary.md`](playbook/unnecessary.md) | Unnecessary work | the same command in several jobs, runs on irrelevant events, tools installed and unused |
| [`playbook/selection.md`](playbook/selection.md) | Test selection | every PR runs every test or job, whatever it touched |
| [`playbook/parallel.md`](playbook/parallel.md) | Parallelization and sharding | one long job sets the critical path, uneven shards, serial independent steps |
| [`playbook/slow-tests.md`](playbook/slow-tests.md) | Slow tests and checks | the test, lint or typecheck step itself dominates run time, or flaky reruns |
| [`playbook/runners.md`](playbook/runners.md) | Queue and runner speed | jobs wait for a runner, or CPU-bound work on small machines |
| [`playbook/cost.md`](playbook/cost.md) | Compute waste | superseded runs still running, jobs without timeouts, blind retries |
| [`playbook/agent-volume.md`](playbook/agent-volume.md) | Agent PR volume | many agent PRs or pushes per day, agent CI rounds that never end |

## Entry format

Every entry has this shape, and `tests/rules.sh` checks every field:

```markdown
### <id>: <one-line name>

- **applies when:** <the audit signal and its threshold, from the list below>
- **how:** <concrete steps, with a GitHub Actions snippet or tool name where one exists>
- **estimate:** <how to turn the audit's numbers into seconds saved per run>
- **verify:** <how to prove it saved time and that no check got weaker>
- **risk:** low | medium | high
- **mode:** auto | report-only (<reason>)
- **evidence:** <StarSling page, then company sources and PR links>
```

The id is the StarSling technique slug, so a refresh can diff against the index. fast-ci's own entries start with `fc-`. Every tool in **how** is free and open source.

## Audit signals

The Speedup's Audit step computes these, and every **applies when** line names at least one. Runtime signals come from the last 150 runs; static signals come from reading the workflow files.

- `runs_per_day`: runs per day, split by PR and default branch.
- `pr_p50`: p50 PR wall time, created to completed.
- `wait_s`: per job, `created_at` to `started_at`.
- `setup_s`, `setup_share`: per job, checkout, toolchain, cache restore and install seconds, and their share of the job.
- `checkout_s`, `install_s`, `tool_install_s`, `image_pull_s`: those setup steps on their own.
- `cache_hit_pr`, `cache_hit_main`: dependency cache hit rate on PR runs and on default-branch runs.
- `run_s`: per job, the project's own commands.
- `critical_path`: per workflow and job, how often it is the slowest job of a PR run (`slowest_in`) and its p50 over `pr_p50` (`share_of_pr_p50`).
- `shard_skew`: slowest shard divided by fastest shard.
- `superseded_running`: PR runs that kept running after a newer commit on the same PR started.
- `rerun_rate`: runs that passed only on a rerun of the same commit (flaky).
- `infra_fail_rate`: failed jobs whose failing step is setup, or with no failed step (runner lost), over all jobs. `timed_out_jobs` counts hangs on their own.
- `draft_runs`: runs on draft PRs. The runs API has no draft state, so read the workflow's draft filter.
- `irrelevant_runs`: runs whose PR changed only files no job reads (docs-only PRs running the full suite). Check it by hand against the paths filters.
- `duplicate_steps` (static): the same build or install command in more than one job of a run.
- `no_timeout_jobs` (static): jobs with no `timeout-minutes`.
- `no_concurrency` (static): a PR workflow with no `concurrency` group.
- `agent_prs_per_day`: PRs or pushes per day from agents and bots.

## Mode

**auto** means the Speedup loop may land the entry, one PR at a time. **report-only** means the loop only estimates the saving and puts it in the report for the user to decide. An entry is report-only, with its reason in brackets, when it does any of these:

- `paid-runner`: moves jobs to paid, bigger or faster runners, whatever they cost (GitHub larger runners, StarSling, Blacksmith and similar).
- `after-merge`: moves a check to after merge, or drops a blocking gate.
- `merge-gate`: changes the merge queue or branch protection, such as merging without retesting against the latest main.
- `weakens-check`: removes, skips or weakens a test or a required check.
- `agent-workflow`: is an agent process outside CI (agent code review, on-call agents, ticket agents, cleanup agents, security agents).
- `needs-infra`: needs infrastructure outside the repo, such as self-hosted runners, a checkout service or a remote cache server.

Test selection skips tests on a PR, so every selection entry is report-only, even when it runs every test a change can reach. The report gives its estimate and the deliberate-miss check and nightly full run it would need.

## Owen Gretzinger's results

His measured wins set the expected size of the entries they back:

| Change | Before | After | Entry |
|---|---|---|---|
| Runners that are not GitHub's | up to 11 min waiting for a machine | 8 s | `faster-runners` |
| Oxlint instead of ESLint | 2 min | 5 s | `native-lint-tools` |
| tsc to TypeScript 7 to bun check | 70 s | under 5 s | `native-type-checking` |
| Test files share a worker | 100 s per shard | 35 s | `share-module-state` |
| Cache seeded from main | half of PR runs missed | 1% | `fc-seed-cache-from-main` |
| Server test job setup fixes | 168 s | 74 s | `setup-cost-limits-sharding` |
| node_modules cache vs install | 33 s install | 13 s restore | `fc-seed-cache-from-main` |
| Blobless clone vs shallow | 36 s checkout | 12 s | `blobless-history` |

He also had an agent audit 20,000 test cases and found almost nothing worth cutting, because the time was never in the tests. Look for it in wait, setup and module loading first.

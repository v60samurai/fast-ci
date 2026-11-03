# Compute waste

Runner time goes to work nobody reads: runs a newer commit replaced, jobs that hang until the platform limit, retries that fail the same way twice, and setup repeated across tiny jobs. Cutting it frees runners, which lowers `wait_s` for every other run.

### cancel-superseded-runs: Cancel superseded pull request runs

- **applies when:** `superseded_running` over 0, or `no_concurrency` on a PR workflow (static).
- **how:** Add a workflow `concurrency` group keyed on the workflow and the PR number, and cancel in progress only for `pull_request` events. Keep default-branch, release, deploy and migration runs out of `cancel-in-progress`. On the default branch, key the group on the commit SHA so main runs never cancel or replace each other (Anthropic). Deploy, publish and migration workflows get their own group with `cancel-in-progress: false`. For `workflow_run` and comment-driven events, key on the logical PR, not the event's own ref (Mastra). Runs for different PRs must never share a group (Uber). The fast-ci Baseline template already sets this.
  ```yaml
  concurrency:
    group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.sha }}
    cancel-in-progress: ${{ github.event_name == 'pull_request' }}
  ```
- **estimate:** `superseded_running` per day times the runner time those runs spent after the newer push started. Wall time for the newer run drops by the `wait_s` the superseded jobs caused when runners were scarce.
- **verify:** Push twice in a row to a test PR: the first run shows cancelled and the second completes. Two quick pushes to main both run to completion. Deploy and release workflows never cancel. `superseded_running` reads 0 over the next 50 runs, and every required check still reports on the latest commit.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/cancel-superseded-runs.md), [Anthropic](https://github.com/anthropics/anthropic-sdk-python/commit/c8e75ece9e407966ed077a8e4e924e7ebd041c71), [Mastra](https://github.com/mastra-ai/mastra/pull/14432), [Stripe](https://github.com/stripe/stripe-ios/pull/7337), [Uber](https://github.com/uber/baseweb/pull/5407)

### bound-job-runtime: Put time limits on jobs that can hang

- **applies when:** `no_timeout_jobs` over 0, or any run in the last 150 ran a job near the 360-minute default.
- **how:** Every job gets `timeout-minutes` set to about 3 times its p95 run time from the audit, with room for a cold setup. For a job with few runs, use 3 times its longest successful run. Add a step-level `timeout-minutes` on steps known to hang, such as simulator boots and integration tests. Lengthen a bound only from real tail data (Mastra later lengthened its checkout timeouts). A timed-out required check still blocks the merge, so the hanging test gets fixed by name. Shopify put a 5-minute timeout on a matrix that normally runs in under a minute. Spotify set 45 minutes on an iOS job whose passing run took 6m34s, plus 30 minutes on its integration test step.
  ```yaml
  jobs:
    test:
      runs-on: ubuntu-latest
      timeout-minutes: 15 # about 3x p95 (4m50s over the last 150 runs)
  ```
- **estimate:** Healthy runs save nothing. Each hung run saves 360 minutes minus the timeout of runner time, times the hung runs per 150. The agent waiting on that run sees red at the timeout instead of after 6 hours.
- **verify:** A search of the workflow files shows `no_timeout_jobs` at 0. Over the next 50 runs no healthy job times out. A timeout on a run that would have passed means the bound is too tight, so raise it. Required checks are unchanged.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/bound-job-runtime.md), [Anthropic](https://claude.com/resources/articles/agentic-coding-is-straining-ci-heres-how-we-scaled-test-impact-analysis-at-anthropic), [Mastra](https://github.com/mastra-ai/mastra/blob/f92e947a448a47515acf14df1eddc5fd5c36f424/.github/workflows/test-combined-stores.yml), [Mastra](https://github.com/mastra-ai/mastra/pull/14098), [Shopify](https://github.com/Shopify/job-iteration/pull/717), [Spotify](https://github.com/spotify/confidence-sdk-flutter/pull/72)

### retry-infra-failures-only: Retry only infrastructure failures

- **applies when:** CI retries jobs or tests automatically (static: a retry action around a test command, Vitest or Playwright `retries`, Jest `jest.retryTimes`, pytest `--reruns`, or a workflow that reruns failed jobs), or `rerun_rate` over 2%, or most automatic retries end the same way as the first attempt.
- **how:** Retries are for runner loss, network and timeouts, never for test failures. Wrap only the steps that touch the network (install, image pulls, downloads) in a step retry, and leave test commands unwrapped. A test that fails and then passes is a flake to fix, not to retry, so remove test-level retries and list each flaky test by name for fixing. A test shard that times out reports once, with no second run. If the repo reruns failed jobs automatically, match only runner-loss errors in the job log. Bun's retry rules matched every timed-out shard. Across about 200 builds they made about 670 retries, of which 465 timed out again and 182 were cancelled, which the PR counts as 97% wasted.
  ```yaml
  - uses: nick-fields/retry@v3
    with:
      timeout_minutes: 5
      max_attempts: 3
      retry_on: error
      command: pnpm install --frozen-lockfile
  - run: pnpm test # never retried: a flaky test gets fixed
  ```
- **estimate:** From the last 150 runs, the automatic retry attempts that ended in the same failure, times their `setup_s` plus `run_s`, divided by runs. Without that split, use Bun's 97% of retry time as waste. A kept infra retry saves one manual rerun, about `pr_p50`, per failure counted in `infra_fail_rate`.
- **verify:** Over the next 50 runs, no test or test job runs twice for the same commit on its own. A deliberate failing test fails once, with no retry. A deliberate network failure in a setup step retries and then recovers or fails after the last attempt. Test counts are unchanged, and `rerun_rate` now shows the flakes instead of hiding them.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/retry-infra-failures-only.md), [Anthropic](https://github.com/oven-sh/bun/pull/34684)

### share-small-job-setup: Share setup across small checks

- **applies when:** two or more jobs in a run have `setup_share` over 70% and `run_s` under 60 s, none of them is the `critical_path` job, and branch protection does not require their names one by one (it requires an aggregate such as `ci-ok`, or none of them).
- **how:** Merge compatible short checks into one job that runs them concurrently and fails if any part fails, such as `npx concurrently --names lint,types "pnpm lint" "pnpm typecheck"`, which exits non-zero when any command fails. Keep every check and its exit status, keep required names through the aggregate, and split again when the combined job becomes the long pole. Linear merged seven small checks into two jobs and saved about 87,000 runner-minutes a month, 11.8% of its CI usage. Stripe iOS paired small jobs, such as snapshot recording with the localization upload, so each pair pays setup once.
- **estimate:** Runner time per run: (number of merged jobs minus 1) times their average `setup_s`. Wall time does not drop, and the combined job's setup plus its longest part must stay under the `critical_path` job's time.
- **verify:** A deliberate failure in each merged check fails the combined job, with that check's name in the log. `pr_p50` is the same or lower over 20 runs, and runner minutes per run are lower. Required checks still report.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/share-small-job-setup.md), [Linear](https://linear.app/now/ci-bottleneck-reworked#batch-short-checks-into-fewer-jobs), [Stripe](https://github.com/stripe/stripe-ios/pull/6969)

### bounded-agent-execution: Bound agent execution and retries

- **applies when:** `agent_prs_per_day` over 0 and agent PRs average more than 3 push-and-fix rounds (CI runs per agent PR), or an agent step inside a CI job is stopped only by the job-wide timeout.
- **how:** Cap agent CI rounds: a fixed number of push-and-fix rounds before the agent hands the branch back to a person, with the remaining failures visible. Stripe gives each agent at most two CI rounds, and fast-ci's own Speedup stops after 3 real fix attempts. For an agent that runs inside a CI job, set a soft timeout from measured run times that asks it to drop anything speculative and return only verified findings, and a hard timeout as the kill switch. DoorDash found a model request could repeat without advancing the turn counter, so max-turn limits never fired and one stuck agent burned 20 minutes; its cleanup agents run under a one-hour hard timeout. Cap turns per session and session retries too (Spotify: 10 turns and 3 retries). Set the limits from the longest successful sessions, and split a task that needs more.
- **estimate:** Per agent PR, the rounds beyond the cap times `pr_p50`, plus, for agents inside CI, the minutes stuck runs spent past the soft limit.
- **verify:** For the report: rounds per agent PR and stuck-agent minutes from run history. If adopted, no agent PR goes past the cap, branches handed back carry their failures, soft-stopped runs report as partial, and normal runs finish under the soft limit.
- **risk:** medium
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/bounded-agent-execution.md), [DoorDash](https://careersatdoordash.com/blog/doordash-built-an-ai-code-reviewer-engineers-actually-listen-to/), [Spotify](https://engineering.atspotify.com/2025/11/context-engineering-background-coding-agents-part-2), [Stripe](https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents-part-2)

### faster-release-linker: Link release builds with a faster linker

- **applies when:** a build profile (`cargo build --timings`, or the link step's own timing) shows linking or final code generation over 30% of a build job's `run_s`.
- **how:** Configure a faster linker before the build. On Linux, rui314/setup-mold@v1 makes mold the default linker, and LLVM's lld is the other free choice. On Windows, point Cargo at LLVM's `lld-link`. OpenAI profiled its Windows x64 release build, found most of the time in final code generation and linking, and now sets the LLVM linker before the Cargo build.
  ```yaml
  - uses: rui314/setup-mold@v1
  - run: cargo build --release
  ```
- **estimate:** The link step's seconds times (1 minus the new linker's ratio), measured once locally with both linkers. OpenAI estimated about four minutes off its release workflow.
- **verify:** Every linked binary passes the same tests and signing steps as before. Compare the build job's time over 5 runs.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/faster-release-linker.md), [OpenAI](https://github.com/openai/codex/pull/27315)

### profile-release-linking: Measure the cost of the release build profile

- **applies when:** compiling or linking a release profile is over 50% of `run_s` on a build job on the critical path, and the profile uses fat LTO or `codegen-units = 1` (static).
- **how:** Measure what the profile costs before keeping it: clean-build time, binary size and runtime on a representative workload, for each candidate (`lto = "fat"` against `lto = "thin"`, different `codegen-units`). OpenAI moved Codex from fat LTO to ThinLTO, kept optimization level 3 and removed the workflow overrides. Its clean release build went from 2073.893 s to 1243.172 s, and the binary grew from 196.7 MiB to 211.8 MiB. Keep size and runtime checks next to the faster build, and put the size and runtime change in the PR.
- **estimate:** The clean build's seconds times (1 minus the new ratio). Use OpenAI's ratio of about 0.6 until the repo measures its own.
- **verify:** Every test passes. Binary size and a benchmark run are recorded before and after and stay within the repo's existing limits. Compare clean build time over 3 runs each.
- **risk:** high
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/profile-release-linking.md), [OpenAI](https://github.com/openai/codex/pull/23710)

### measure-gc-memory-budget: Measure the analyzer's garbage-collection budget

- **applies when:** a Go-based analyzer step (golangci-lint, staticcheck) is over 60 s of `run_s`, and its peak memory is under half the runner's RAM.
- **how:** Set `GOGC=400` and derive `GOMEMLIMIT` from half of physical RAM, capped (OpenAI capped it at 6 GiB). `GOMEMLIMIT` is a soft limit per Go process, and concurrent processes and native allocations can still exhaust the runner, so budget the memory that is actually free.
  ```yaml
  - name: Lint
    run: |
      limit=$(( $(awk '/MemTotal/ {print $2}' /proc/meminfo) / 2048 ))
      [ "$limit" -gt 6144 ] && limit=6144
      GOGC=400 GOMEMLIMIT="${limit}MiB" golangci-lint run
  ```
- **estimate:** The lint step's seconds with and without the settings on the same runner, over 3 runs each. The difference is the saving per run.
- **verify:** A seeded lint violation still fails with the same finding. No out-of-memory failure over 20 runs. Compare the step's time over 10 runs.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/measure-gc-memory-budget.md), [OpenAI](https://github.com/openai/openai-go/pull/996)

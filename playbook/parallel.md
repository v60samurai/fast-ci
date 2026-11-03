# Parallelization and sharding

A PR takes as long as its slowest job, so the bottleneck here is work that runs in series when it could run side by side: independent checks chained by `needs:`, one long job doing several unrelated things, a test suite on one runner or one worker, and shards that finish at very different times.

### parallel-independent-checks: Run independent checks in parallel

- **applies when:** a static pattern shows lint, typecheck, build or tests in one job, or chained by `needs:` when the later job reads none of the earlier job's outputs or artifacts, and the chain is the `critical_path` at over 50% of `pr_p50`.
- **how:** Give lint, typecheck, build and tests each their own job with no `needs:` between them, so a PR takes as long as the slowest one (Owen's setup). Keep `needs:` only where a job downloads another job's artifact, or where it is a deliberate gate before a deploy. Turn off a build's built-in lint (Next.js `next build` lint) only once the separate lint job is required. Inside one job, run independent checks through the task runner in one call (`turbo run lint format:check`), keeping autofix commands in order. Add one aggregate job so the required check name stays the same and branch protection does not change:
  ```yaml
  ci-ok:
    if: always()
    needs: [lint, typecheck, build, test]
    runs-on: ubuntu-latest
    steps:
      - if: contains(needs.*.result, 'failure') || contains(needs.*.result, 'cancelled')
        run: exit 1
  ```
- **estimate:** old `critical_path` minus the new one, where the new one is the largest over the new jobs of (`wait_s` + `setup_s` + that check's own run seconds). DoorDash saw lint results 5 minutes sooner by running its 3 minutes of ESLint beside the Next.js build.
- **verify:** compare p50 `pr_p50` over 10 runs before and after. Every check that ran before still runs, with the same file filters and the same test count, and `ci-ok` is the only required check. Push a commit with a deliberate lint error and confirm `ci-ok` goes red while the tests still run.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/parallel-independent-checks.md), [Anthropic](https://github.com/oven-sh/bun/pull/34682), [DoorDash](https://careersatdoordash.com/blog/how-doordash-slashed-web-developer-build-times/), [Mastra](https://github.com/mastra-ai/mastra/pull/18428), [OpenAI](https://github.com/openai/openai-cli/pull/489), [Shopify](https://github.com/Shopify/tecnix/pull/74), [Uber](https://www.uber.com/us/en/blog/how-we-halved-go-monorepo-ci-build-time/), [Owen Gretzinger](https://x.com/owengretzinger/status/2116291924219060319)

### split-long-lanes: Split independent work off the longest job

- **applies when:** the `critical_path` job runs two or more independent steps in series (migration checks, another app's tests, an integration suite after unit tests), and its `run_s` is over 1.5 times the next slowest job.
- **how:** Read the slowest job step by step and list what else it does besides its main command. Move each independent piece (migration checks, other apps' tests, a slow test class) into its own job with the same setup, and add it to the `ci-ok` aggregate's `needs:`. Keep variants that share expensive setup together in one job, as Stripe kept its five installation variants. Owen did this after splitting lint, typecheck, build and tests, and it alone saved him 2 minutes.
- **estimate:** the slowest job's `run_s` minus the longest piece left in any one job, minus the new job's `setup_s` and `wait_s` if those make it the new long pole. Stripe's 27-minute job became 11 to 12 and 13 minutes running side by side.
- **verify:** compare p50 `critical_path` over 10 runs before and after. The split jobs together run the same steps and test count as the old job, and every new job is in `ci-ok`'s `needs:`. Break one moved piece on purpose and confirm `ci-ok` goes red.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/split-long-lanes.md), [Stripe](https://github.com/stripe/stripe-ios/pull/7334), [Owen Gretzinger](https://x.com/owengretzinger/status/2116291924219060319)

### shard-test-suites: Split long test suites across runners

- **applies when:** one test job is the `critical_path` at over 40% of `pr_p50`, its `run_s` is over 120 s, and it runs on one runner with no `--shard` or matrix.
- **how:** Run the suite as a matrix of shards with the runner's own flag (`vitest --shard`, `jest --shard`, `playwright test --shard`, `bun test --shard`, `pytest-split` for pytest). fast-ci's default is 4 shards, because a 2-vCPU runner is one physical core and more runners is the free way to more cores. Set `fail-fast: false`, give each shard's artifacts a unique name, merge coverage in a job after the shards, and put the shards behind the `ci-ok` aggregate so the check name stays the same. Isolate shared state first (`isolated-parallel-tests`).
  ```yaml
  test:
    strategy:
      fail-fast: false
      matrix:
        shard: [1, 2, 3, 4]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - run: npm ci
      - run: npx vitest run --shard=${{ matrix.shard }}/4
  ```
- **estimate:** the test job's `run_s` times (1 minus 1.2 / N) for N shards, where 1.2 allows for uneven shards, and minus about 30 s if a coverage merge job is added in series. Each shard still pays `setup_s`, so runner minutes rise by (N minus 1) times `setup_s`. At 4 shards, BDM CI went from 504 s to 206 s at p50, and Shopify went from 11m 43s to 7m 44s on two shards.
- **verify:** compare p50 `pr_p50` over 10 runs before and after, and the shard count stays as set for 5 green runs in a row. The shards together report the same total test count as the single job, every test runs exactly once, and a deliberate failure in one shard turns `ci-ok` red.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/shard-test-suites.md), [Anthropic](https://bun.sh/blog/bun-v1.3.13), [DoorDash](https://careersatdoordash.com/blog/how-doordash-slashed-web-developer-build-times/), [Mastra](https://github.com/mastra-ai/mastra/blob/f92e947a448a47515acf14df1eddc5fd5c36f424/.github/workflows/e2e-tests.yml), [Mastra](https://github.com/mastra-ai/mastra/pull/15888), [OpenAI](https://github.com/openai/openai-cli/pull/511), [Shopify](https://github.com/Shopify/cli/pull/7350), [Spotify](https://github.com/spotify/confidence-cli/pull/73), [Stripe](https://github.com/stripe/stripe-android/pull/13225)

### tune-test-workers: Match test concurrency to the runner

- **applies when:** the test config sets a fixed worker count, or no count, that was never measured on this runner (static: `--maxWorkers=8`, `-n auto` on a 2-vCPU runner, Playwright `workers` above the core count), or `rerun_rate` is over 2% on a test job, or runner loss shows in `infra_fail_rate` over 1% on a test job.
- **how:** Start at half the runner's cores, one worker per physical core: `--maxWorkers=50%` for Vitest and Jest, `pytest -n $(( $(nproc) / 2 ))` for pytest-xdist, the same ratio for Playwright `workers` and Bazel `--local_test_jobs`. A 4-vCPU job runs 2 to 4 workers, never 8. Count nested worker processes and memory toward the limit, and cap workers lower when the job runs out of memory. Raising concurrency needs 5 green runs in a row at the new level. If a timing test fails, lower concurrency before you loosen a timeout. Record the setting and why in a comment next to it.
- **estimate:** when workers exceed physical cores, expect no slowdown from halving them (Owen halved his with no slowdown), plus `rerun_rate` times the job's full time saved per run. When the suite runs on fewer workers than cores, the test step's `run_s` times (1 minus old workers / new workers), capped by memory. On Listing QA, one worker per core took CI from 45.4 to 13.3 min at p50, and OpenAI's slowest shard went from 835.5 s to 609.3 s at 8 local jobs.
- **verify:** compare p50 test job `run_s` and `rerun_rate` over 10 runs before and after, and require 5 green runs in a row at the new level. The same test count runs, and no timeout was raised.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/tune-test-workers.md), [Anthropic](https://github.com/oven-sh/bun/pull/36175), [Mastra](https://github.com/mastra-ai/mastra/pull/13937), [Mastra](https://github.com/mastra-ai/mastra/blob/f92e947a448a47515acf14df1eddc5fd5c36f424/packages/memory/integration-tests/vitest.config.ts), [OpenAI](https://github.com/openai/codex/pull/31352), [Stripe](https://github.com/stripe/stripe-ios/pull/7333), [Owen Gretzinger](https://x.com/owengretzinger/status/2116291924219060319)

### setup-cost-limits-sharding: Reduce the setup floor before adding shards

- **applies when:** a test job is the `critical_path` and its `setup_share` is over 30%, or each shard spends most of its run loading modules rather than running tests, or a PR proposes more shards while per-shard `setup_s` is over 60 s.
- **how:** If tests are the critical path, find where the CPU goes before adding shards. Owen's shards spent most of their time loading modules, so cores helped more than shard count. First cut per-shard setup with the caching entries and let test files share a worker (`share-module-state`). Shard across parallel jobs, each with its own database (Owen used 6), only if sharding still helps after that. Any move to a bigger or faster runner, paid or not, belongs to `faster-runners` and is report-only. Otherwise it belongs to `faster-runners`, which is report-only. Remeasure per-shard setup before every shard count change.
- **estimate:** the test job's `setup_s` minus its measured floor (restore and boot only) comes off every shard. Owen's server test job setup fixes took it from 168 s to 74 s. A move from N to N + 1 shards saves `run_s` times (1 / N minus 1 / (N + 1)) of wall time and costs one more `setup_s` of runner minutes, so stop adding shards when that saving falls under about 15 s.
- **verify:** compare p50 test job `setup_s` and `critical_path` over 10 runs before and after. The test count and the database each shard gets stay the same, and a deliberate failure in one shard turns the aggregate red.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/setup-cost-limits-sharding.md), [Linear](https://linear.app/now/ci-bottleneck-reworked#sharding-is-limited-by-setup-overhead), [Owen Gretzinger](https://x.com/owengretzinger/status/2116291924219060319)

### balance-test-shards: Balance test work across shards

- **applies when:** `shard_skew` is over 1.3, or one test file takes over half the slowest shard's `run_s`.
- **how:** Split the biggest test files, because Vitest and Jest assign work by file and one large file still sets its shard's time. Then assign by measured duration rather than path: save JUnit timings from the default branch and split with `pytest-split --durations-path`, Playwright's per-file timings, or a longest-first assignment to the least-loaded shard. Refresh the timings from default-branch runs so new slow tests spread out, and keep a catch-all shard that runs every test not explicitly assigned.
- **estimate:** the slowest shard's `run_s` minus the mean shard `run_s`. OpenAI's Windows tests went from a 22m26s median on one job to 7m29s on four balanced shards, and Ramp's better packing saved 2 to 3 minutes.
- **verify:** compare `shard_skew` and p50 `critical_path` over 10 runs before and after. The union of test IDs across shards equals the old union, with no duplicates, and a new test file lands in the catch-all shard.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/balance-test-shards.md), [Linear](https://linear.app/now/ci-bottleneck-reworked#balance-work-the-way-the-test-runner-sees-it), [OpenAI](https://github.com/openai/codex/pull/22408), [Ramp](https://builders.ramp.com/post/faster-python-tests-part-two), [Stripe](https://github.com/stripe/stripe-ios/pull/7333)

### isolated-parallel-tests: Isolate state before running tests in parallel

- **applies when:** a static pattern shows a test job forced to one worker (`workers: 1`, `--runInBand`, `fileParallelism: false`, `-p no:xdist`) because tests share a database, port, account or temp directory, and that job's `run_s` is over 120 s.
- **how:** Give each worker its own state: one database or schema per worker (keyed on `VITEST_POOL_ID`, `JEST_WORKER_ID` or `PYTEST_XDIST_WORKER`), ephemeral ports discovered at runtime, a temp directory and account per test, and a Docker Compose project name per suite. Do one-time setup (process sweep, runtime install) in global setup before workers start, and replace fixed sleeps with a readiness probe. Keep tests that truly share a remote endpoint in a serial lane. Then raise workers as in `tune-test-workers`. With a shared database, measure the workers-per-database ratio (Ramp settled on about 12).
- **estimate:** the serial job's `run_s` times (1 minus 1 / W) times about 0.75 for W workers. Shopify went from about 27 minutes on 1 worker to about 10 minutes on 5.
- **verify:** compare p50 test job `run_s` over 10 runs before and after, and require 5 green runs in a row. The same test count runs, and the serial lane still runs every test it held.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/isolated-parallel-tests.md), [DoorDash](https://github.com/doordash-oss/agentic-orchestrator/pull/139), [Ramp](https://builders.ramp.com/post/faster-python-tests-part-two), [Shopify](https://github.com/Shopify/cli/pull/7309), [Stripe](https://github.com/stripe/sync-engine-fork/pull/124), [Uber](https://github.com/uber/submitqueue/pull/41)

### parallel-test-packages: Run independent test packages concurrently

- **applies when:** a static pattern shows a shell loop running tests one package, crate or module at a time (`for p in ...; do go test $p`, one `cargo test -p` per crate, one tox env after another), or one test environment's `run_s` is over twice the others on a multi-core runner.
- **how:** Hand the whole package list to the test runner in one call so it schedules packages itself (`go test ./...`, `cargo test --workspace`, `pytest -n auto --dist=loadfile`). Where no runner does this, run the packages with `xargs -P "$(nproc)"`, longest first, each with its own log, and exit nonzero if any fails. Keep race flags, special-case tests and one combined coverage profile.
- **estimate:** the serial step's seconds times (1 minus 1 / cores), times about 0.7 for contention. Spotify's luigi core tests went from about 5 minutes to 2 to 4.
- **verify:** compare p50 test job `run_s` over 10 runs before and after. Every package still reports its tests with the same count, and a deliberate failure in one package fails the step.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/parallel-test-packages.md), [Anthropic](https://github.com/oven-sh/bun/pull/39218), [Spotify](https://github.com/spotify/luigi/pull/3398), [Uber](https://github.com/cadence-workflow/cadence/pull/6801)

### build-once-for-shards: Build once and share the output with test shards

- **applies when:** `duplicate_steps` shows the same build or compile command in every shard or matrix leg, and that build step is over 60 s.
- **how:** Add one build job that uploads the output with `actions/upload-artifact@v4`, named by commit, platform and config. Each shard `needs:` it and downloads with `actions/download-artifact@v4` instead of building. Build where it is cheap and test where it must run, as OpenAI builds the ARM64 archive on x64 and tests it on ARM64.
- **estimate:** runner minutes drop by (N minus 1) times the build step's seconds for N shards. Wall time drops by the per-shard build seconds minus the single build job and the artifact transfer (often 10 to 30 s), so it helps the `critical_path` mainly when shard builds are slower than one build. Stripe's full suite went from about 25 to about 14 minutes, together with a CI move.
- **verify:** compare p50 `critical_path` and summed job minutes over 10 runs before and after. Every shard tests an artifact from its own commit, and the test count matches.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/build-once-for-shards.md), [OpenAI](https://github.com/openai/codex/pull/23358), [Stripe](https://github.com/stripe/stripe-react-native/pull/2137)

### matrix-by-supported-runtime: Test supported runtimes concurrently

- **applies when:** a static pattern shows one job testing several runtimes or target frameworks in series, or installing every toolchain in every lane (`tool_install_s` over 30 s for runtimes the lane never uses).
- **how:** Make one matrix job per supported runtime, each installing only its runtime (`actions/setup-node@v5` with `node-version: ${{ matrix.node }}`, `actions/setup-dotnet@v4` with one framework). Set `fail-fast: false` so every leg reports. Move example builds to their own job. Put every leg behind the `ci-ok` aggregate so branch protection needs no new names.
- **estimate:** the old job's `run_s` minus the slowest single runtime's run seconds, plus the `tool_install_s` each lane no longer pays.
- **verify:** compare p50 `critical_path` over 10 runs before and after. Every runtime that was tested is still a matrix leg, each runs the same test count, and a failure on one runtime turns `ci-ok` red.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/matrix-by-supported-runtime.md), [Stripe](https://github.com/stripe/stripe-dotnet/pull/3340)

### overlap-independent-setup: Overlap independent setup with explicit joins

- **applies when:** a job pulls images (`image_pull_s` over 20 s) and then installs dependencies (`install_s` over 20 s) in series, and neither step uses the other's output.
- **how:** Start the pull in the background, install, then wait on the pull by its process ID so its exit status fails the step. Keep gates and publishing in order.
  ```yaml
  - run: |
      docker compose pull & pull=$!
      npm ci
      wait "$pull"
  ```
- **estimate:** the smaller of `image_pull_s` and `install_s`, minus a little for shared CPU, disk and network.
- **verify:** compare p50 setup seconds of that job over 10 runs before and after. Make the pull fail on purpose (a bad image tag) and confirm the step goes red.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/overlap-independent-setup.md), [Stripe](https://github.com/stripe/sync-engine-fork/pull/223)

### parallel-test-framework: Move tests to a parallel-by-default framework

- **applies when:** a test step's `run_s` is over 300 s, the runner shows it running mostly serially (XCTest, unittest, a framework with no parallel mode), and a framework that runs the same tests in parallel exists for the stack.
- **how:** Migrate one package per PR to the parallel framework (Swift Testing for XCTest, pytest with pytest-xdist for unittest). Run the package's tests after every file edit, and count a package as migrated only after its tests pass 10 times in a row, which surfaces tests that depend on order, shared state or timing. Fix each root cause. Leave tests on the old framework where the new one lacks a feature they need.
- **estimate:** the test step's `run_s` times about 0.6, from DoorDash's measured 60% faster unit test step (and about 40% faster builds overall).
- **verify:** compare p50 test step `run_s` over 10 runs before and after for the migrated package. Every old test has a migrated counterpart with the same assertions, the test count matches, and 10 green runs in a row pass.
- **risk:** high
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/parallel-test-framework.md), [DoorDash](https://careersatdoordash.com/blog/doordash-using-cursor-to-accelerate-migration-to-swift-testing/)

### parallel-cleanup: Clean up independent test resources concurrently

- **applies when:** a static pattern shows test setup or teardown looping over independent resources with an `await` per item (index, table or bucket deletion), and that phase takes over 10 s of `run_s`.
- **how:** Start every independent operation at once with `Promise.all` (or `asyncio.gather`), then wait once for all of them. Respect the service's concurrency limit, report every error, and confirm the deletions finished before later tests run.
- **estimate:** the cleanup phase's seconds times (1 minus 1 / K) for K independent resources, bounded by the service's limit.
- **verify:** compare p50 test job `run_s` over 10 runs before and after, with 5 green runs in a row. The same tests run, and a failed deletion still fails the setup.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/parallel-cleanup.md), [Mastra](https://github.com/mastra-ai/mastra/pull/13965)

### weighted-build-and-test: Run memory-heavy build and test on separate runners

- **applies when:** a static pattern shows build and test in series in one job because running them together would exhaust the runner's memory, and that job is the `critical_path`.
- **how:** Run build and test as parallel jobs on separate runners, each sized to the memory it needs on runners the org already has. Measure each step's peak memory first (`/usr/bin/time -v`) and remeasure as the suite grows. If the tests need the build's output, this does not apply; use `build-once-for-shards`.
- **estimate:** the shorter of the build and test steps' seconds, minus the new job's `setup_s`. DoorDash halved its CI time to 11 minutes.
- **verify:** compare p50 `critical_path` over 10 runs before and after. Both jobs run the same commands and test count and sit behind the `ci-ok` aggregate.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/weighted-build-and-test.md), [DoorDash](https://careersatdoordash.com/blog/how-doordash-slashed-web-developer-build-times/)

### parallel-build-targets: Build every target framework in one parallel call

- **applies when:** a static pattern shows a build step calling the build tool once per target framework or configuration in a loop, and that step is over 60 s of `run_s`.
- **how:** Pass every target to one build invocation with parallelism on (MSBuild `-m` with `BuildInParallel`, `cargo build` with several `--target` flags, `make -j"$(nproc)"`). Check memory headroom and that each target's output is identical to before.
- **estimate:** the build step's seconds times (1 minus 1 / T) for T targets, capped by the runner's cores.
- **verify:** compare p50 build step seconds over 10 runs before and after, and diff the build outputs between the two runs.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/parallel-build-targets.md), [OpenAI](https://github.com/openai/openai-dotnet/pull/1009)

### parallel-packaging: Compress release artifacts in parallel

- **applies when:** a static pattern shows a release step compressing or archiving independent files in a loop, and that step is over 60 s of `run_s`.
- **how:** Run the archives with `xargs -P 2` (or the core count after measuring), which exits nonzero when any worker fails. Measure the worker count, since workers share CPU and disk.
  ```yaml
  - run: ls dist/*.exe | xargs -P 2 -I{} 7z a {}.zip {}
  ```
- **estimate:** the packaging step's seconds times about 0.4, from OpenAI's 121 s to 73 s with two workers.
- **verify:** compare the step's seconds over 3 release runs before and after. The same archives come out, and a corrupt input fails the step.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/parallel-packaging.md), [OpenAI](https://github.com/openai/codex/pull/27855)

### one-machine-build: Build on one machine when the long pole leaves it idle

- **applies when:** two build jobs run on separate runners, one is the `critical_path` and leaves its runner mostly idle (CPU under 50% for most of `run_s`), and the other's output is downloaded by a later step.
- **how:** Move the shorter compile into the long job and run it in the background alongside the long compile, then link there. Drop the separate job and its artifact download. Do this only when the long job's existing runner has the cores and memory both compiles need. If it needs a bigger machine that costs more, report it under `faster-runners` instead.
- **estimate:** the removed job's `wait_s` and `setup_s` plus the artifact download, minus any slowdown of the long compile. Bun cut its build from 26 to 13 agents and about 93 to 69 agent-minutes, with lanes 23 to 43 s faster.
- **verify:** compare p50 `critical_path` and summed job minutes over 10 runs before and after, and confirm the linked output matches.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/one-machine-build.md), [Anthropic](https://github.com/oven-sh/bun/pull/37733)

### package-on-available-runner: Package other architectures on the runner that is free

- **applies when:** a packaging job for another architecture runs no target code and its `wait_s` is over 30 s on a scarce runner label.
- **how:** Move jobs that only download, sign, archive and compress to the common runner label the workflow already uses. Keep any step that runs the target's binaries on its native runner.
- **estimate:** that job's `wait_s` minus the common label's `wait_s`. OpenAI's ARM64 packaging waited 76 s for its runner and held the release 1m43s after x64 finished.
- **verify:** compare the release workflow's wall time over 3 runs before and after, and diff the packaged files.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/package-on-available-runner.md), [OpenAI](https://github.com/openai/codex/pull/28001)

### size-agents-to-graph-width: Size the job count to the widest layer of the build graph

- **applies when:** a static pattern shows a fixed matrix of N parallel build jobs on every commit, and many of them finish with a `run_s` under their `setup_s` because they had nothing to do.
- **how:** Add a plan job that reads the monorepo tool's graph for the change (`turbo run build --dry=json`, `nx show projects --affected`, `rush list`), takes the widest layer as the job count, and outputs it as a JSON list. Feed it to the matrix with `fromJSON(needs.plan.outputs.shards)`. Keep long single tasks in mind, since they still set the wall time.
- **estimate:** runner minutes drop by (N minus graph width) times `setup_s`; wall time drops only by any `wait_s` those idle jobs caused. DoorDash went from 220 agent-minutes per run to 30, with other runtime changes.
- **verify:** compare summed job minutes and p50 `critical_path` over 10 runs before and after. Every task the graph lists still runs, and the default branch still builds everything.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/size-agents-to-graph-width.md), [DoorDash](https://careersatdoordash.com/blog/how-doordash-slashed-web-developer-build-times/)

### uncluster-no-op-projects: Let shared packages without a build step stay cacheable

- **applies when:** `shard_skew` is over 1.5 across distributed build jobs, and the slow job holds a cluster of projects that depend on a package with no build output (shared configs, lint profiles).
- **how:** In the monorepo tool, mark packages with no build or test script as no-op or cacheable, so their dependents spread across every job (Rush did this upstream; in Turbo or Nx, give such packages no build task, or `outputs: []`). A package that writes output still declares its outputs.
- **estimate:** the slowest build job's `run_s` minus the mean build job `run_s`. DoorDash cut its cobuild agents from ten to five and used all five.
- **verify:** compare `shard_skew` and p50 `critical_path` over 10 runs before and after. Every project still builds and tests once per run.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/uncluster-no-op-projects.md), [DoorDash](https://careersatdoordash.com/blog/how-doordash-slashed-web-developer-build-times/)

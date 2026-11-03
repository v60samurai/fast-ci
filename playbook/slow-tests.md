# Slow tests and checks

These entries apply when the test, lint or typecheck step itself is most of a job's `run_s`, or when flaky failures send jobs back for reruns. Most of the time in a slow suite goes to tool startup, module loading, fixed waits and real services, not to the assertions, so look there before cutting any test.

### native-lint-tools: Use a faster native linter without losing rules

- **applies when:** a lint step runs ESLint, or flake8, isort, pylint or black, for over 20 s of `run_s` in a job on the `critical_path`, and the repo does not already run Oxlint, Biome or Ruff for that code.
- **how:** For JS and TS, replace ESLint with Oxlint, keeping ESLint only for the rules Oxlint cannot cover yet (custom local rules, plugins Oxlint lacks, type-aware rules). If the repo already uses Biome, move the rules there instead. For Python, replace flake8, isort and the formatter with Ruff (`ruff check` and `ruff format`) configured in `pyproject.toml`. Write a ledger first: every rule enforced today maps to a rule in the new tool or stays in the old one. Keep every rule enforced today, and turn on every other rule the code passes for free (for Oxlint, every category in `.oxlintrc.json`). Fix the new errors it finds, landing the automated fixes in a commit separate from the config change. Run `eslint-plugin-oxlint` in the remaining ESLint config so the two tools do not check the same rule twice. Owen took lint from 2 min to 5 s.

  ```yaml
  - uses: actions/checkout@v5
  - uses: actions/setup-node@v5
    with: { node-version-file: .nvmrc }
  - run: npm ci
  - run: npx oxlint --deny-warnings
  # only if rules are left that Oxlint lacks
  - run: npx eslint . --max-warnings=0
  ```
- **estimate:** lint step seconds times about 0.95 (Owen's 2 min to 5 s) when ESLint goes away entirely. When an ESLint pass stays for unsupported rules, subtract that pass's measured time.
- **verify:** compare the lint step over 5 runs before and after. Run old and new linters on the same commit and diff their findings: every rule in the ledger reports the same files. Commit a deliberate violation of three kept rules on the PR branch and confirm the lint job goes red, then drop that commit.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/native-lint-tools.md), [Linear](https://linear.app/now/ci-bottleneck-reworked#lint-without-the-type-checker), [Spotify](https://github.com/spotify/luigi/pull/3395), [Owen Gretzinger](https://x.com/owengretzinger/status/2116291924219060319)

### native-type-checking: Run the type check on a native compiler

- **applies when:** a step runs `tsc --noEmit` (directly or through a `package.json` script) for over 20 s of `run_s` in a job on the `critical_path`, and the repo is not already on TypeScript 7. A `tsc` that emits build output does not qualify.
- **how:** Benchmark `tsc` against TypeScript 7 (`typescript@^7`, or `tsgo` from `@typescript/native-preview` where 7 has not shipped for the repo) and, in a Bun project, `bun check`, on the same commit and runner class. Point the `typecheck` script at the fastest one whose errors match `tsc`'s on this repo. Anything that calls the compiler API (typescript-eslint type-aware rules, ts-loader) keeps a side-by-side TypeScript 6 alias. TypeScript 7's new defaults can surface new errors, so list them in the PR and fix them; never narrow the check to make it fit. Note any faster local-only option in the report. Switch again when a faster checker ships. Owen went from `tsc` to TypeScript 7 to `bun check`, 70 s to under 5 s.

  ```yaml
  - run: npm i -D @typescript/native-preview
  - run: npx tsgo --noEmit -p tsconfig.json
  ```
- **estimate:** typecheck step seconds times 0.73 (Linear's weekly median drop), up to 0.93 (Owen's 70 s to under 5 s).
- **verify:** compare the typecheck step over 5 runs before and after. Run old and new checkers on the same commit and diff their error output, which must match. Add a deliberate type error on the PR branch and confirm the job goes red, then remove it. Keep the old check beside the new one until a sampled run matches.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/native-type-checking.md), [Linear](https://linear.app/now/ci-bottleneck-reworked#upgraded-infrastructure-and-tooling), [Owen Gretzinger](https://x.com/owengretzinger/status/2116291924219060319)

### share-module-state: Let test files share a worker

- **applies when:** the test step is over half of `run_s` on the `critical_path`, the runner isolates every file (Vitest default `isolate: true`, Jest with fresh module registries, pytest-xdist workers restarted per file), and Vitest's summary shows `transform` plus `collect` plus `setup` over half of its `Duration`.
- **how:** Vitest gives every test file a fresh worker by default, so every file reloads the app. Set `test.isolate: false` (Jest: turn `isolateModules` off; pytest: reuse xdist workers). Add a `setupFiles` hook that resets shared state after every file: database rows, mocks, globals, timers and module singletons. Files that still fail, and files that use fake timers, go in a second Vitest project that keeps `isolate: true`, the opt-in shape Linear uses. Write in `AGENTS.md` what a test must clean up, so new tests follow it. Keep the change only if the suite is green 5 runs in a row, with the run count and reason in a comment next to the setting. Owen took 100 s per shard to 35 s.
- **estimate:** test step seconds times 0.65 (Owen's 100 s to 35 s per shard), on each shard on the `critical_path`. Linear called it its largest single win, about 17% of monthly CI cost.
- **verify:** compare the test step over 5 runs before and after, on every shard. The test count reported per shard stays the same. Run the suite 5 times in a row on the PR and in random file order (`--sequence.shuffle`) at least once. Write one test that leaves a global set and confirm the reset hook clears it before the next file.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/share-module-state.md), [Linear](https://linear.app/now/ci-bottleneck-reworked#share-module-state-only-with-strict-isolation-rules), [Owen Gretzinger](https://x.com/owengretzinger/status/2116291924219060319)

### flaky-tests: Fix flaky tests from CI history

- **applies when:** `rerun_rate` is over 0 for a required job.
- **how:** List every job that failed and then passed on the same commit (`gh run view <id> --attempt 1 --json jobs`), and pull the failing test names from the first attempt's log. Reproduce each one by running it many times (`vitest --repeat 50`, `pytest --count 50` with pytest-repeat, `go test -count 50 -race`). Fix the cause in the test: wait for the event it depends on, sort unordered output, clean up its own resources, or remove a timing dependency. Keep every assertion and the behavior under test. Do not add retries, longer timeouts or skips. The entries below cover the common causes.
- **estimate:** `rerun_rate` times (the flaky job's `run_s` plus its `wait_s`), per run, plus the agent's own wait on the rerun.
- **verify:** the fixed test passes 50 repeated runs locally and on CI. Compare `rerun_rate` over the next 50 runs with the baseline. The test count stays the same, and a deliberate break of the behavior under test still fails it.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/flaky-tests.md), [OpenAI](https://developers.openai.com/blog/maintaining-software-with-the-gpt-6-family#other-ideas-to-try)

### poll-readiness: Wait for observable readiness instead of sleeping

- **applies when:** workflow steps or tests contain fixed sleeps of 2 s or more before an asynchronous check (`sleep`, `time.sleep`, `setTimeout`, `await sleep(`), or a service health check probes something other than what the tests use (a Unix socket on `localhost` while clients use TCP, an open port before migrations finish). Static pattern.
- **how:** Replace each sleep with a helper that polls the condition the next step needs, returns as soon as it holds, and throws with useful output when a deadline passes. Probe the real operation: `SELECT 1` over TCP on `127.0.0.1`, a search service ping, or the indexed document's content and version, since a matching count alone misses same-size updates. Use `docker compose up --wait` with query health checks, or service health options in the workflow. Keep any existing retry loop until the new probe is proven. Keep tests that check a timeout on purpose unchanged.

  ```yaml
  services:
    postgres:
      image: postgres:16
      ports: ["5432:5432"]
      env: { POSTGRES_PASSWORD: postgres }
      options: >-
        --health-cmd "pg_isready -h 127.0.0.1 -U postgres"
        --health-interval 2s --health-retries 30
  ```
- **estimate:** the sum of fixed sleeps per run, minus the measured time until each condition holds. Read sleep totals from the test code and step logs.
- **verify:** compare the affected job over 5 runs before and after. The same tests run and pass. Stop the service in one run and confirm the probe fails at its deadline with logs, not with a hang. Watch `rerun_rate` for new startup races, since faster setup can expose ones the sleep hid (Mastra needed a follow-up PR for this).
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/poll-readiness.md), [Mastra](https://github.com/mastra-ai/mastra/pull/13808), [Mastra](https://github.com/mastra-ai/mastra/pull/14520), [Mastra](https://github.com/mastra-ai/mastra/pull/15895), [Stripe](https://github.com/stripe/sync-engine-fork/pull/124), [Uber](https://github.com/uber/submitqueue/pull/64)

### shorten-proven-test-waits: Shorten deliberate test waits

- **applies when:** a test or a CI-run example sleeps for a fixed time to trigger a timeout or a slow path, or a service with no readiness signal is checked after repeated conservative waits, and those sleeps add up to over 10 s of `run_s`. Static pattern.
- **how:** Where a sleep exists only to trigger a timeout, shrink the sleep and the timeout together so the timeout branch still runs and is asserted. Anthropic's example slept 60 s to trigger a 10 s timeout and now sleeps 5 s against a 3 s timeout. Where a service has no readiness predicate, prefer a real completion signal (see poll-readiness). If there is none, lower the wait only after stressing the test on slow runners. Mastra's Chroma tests cut 80 waits of 2 s to 200 ms, from 160 s of sleeping to about 16 s.
- **estimate:** (old wait minus new wait) times the number of waits per run. Anthropic estimated 50 s or more off the examples job.
- **verify:** compare the job over 5 runs before and after. The same tests run, and the timeout path still runs and is asserted (break the timeout handling on purpose and confirm the test fails). Run the shortened tests 5 times in a row; if one fails, raise the wait before touching any assertion.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/shorten-proven-test-waits.md), [Anthropic](https://github.com/anthropics/claude-agent-sdk-python/pull/760), [Mastra](https://github.com/mastra-ai/mastra/pull/13866)

### mock-external-dependencies: Keep unit tests independent of slow services

- **applies when:** a unit or component test job on the `critical_path` declares database or service containers (`services:` or `docker compose up` in the job, static) that its tests use only for storage, or its tests make live network calls to a service outside the code under test.
- **how:** Give the unit tests a controlled substitute: add the missing mock for the live call, use dummy models or fakes for remote APIs, or an in-process store such as SQLite for tests that only need persistence. Move engine-specific tests into an integration job that runs the real dependency, and keep every engine-specific assertion there. OpenAI added one missing mock to a 63-test resolver suite and kept all 63 tests. Uber removed four database servers from its unit-test container.
- **estimate:** the mocked suite's seconds times 0.95 (OpenAI's 592.6 s to 29.8 s), plus the service containers' start time from the job's setup steps.
- **verify:** compare the job over 5 runs before and after. The unit and integration jobs together discover the same tests as before (compare collected test IDs) and the combined coverage does not drop. A deliberate bug in the code under test still fails the unit test.
- **risk:** medium
- **mode:** report-only (weakens-check)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/mock-external-dependencies.md), [OpenAI](https://developers.openai.com/blog/maintaining-software-with-the-gpt-6-family#other-ideas-to-try), [Uber](https://github.com/cadence-workflow/cadence/pull/6800)

### reduce-test-process-overhead: Start fewer test processes

- **applies when:** the test step on the `critical_path` starts a separate process, interpreter or test binary per file or target (a loop over files, one `cargo test` binary per file under `tests/`, many CLI subprocess cases, separate per-target `xcodebuild test` calls). Static pattern.
- **how:** Batch compatible work into fewer processes. Run reliable files as one parallel invocation per shard (`bun test --parallel`), and keep a denylist of files that showed batch sensitivity, plus memory-measuring tests, on their own path. In Rust, move integration tests into one suite so cargo builds and starts one binary. In Python, run policy cases in-process with fresh globals, and keep a few real subprocess tests for CLI parity. On iOS, build related test targets in one scheme. Keep targets whose environment or isolation differs in their own lane. The batch reports every file it runs, and any error turns the job red.
- **estimate:** test step seconds times 0.42 (Anthropic's Bun ASAN lane, 8.5 to 4.9 min) to 0.62 (OpenAI Python, 7m00s to 2m41s).
- **verify:** compare the test step over 5 runs before and after. The number of tests reported is the same as before. Run the batched suite 5 times in a row, and compare pass and fail results as well as time.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/reduce-test-process-overhead.md), [Anthropic](https://github.com/oven-sh/bun/pull/36175), [OpenAI](https://github.com/openai/openai-python/pull/3830), [Stripe](https://github.com/stripe/stripe-ios/pull/7332)

### lint-without-types: Keep the lint rule, drop its type-graph dependency

- **applies when:** the ESLint config enables typed linting (`parserOptions.project` or `projectService`, static) and the lint step is over 20 s of `run_s` on the `critical_path`.
- **how:** List every rule that needs type information. For each custom rule where a syntax-tree check is provably equivalent, rewrite it to use the syntax tree only. Keep each rule that truly needs types in a separate required pass. Once no rule in the main pass needs types, remove `parserOptions.project` so ESLint stops building the TypeScript program. Do this before native-lint-tools, since syntax-only rules port to Oxlint easily.
- **estimate:** lint step seconds times 0.55 (Linear's full-repository lint drop), or 0.68 for a package dominated by typed rules (Linear's API package).
- **verify:** compare the lint step over 5 runs before and after. Keep a rule-by-rule ledger in the PR: each rewritten rule reports the same findings on the same commit. Add a deliberate violation for each rewritten rule and confirm the lint goes red.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/lint-without-types.md), [Linear](https://linear.app/now/ci-bottleneck-reworked#lint-without-the-type-checker)

### coordinate-test-setup: Build the test database once for all workers

- **applies when:** parallel test workers (pytest-xdist, Vitest or Jest workers) each run the same migrations or fixture build at startup (static: a per-worker fixture that applies migrations), and the test step is on the `critical_path`.
- **how:** Have one worker build the schema while the others wait on a file lock (for pytest-xdist, `filelock` under the shared temp dir) or move it to a single `globalSetup`. Each worker then clones the template database (`CREATE DATABASE w1 TEMPLATE test_template`) or uses its own schema. Ramp's per-worker migrations ran Postgres out of working memory at higher worker counts; one shared build let it run more workers.
- **estimate:** per-worker setup seconds minus one setup's seconds, on the slowest worker, plus any time from raising workers afterwards. The schema build itself stays as a floor on the job.
- **verify:** compare the test step over 5 runs before and after. The same tests run and pass. Delete the template between runs and confirm the next run rebuilds it, and that a migration change is picked up. Run 5 times in a row at the new worker count.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/coordinate-test-setup.md), [Ramp](https://builders.ramp.com/post/faster-python-tests)

### schema-snapshots: Load a schema snapshot when the schema did not change

- **applies when:** test setup replays the full migration history in each container or shard (static), and that setup is over 10 s per container in `setup_s` or `run_s`.
- **how:** Generate a schema dump and seed bootstrap file at the migration head (`pg_dump --schema-only`, or the framework's schema dump) and commit it or build it in CI. When a PR leaves migrations unchanged, load the snapshot. When migrations change, and on every default-branch run, replay the full history as today. Add a check that fails when the snapshot does not match the migration head.
- **estimate:** per-container setup seconds times (1 minus 1.5/12), about 0.88 (Linear's 12 s to 1 to 2 s), on each container on the `critical_path`, for PRs that do not touch migrations.
- **verify:** compare setup time over 5 runs before and after. The same tests run. Change a migration without regenerating the snapshot and confirm the staleness check goes red. Confirm the full migration replay still runs on the default branch and on PRs that touch migrations.
- **risk:** medium
- **mode:** report-only (weakens-check)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/schema-snapshots.md), [Linear](https://linear.app/now/ci-bottleneck-reworked#avoid-replaying-unchanged-setup)

### synchronize-assertions: Wait for the state change before asserting

- **applies when:** `rerun_rate` is over 0 and a flaky test reads asynchronous state (lag, counters, queue depth, UI state) right after triggering the operation that updates it.
- **how:** Wait for the specific signal the operation emits when it finishes (a callback, channel, event or poll tick), with a bounded timeout, then assert. Confirm the signal comes from the operation under test, not a side effect. Keep every assertion.
- **estimate:** as flaky-tests: `rerun_rate` times (the job's `run_s` plus `wait_s`) for this test's share of reruns.
- **verify:** run the test 50 times locally and on CI, all passing (Uber's check). The assertions are unchanged, and breaking the operation still fails the test.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/synchronize-assertions.md), [Uber](https://github.com/uber/submitqueue/pull/274)

### normalize-unordered-results: Sort unordered results before comparing

- **applies when:** `rerun_rate` is over 0 and a flaky test's failure shows the same items in a different order (expected `[A B]`, got `[B A]`).
- **how:** Decide whether order is part of the output contract. If it is not, sort a copy of the values before formatting or comparing, in the producer when a stable public output helps, or in the test otherwise. Sort a copy where callers share the slice. Keep membership and error-field assertions.
- **estimate:** as flaky-tests: `rerun_rate` times (the job's `run_s` plus `wait_s`) for this test's share of reruns.
- **verify:** run the test 50 times, all passing. A missing or extra item still fails it. Callers of the producer see no change beyond the order.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/normalize-unordered-results.md), [Uber](https://github.com/cadence-workflow/cadence/pull/6831)

### check-cleanup-at-test-end: Check for leaks after the test cleans up

- **applies when:** `rerun_rate` is over 0 and a flaky test runs a leak or cleanup check (`goleak.VerifyNone`, open-handle checks) before the test body or its cleanup has run.
- **how:** Move the check to the end of the test, after the body and its cleanup, for example as the first `defer` in Go so it runs last. Then it inspects this test's own goroutines or handles, not ones another test left behind. Wait for asynchronous shutdown before the check.
- **estimate:** as flaky-tests: `rerun_rate` times (the job's `run_s` plus `wait_s`) for this test's share of reruns. Uber's detector had fired 5 times in four months.
- **verify:** run the test 10 times with the race detector (`go test -race -count 10`), all passing. Add an intentional leak and confirm the check still fails.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/check-cleanup-at-test-end.md), [Uber](https://github.com/cadence-workflow/cadence/pull/7969)

### flakiness-gate-before-blocking: Prove a new test is stable before it blocks merges

- **applies when:** `rerun_rate` is over 0 in a suite that blocks merges, and PRs add new end-to-end tests most weeks.
- **how:** Add a workflow that runs each new or changed end-to-end test many times (for example 20) in a separate job. A test joins the blocking suite only if its failure rate stays under a threshold chosen from the suite's own history. Until then it runs, reports, and does not block. Shopify used a strict test API with an assertion on every step and this gate to take its mobile suite from 50% to 98% stability.
- **estimate:** the share of `rerun_rate` caused by tests under 30 days old, times (the job's `run_s` plus `wait_s`). The gate costs about runs times the test's time in runner minutes, off the `critical_path`.
- **verify:** compare `rerun_rate` over 50 runs before and after. Confirm a deliberately flaky new test is held back by the gate and a stable one is promoted.
- **risk:** medium
- **mode:** report-only (weakens-check)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/flakiness-gate-before-blocking.md), [Shopify](https://shopify.engineering/mobile-e2e-testing)

### trace-screenshots: Record full traces only when someone reads them

- **applies when:** the end-to-end config records traces, video or screenshots on every test (`trace: 'on'`, `video: 'on'` or `screenshot: 'on'` in `playwright.config`, static), or the workflow uploads them on passing runs.
- **how:** Record only what a failure needs: in Playwright, `trace: 'retain-on-failure'`, `screenshot: 'only-on-failure'`, `video: 'retain-on-failure'`. Keep full traces for runs someone reads as evidence (a manual input or a label). Upload the artifact with `if: failure()`. Teardown can run before the runner records an in-flight error, so check that assertion, timeout and teardown errors each still save a usable trace.
- **estimate:** the end-to-end step's seconds with tracing on minus one run with it off, plus the upload step's seconds on passing runs.
- **verify:** compare the end-to-end job over 5 runs before and after. The same tests run. Make one test fail by assertion, one by timeout and one in teardown, and confirm each leaves a trace artifact.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/trace-screenshots.md), [DoorDash](https://github.com/doordash-oss/agentic-orchestrator/pull/139)

### agent-import-cycles: Break import cycles and load the app lazily

- **applies when:** tests or tools start the application, and its import takes over 2 s per process (`python -X importtime`, or Vitest's `collect` time over half its `Duration`), on a job on the `critical_path`.
- **how:** Find the cycles (`madge --circular` for JS and TS, `pylint --disable=all --enable=cyclic-import` for Python) and break them. Move heavy imports that one command or test needs into the function that uses them, or into a dynamic `import()`. A lazy import moves a failure from startup to first use, so add a test that imports every module. Ramp gave this work to an agent and merged much of what it produced.
- **estimate:** app import seconds saved times the number of processes or workers that import it per run, divided by the workers running in parallel.
- **verify:** compare the test step over 5 runs before and after, and the import time measured the same way. The same tests run and pass. The import-every-module test fails when one module has a broken import.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/agent-import-cycles.md), [Ramp](https://claude.com/customers/ramp-boris-office-hours)

### finish-fixtures-before-timeout: Complete the fixture before its timeout fires

- **applies when:** the slowest tests' durations cluster at a configured timeout (many tests taking close to the same 10 s, for example) on the happy path, in a job on the `critical_path`.
- **how:** Find the operation the test waits on and have the fixture complete it, so the test advances on that event and not on the timer that rescues it. Update expected event histories when completing adds events. Confirm the test is about the completion path, and keep dedicated timeout tests as they are. Uber's integration tests each waited 10 s for an activity to time out.
- **estimate:** the timeout's seconds times the affected tests, divided by parallel workers.
- **verify:** compare the job over 5 runs before and after. The same tests run, and the dedicated timeout tests still run and pass. Breaking the completion path fails the changed tests.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/finish-fixtures-before-timeout.md), [Uber](https://github.com/cadence-workflow/cadence/pull/8290)

### compile-test-sources-once: Transpile test sources once per run

- **applies when:** tests start many Node subprocesses that each load a TypeScript transpiler (`ts-node`, `tsx`, a register hook) on the same sources. Static pattern.
- **how:** In a Vitest `globalSetup`, compile the sources the subprocesses load once (with `tsc` or esbuild) into a directory under the run's temp dir, and point the subprocesses at it. Set `NODE_COMPILE_CACHE` on Node 22 or later. The snapshot belongs to one run, so never cache it across runs.
- **estimate:** per-subprocess transpile seconds times subprocesses per run, divided by parallel workers. OpenAI's Node SDK job went from 5m37s to 3m47s with this and smaller changes.
- **verify:** compare the test step over 5 runs before and after. The same tests run. Change a source file and confirm the subprocess tests see the change on the next run.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/compile-test-sources-once.md), [OpenAI](https://github.com/openai/openai-node/pull/2713)

### release-query-results: Release query results before they become a timeout

- **applies when:** an integration step spends most of its time idle after its queries complete, or its duration sits near a client or connection timeout, on a job on the `critical_path`.
- **how:** Profile connection lifetimes, then read or close every query result so the connection goes back to the pool (consume the ClickHouse result, close cursors and response streams). Keep the query behavior and its result checks.
- **estimate:** the job's seconds times 0.44 (Mastra's 530 s to 298 s median over five same-commit trials), or the idle time the profile shows.
- **verify:** compare the job over 5 runs before and after on the same commit. The same tests run and pass, and the result checks are unchanged.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/release-query-results.md), [Mastra](https://github.com/mastra-ai/mastra/pull/25613)

### precompile-test-imports: Precompile imports for no-bytecode test subprocesses

- **applies when:** Python tests launch many isolated interpreters with bytecode writes off (`-B` or `PYTHONDONTWRITEBYTECODE=1`), so each one recompiles the same modules. Static pattern.
- **how:** In each shard's disposable copy of the package, run `python -m compileall -q --invalidation-mode checked-hash <copy>` before the tests. Leave the subprocesses' no-write flags on, and keep the generated bytecode out of release artifacts.
- **estimate:** the affected tests' seconds times 0.15 (OpenAI's 451.7 s to 381.7 s, plus 1.1 s to prepare).
- **verify:** compare the test step over 5 runs before and after. The same tests run, the no-write tests still pass, and the release artifact has no `.pyc` files.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/precompile-test-imports.md), [OpenAI](https://github.com/openai/codex-security/pull/2036)

### avoid-incidental-test-dns: Use a loopback address for local mock servers

- **applies when:** tests on Windows runners (`runs-on: windows-*`, static) connect to a local mock server by `localhost`, and that job's `run_s` is longer than the same tests on Linux.
- **how:** Point the mock server and its clients at `127.0.0.1` on the slow platform, bound to the same address. Keep dedicated hostname, IPv6 and DNS tests where the product needs them.
- **estimate:** the Windows test step's seconds minus the Linux test step's seconds for the same tests, as an upper bound. Measure one run each way.
- **verify:** compare the Windows job over 5 runs before and after. The same tests run, and the hostname and IPv6 tests still run.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/avoid-incidental-test-dns.md), [Stripe](https://github.com/stripe/stripe-python/pull/1849)

### suite-under-leak-sanitizer: Run the suite under a leak sanitizer

- **applies when:** a repo with native code (C, C++, Rust or Zig, or a language with a leak checker) runs tests only in regular builds, and `rerun_rate` or `infra_fail_rate` is over 0 from crashes, out-of-memory kills or timeouts in native tests.
- **how:** Add a separate lane that runs the full suite with LeakSanitizer or AddressSanitizer on, and a suppression file in which every entry has a written reason. Size its per-test timeout from one measured run, and make a new leak fail the lane. Run it in parallel with the regular lanes so it stays off the `critical_path`. Bun fixed every leak its sanitizer lane reported.
- **estimate:** this adds runner time. It saves time only through fewer leak-driven failures: the share of `rerun_rate` from those crashes times (the job's `run_s` plus `wait_s`).
- **verify:** confirm `pr_p50` does not grow, since the lane runs in parallel. Add a deliberate leak and confirm the lane goes red. Every suppression has a reason.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/suite-under-leak-sanitizer.md), [Anthropic](https://github.com/oven-sh/bun/pull/30875)

### batch-historical-restores: Restore a set of files in one Git command

- **applies when:** a CI script restores files from another revision with one `git checkout <rev> -- <file>` per file in a loop. Static pattern.
- **how:** List the files once and check them out in one call, with literal paths, so files missing from the baseline stay untouched: `git ls-tree -r -z --name-only <rev> -- <dir> | git --literal-pathspecs checkout <rev> --pathspec-from-file=- --pathspec-file-nul`.
- **estimate:** per-call seconds times the files restored, minus one call. OpenAI went from 82 checkouts to one, and with compile-historical-api-probes from 198.66 s to 88.63 s locally.
- **verify:** compare the step over 5 runs before and after. The restored file list is identical (diff `git status` output from both versions), including files absent from the baseline.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/batch-historical-restores.md), [OpenAI](https://github.com/openai/openai-go/pull/1152)

### compile-historical-api-probes: Compile old API probes instead of linting them

- **applies when:** a compatibility check restores old tests and runs a full lint or test pass on them, when its contract is only that the old code still compiles, and that check's `run_s` is over 60 s. Static pattern.
- **how:** Compile the restored tests and stop there (`go test -c -vet=off -o /dev/null ./...`). Current-tree lint and tests stay required in the normal CI workflow.
- **estimate:** the check's lint or test seconds minus compile seconds. Together with batch-historical-restores, OpenAI went from 198.66 s to 88.63 s locally.
- **verify:** compare the step over 5 runs before and after. Remove an exported API on the PR branch and confirm the check still goes red. Confirm lint and tests still run on the current tree.
- **risk:** low
- **mode:** report-only (weakens-check)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/compile-historical-api-probes.md), [OpenAI](https://github.com/openai/openai-go/pull/1152)

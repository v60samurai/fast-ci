# Test selection

Every PR runs every test and job, whatever it touched. These entries run only what a change can reach and keep the full run on the default branch. The last three move checks after merge or drop gates, so they stay with the user.

### select-affected-tests: Run only the tests a change can affect

- **applies when:** the test job is the `critical_path` job and over 40% of `pr_p50`, and it runs the full suite on every PR (static: no affected command, `--changed`, `--changedSince` or path selector in the test step).
- **how:** Use the monorepo tool's affected command (`nx affected -t test`, `turbo run test --filter=...[origin/main]`, `pnpm --filter "...[origin/main]" test`) or a path-based selector (Vitest `--changed`, Jest `--changedSince`, pytest-testmon), and run the full suite on the default branch every night. The fast-ci Baseline runs Vitest's affected tests on PRs behind a `ci-ok` gate. A change to any of these runs every test, because the import graph cannot see them: lockfiles, `package.json`, `pnpm-workspace.yaml`, `.npmrc`, `.node-version`, `.nvmrc`, `tsconfig*.json`, Vite or Vitest config, `.env*`, `.github/`, `patches/` and the shared test setup. Add any file the tests read without importing it (fixtures, demo data, codegen sources). Fall back to the full suite on a selector error, an empty selection for a code change, or a missing base commit, and check out with `fetch-depth: 0`. Always run tests that find their files at runtime and tests that were red last time (Stripe). For dbt, build `--select state:modified+1` against the manifest saved after every production run, and keep a full build on a schedule (Ramp). Stripe runs about 5% of its Ruby suite per build on average, median 0.5%, with under 10% of the compute.
  ```yaml
  - id: scope
    env:
      BASE: ${{ github.base_ref }}
    run: | # extend the regex to the whole full-run list above
      if [ -z "$BASE" ] || git diff --name-only "origin/$BASE"...HEAD | grep -qE '(^|/)(pnpm-lock\.yaml|package\.json|\.npmrc|tsconfig[^/]*\.json)$|^(\.github|patches)/'
      then echo "filter=" >> "$GITHUB_OUTPUT"
      else echo "filter=--filter=...[origin/$BASE]" >> "$GITHUB_OUTPUT"; fi
  - run: pnpm turbo run test ${{ steps.scope.outputs.filter }}
  ```
- **estimate:** The test job's `run_s` times (1 minus the selected share), per PR run. Measure the selected share by replaying the last 20 merged PRs' diffs through the selector. Without that, use Stripe iOS's measured drop, framework tests from about 22 minutes to about 12 to 14, a selected share of about 0.6.
- **verify:** On purpose, make a change the selector would miss (edit a fixture or a file on the full-run list without touching an import) and confirm the run fails or runs everything. Then confirm a change to one leaf module runs fewer tests. The `ci-ok` gate fails when code files changed and no test ran. A skipped required job reports green only when the change truly needed nothing it skipped. The default branch and nightly runs still run the full suite with the same test count as before. Compare the test job's time and `pr_p50` over 20 PR runs.
- **risk:** high
- **mode:** report-only (weakens-check)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/select-affected-tests.md), [Anthropic](https://claude.com/resources/articles/agentic-coding-is-straining-ci-heres-how-we-scaled-test-impact-analysis-at-anthropic), [Mastra](https://github.com/mastra-ai/mastra/pull/18819), [Ramp](https://builders.ramp.com/post/cost-efficient-snowflake-ci), [Stripe](https://stripe.dev/blog/selective-test-execution-at-stripe-fast-ci-for-a-50m-line-ruby-monorepo), [Stripe](https://github.com/stripe/stripe-ios/pull/7332), [Owen Gretzinger](https://x.com/owengretzinger/status/2116291924219060319)

### skip-unaffected-jobs: Skip jobs whose inputs have not changed

- **applies when:** `irrelevant_runs` over 0 (docs-only PRs running the full suite), or an expensive job or matrix that verifies one subsystem (native, platform, end-to-end, packaging) runs on every PR.
- **how:** Use the monorepo tool's affected command (`nx affected`, `turbo --filter=...[origin/main]`, `pnpm --filter ...[origin/main]`) or a path-based selector, and run the full suite on the default branch every night. Add a `changes` job that diffs against the base and sets outputs (dorny/paths-filter@v3 or a `git diff` step), and put a job-level `if:` on each expensive job, so skipped work never takes a runner. Filter at the job level, never with a workflow-level `paths:` on a workflow that holds required checks, because a workflow that never starts leaves its required checks pending (Shopify CLI restored its tests for this reason). Report required names through the `ci-ok` aggregate or an always-present job that passes with no work. The path list covers every input: source, shared packages, lockfiles, schemas, generators, build config, the workflow file and the filter file itself. Run everything when the base commit is missing, on manual dispatch, on the default branch, and for added, deleted, renamed or mixed changes the filter cannot place (DoorDash, OpenAI). Seven OpenAI PRs that only edited pytest modules used 17h29m53s of runner time (139 jobs) on jobs this route skips.
  ```yaml
      - id: f
        uses: dorny/paths-filter@v3
        with:
          filters: |
            native: ['native/**', 'packages/shared/**', 'pnpm-lock.yaml', '.github/**']
    # the changes job also sets outputs.native: ${{ steps.f.outputs.native }}
    native-tests:
      needs: changes
      if: needs.changes.outputs.native == 'true' || github.event_name != 'pull_request'
  ```
- **estimate:** For each skippable job, the share of PRs that do not touch its inputs times its `setup_s` plus `run_s`, summed per PR. Get the share by replaying the last 50 merged PRs' file lists through the filter. `pr_p50` drops when a skipped job was on the `critical_path`. For docs-only PRs, `irrelevant_runs` times the full run's runner time.
- **verify:** On purpose, make a change the filter would miss (a shared package, a lockfile, the workflow file) and confirm the job runs and a deliberate failure in it turns the run red. A docs-only PR reports every required check and starts no expensive job. A skipped required job reports green only when the change truly needed nothing it skipped. The default branch runs every job. Compare runner minutes and `pr_p50` over 20 PR runs.
- **risk:** high
- **mode:** report-only (weakens-check)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/skip-unaffected-jobs.md), [Anthropic](https://claude.com/resources/articles/agentic-coding-is-straining-ci-heres-how-we-scaled-test-impact-analysis-at-anthropic), [DoorDash](https://github.com/doordash-oss/agentic-orchestrator/pull/180), [Mastra](https://github.com/mastra-ai/mastra/pull/22381), [OpenAI](https://github.com/openai/codex-security/pull/2002), [Shopify](https://github.com/Shopify/checkout-kit/pull/546), [Shopify](https://github.com/Shopify/checkout-kit/pull/349), [Stripe](https://github.com/stripe/stripe-ios/pull/7336), [Owen Gretzinger](https://x.com/owengretzinger/status/2116291924219060319)

### scope-workspace-builds: Install and build only the workspace packages a job uses

- **applies when:** a monorepo job installs or builds the whole workspace while it tests one package or package family (static: `pnpm install` or `turbo run build` with no `--filter` in that job), and its `install_s` is over 30 s.
- **how:** Scope install and build to the package and its dependencies: `pnpm install --frozen-lockfile --filter <pkg>...` and `pnpm --filter <pkg>... build`, or `turbo run build --filter=<pkg>...`. The trailing `...` pulls in its dependencies. Include generated prerequisites too. A filtered install produces a different `node_modules`, so give it its own cache key, or it overwrites the full install's cache. Before you move a build out of a gate, confirm another required check still runs it (Mastra). Linear's API test install went from 44 to 73 s down to 16 to 18 s. Shopify split one sequential job into a lint job and three package-family lanes that each build their own closure, and CI went from about 11 minutes to about 5. Each new package has to join a lane.
- **estimate:** `install_s` times (1 minus the closure's share of the workspace), plus the seconds of the builds the job no longer runs. Without a measurement, use Linear's ratio of about 0.3 of the old install time.
- **verify:** The job runs the same tests as before. Every workspace package is still built and tested by some job (compare the lanes' package lists with `pnpm ls -r --depth -1`). Compare `install_s` and job time over 10 runs.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/scope-workspace-builds.md), [Linear](https://linear.app/now/ci-bottleneck-reworked#install-only-the-dependencies-each-job-needs), [Mastra](https://github.com/mastra-ai/mastra/pull/22381), [Shopify](https://github.com/Shopify/shopify-app-js/pull/2777)

### skip-identical-validation: Reuse validation for unchanged inputs

- **applies when:** the last 150 runs validate the same tree more than once (re-pushes, rebases with no content change, reruns after an unrelated failure), counted by mapping each run's `head_sha` to its tree; or a formatter or code generator re-validates output identical to its input.
- **how:** This is auto only when the skip is keyed on the full content of every input the job reads: the git tree hash (`git rev-parse HEAD^{tree}`), the runner OS and architecture, every toolchain version, and the workflow file, which the tree already covers. A key built from a hand-picked path list is a selector and belongs under skip-unaffected-jobs, with its tests. After the job passes, save a marker with actions/cache/save@v4 under that key, only on success. A small gate job looks the key up with `lookup-only: true`, and the expensive job skips at the job level on a hit, so no runner is reserved (Linear). Keep the gate small, because it sits on the critical path. For a formatter, compare the final output with the original after every restoration step and skip re-lexing only when they are identical. Every changed result still gets the original checks (OpenAI: median 5.79 s to 4.11 s).
  ```yaml
  - id: tree
    run: echo "sha=$(git rev-parse 'HEAD^{tree}')" >> "$GITHUB_OUTPUT"
  - id: pass
    uses: actions/cache/restore@v4
    with:
      path: .ci-pass
      key: test-pass-${{ runner.os }}-${{ runner.arch }}-node${{ steps.js.outputs.node-version }}-${{ steps.tree.outputs.sha }}
      lookup-only: true
  ```
- **estimate:** The share of PR runs whose tree already has a recorded pass, times the skipped jobs' `setup_s` plus `run_s`, minus the gate job's time.
- **verify:** Rerun a passed run: the jobs skip and every required check reports success. Change one byte in any file, or bump the toolchain version: the jobs run. A failed run never records a pass. The default branch and nightly runs never skip. Compare runner minutes over 20 PR runs.
- **risk:** medium
- **mode:** report-only (weakens-check)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/skip-identical-validation.md), [Linear](https://linear.app/now/ci-bottleneck-reworked#optimize-the-jobs-that-gate-other-work), [OpenAI](https://github.com/openai/openai-ruby/pull/966)

### package-once: Package once, and build full installers after merge

- **applies when:** a PR job builds explicitly and then runs a packaging command that builds again, or PRs build full release installers that no test reads (static), and that job is on the `critical_path`.
- **how:** Read the wrapper scripts, then remove the standalone build that packaging repeats. That half alone is avoid-duplicate-builds, which is auto. On PRs, package only the unpacked app the end-to-end tests consume (for electron-builder, `--dir`), and build and inspect the full installers on pushes to main, with an owner who watches that run. DoorDash did both in one PR.
- **estimate:** The removed build step's seconds, plus the full installer build's seconds minus the unpacked build's seconds, on the PR's `critical_path` job.
- **verify:** For the report: the PR end-to-end journeys run against the unpacked app with the same count, and main still builds and inspects every installer. If the user approves, a deliberate installer-only break goes red on main and notifies the named owner.
- **risk:** medium
- **mode:** report-only (after-merge)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/package-once.md), [DoorDash](https://github.com/doordash-oss/agentic-orchestrator/pull/139)

### defer-heavy-validation: Move selected heavy checks after merge

- **applies when:** a heavy suite or matrix (VM tests, a full build matrix, installer tests) is the `critical_path` job and over 50% of `pr_p50`, and the cheaper required checks catch nearly every break it catches.
- **how:** For the report, count leg-unique failures in the last 150 runs: failures only the heavy suite caught, each of which would have reached main. If the user approves, keep a chosen PR gate, and run the heavy suite on pushes to main, merge-queue runs and manual dispatch, optionally as non-required PR jobs. Required check names still report on every PR. Give the post-merge run an owner who is notified and can block a release, and write the tradeoff in the PR. OpenAI kept Bazel build, test and clippy on PRs and moved the full Cargo matrix to main. Shopify kept component tests and cheap flake checks on PRs and moved VM tests, installer tests and the remaining flake checks after merge.
- **estimate:** The heavy job's `wait_s` plus `setup_s` plus `run_s`, minus the next slowest PR job's, saved from `pr_p50`.
- **verify:** For the report: the leg-unique failure count and the minutes saved. If adopted, main runs the suite on every push, and a deliberate failure in the moved suite goes red on main and notifies the owner.
- **risk:** high
- **mode:** report-only (after-merge)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/defer-heavy-validation.md), [OpenAI](https://github.com/openai/codex/pull/16072), [Shopify](https://github.com/Shopify/tecnix/pull/74)

### minimal-merge-gates: Keep blocking merge gates minimal and follow flakes with a rerun

- **applies when:** `rerun_rate` over 5% on required checks, so merges wait on results a follow-up run clears, in a repo with high `agent_prs_per_day` and short-lived PRs.
- **how:** For the report, list each required check with its `rerun_rate` and the merge wait it adds. If the user approves, keep blocking only the checks that guard correctness, and handle a flake with a follow-up run while work continues. Checks that guard changes a follow-up commit cannot undo stay required, such as migrations, security checks and published artifacts. The flakes the reruns reveal still get fixed. OpenAI's agent-first team works this way because, when agent throughput far exceeds human attention, corrections are cheap and waiting is expensive.
- **estimate:** For each check dropped from blocking, its `rerun_rate` times `pr_p50`, per PR.
- **verify:** For the report: the wait per PR each dropped gate adds. If adopted, the dropped checks still run on every PR and on main, their failures notify an owner, and `rerun_rate` is tracked until the flakes are fixed.
- **risk:** high
- **mode:** report-only (after-merge)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/minimal-merge-gates.md), [OpenAI](https://openai.com/index/harness-engineering/)

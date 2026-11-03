# Unnecessary work

A run often does the same work twice, starts on events no job cares about, or pays for tools and builds nothing reads. These entries remove that work while every check still runs at least once on the inputs it covers.

### run-ci-once: Run CI once per pull request commit

- **applies when:** a PR workflow triggers on `push` for every branch and on `pull_request` (static), so `runs_per_day` shows two runs for the same head SHA; or metadata events (`edited`, `labeled`, `assigned`) start checks that do not read that metadata.
- **how:** Limit `push` to the default branch, and to release branches if they need push builds. PRs run through `pull_request`. Keep `workflow_dispatch` so a branch without a PR can still run by hand. Drop trigger types such as `labeled` or `edited` from workflows whose jobs do not read that metadata. Before you treat two runs as duplicates, check that they test the same ref with the same permissions (`pull_request` tests the merge commit, `push` tests the branch head). Preview deploys, cache warming, release side effects and metadata-dependent checks keep the triggers they need. Shopify's two identical runs for one commit started 3 seconds apart.
  ```yaml
  on:
    push:
      branches: [main]
    pull_request:
    workflow_dispatch:
  ```
- **estimate:** Runner time saved per PR commit is the duplicate run's `setup_s` plus `run_s`, summed over its jobs. `pr_p50` drops by the extra `wait_s` the duplicate causes when both runs queue for the same runners, measured as the `wait_s` gap between paired and single runs.
- **verify:** Over the next 10 PR pushes, each head SHA has one run. Compare `wait_s` and `pr_p50` over 20 runs before and after. Every required check name still reports on every PR, a push to main still runs the full workflow, and a deliberate failing test on a PR still turns the run red.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/run-ci-once.md), [Anthropic](https://claude.com/resources/articles/agentic-coding-is-straining-ci-heres-how-we-scaled-test-impact-analysis-at-anthropic), [Shopify](https://github.com/Shopify/vscode-shopify-ruby/pull/808), [Spotify](https://github.com/spotify/target-determinator/pull/15)

### lint-before-the-push: Fix lint before the push reaches CI

- **applies when:** the repo has no pre-push hook (static: no `lefthook.yml`, no `.husky/pre-push`, no hook installed by a setup script), or more than 5% of failed PR runs in the last 150 failed only in a format, lint or typecheck job.
- **how:** Add a pre-push hook (lefthook, husky, or a plain git hook installed by the repo's setup script) that runs format, lint and typecheck on the changed files only, in under 10 seconds. Owen's takes 9. Time it. It lives in a hook because agents skip steps written in `AGENTS.md`. fast-ci's Baseline `lefthook.yml` is this hook. Stripe goes further: its coding agents run a subset of linters locally and loop on them before pushing, and a local cache of lint results returns fixes in well under a second. The hook is a first filter. CI keeps its full format, lint and typecheck jobs as the required gate, and a failing hook gets fixed, never bypassed with `--no-verify`.
  ```yaml
  pre-push:
    parallel: true
    commands:
      lint:
        glob: "*.{js,jsx,ts,tsx}"
        run: npx oxlint {push_files}
  ```
- **estimate:** (PR runs that failed only on format, lint or typecheck, divided by all PR runs) times `pr_p50`, per PR run, because each of those failures costs one whole extra CI round before the fix.
- **verify:** Time the hook on a typical push and confirm it finishes in under 10 s, and that `lefthook run pre-push --all-files` passes. Commit a deliberate lint error and confirm `git push` stops before it reaches the remote. Over the next 20 PR runs, the share that fail only on lint or format drops. CI's format, lint and typecheck jobs are unchanged and still required.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/lint-before-the-push.md), [Stripe](https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents-part-2), [Owen Gretzinger](https://x.com/owengretzinger/status/2116291924219060319)

### avoid-duplicate-builds: Remove repeated build steps

- **applies when:** `duplicate_steps` shows the same build command (`pnpm build`, `cargo build`, `docker build`) twice in one job or in several jobs of one run; or a build runs right before a command that builds again (`pnpm pack` with a `prepack` script, a second `docker build` only to export files).
- **how:** Trace who produces each artifact and who consumes it, keep the one build whose output is published or tested, and remove the other. Before you delete an explicit build in front of `pnpm pack`, confirm the exact pack command runs `prepack` (no `--ignore-scripts`), or the package ships stale (OpenAI). In a release job, keep the build that runs after the last version change (Mastra). In a multi-stage Dockerfile, derive the test and lint stages from one build stage, so cargo, Go or Maven reuse its output (Spotify: total compute across the affected stages fell from 1807 s to 712 s, 61%, in a local no-cache build). Delete a second build that only copies outputs out or prints a summary, after checking no later step, release or reviewer reads them. To share a build across jobs, pass it with actions/upload-artifact@v4 and actions/download-artifact@v4.
- **estimate:** The removed build's step seconds, per run where it ran. `pr_p50` drops by the same amount when the build was on the `critical_path` job. For Dockerfile stage reuse with no per-stage timing, use Spotify's 61% of the affected stages' time.
- **verify:** Over 10 runs before and after, the build count per run drops and the job time drops by about the build's time. The published or tested artifact passes the same checks (compare `pnpm pack --dry-run` file lists, or image contents). Every test and lint job still runs and reports.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/avoid-duplicate-builds.md), [Mastra](https://github.com/mastra-ai/mastra/pull/22380), [OpenAI](https://github.com/openai/codex-security/pull/397), [Spotify](https://github.com/spotify/confidence-resolver/pull/355), [Spotify](https://github.com/spotify/confidence-resolver/pull/81)

### avoid-duplicate-validation: Run shared validation once

- **applies when:** `duplicate_steps` shows the same lint, typecheck, test or snapshot command in more than one job or matrix leg on the same inputs: an OS matrix that repeats typecheck, lint and format on every leg, a test wrapper that calls a test task CI also calls, Debug and Release passes over code with no configuration-specific paths, or a bot's commit hook that repeats required CI.
- **how:** Run platform-independent checks on one leg (`if: matrix.os == 'ubuntu-latest'`) and keep packaging and smoke tests on every leg (DoorDash). Any check that reads platform-specific code paths, native modules or line endings stays on every leg where it can differ. Where a wrapper task already runs the unit tests, call one or the other per module, not both (Stripe Android). Skip a snapshot class in the broad suite only while a required lane runs it (Stripe iOS). Drop a duplicate configuration only when it has no code paths or published build of its own (Stripe .NET). Disable a hook in an automated version PR only after proving required workflows check the same files and fail the same way (Mastra).
- **estimate:** The repeated step's `run_s` times the number of extra legs or jobs it ran in, as runner time per run. `pr_p50` drops when the repeated step sat on the `critical_path` job.
- **verify:** List unique test ids, checks and snapshot classes across the whole run before and after (JUnit reports or the runner's list mode). The union is identical. Each check still runs at least once per run and its required name still reports. A deliberate type error still fails the run. Compare runner time and `pr_p50` over 10 runs.
- **risk:** medium
- **mode:** report-only (weakens-check)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/avoid-duplicate-validation.md), [DoorDash](https://github.com/doordash-oss/agentic-orchestrator/pull/139), [Mastra](https://github.com/mastra-ai/mastra/pull/2952), [Stripe](https://github.com/stripe/stripe-ios/pull/7332), [Stripe](https://github.com/stripe/stripe-android/pull/13033)

### install-consumed-tools: Install tools only in the jobs that need them

- **applies when:** a shared setup step or composite action installs a runtime, browser or CLI in every job, and `tool_install_s` is over 10 s in a job that never calls it; or a change-detection job runs a full workspace install before a decision that takes seconds.
- **how:** Move each install into the jobs that use it, and list every tool a job needs in that job. Trace indirect use first: scripts, `package.json` lifecycle scripts and local actions can call the tool. Stripe Android moved a Ruby install of about 2 minutes out of the shared prepare step into the two jobs that run Ruby. For a change-detection or graph job, skip the workspace install and run a pinned standalone binary or a filtered install of the root tools only, then prove its dependency discovery works without install scripts (Mastra).
- **estimate:** `tool_install_s` times the number of jobs that installed the tool and did not use it, as runner time per run. `pr_p50` drops by `tool_install_s` when the `critical_path` job was one of them.
- **verify:** Compare `tool_install_s` per job over 10 runs before and after. Every job still passes with the same test count, including the jobs that use the tool. A job that silently needed the tool would fail, so a green run with unchanged counts is the proof.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/install-consumed-tools.md), [Mastra](https://github.com/mastra-ai/mastra/blob/f92e947a448a47515acf14df1eddc5fd5c36f424/.github/workflows/prebuild.yml), [Mastra](https://github.com/mastra-ai/mastra/pull/12246), [Stripe](https://github.com/stripe/stripe-android/pull/10184)

### gate-irrelevant-events: Reject irrelevant events before allocating runners

- **applies when:** `irrelevant_runs` over 0 from non-code events, such as `issue_comment` runs whose comment holds no command or `pull_request` `edited` runs where only the body changed; or a job whose every step skips on an `if:` after its runner starts (static: the condition sits on steps, not on the job).
- **how:** Move the condition to the job, so GitHub decides before it allocates a runner. For comment commands, match the exact command in the new body or the previous one (`github.event.changes.body.from`), so removing a command still counts (Mastra). Keep author permission checks and fork trust separate from event filtering. For body-only PR edits, skip source validation and give those events their own concurrency group so they never cancel a real run. Title, base and combined edits still run full validation (OpenAI). When a preparation job already classifies the change, read its output in a job-level `if:`, keep required names reporting with explicit jobs, and run everything for an unknown diff (OpenAI).
  ```yaml
  jobs:
    major-bump:
      if: >-
        github.event_name == 'issue_comment' &&
        (contains(github.event.comment.body, '/major') ||
         contains(github.event.changes.body.from, '/major'))
      runs-on: ubuntu-latest
  ```
- **estimate:** `irrelevant_runs` per day times the runner time of the jobs they start (`setup_s` plus `run_s`). Wall time improves through `wait_s` when those runs compete for runners, and by up to `pr_p50` per body edit that used to cancel and restart a real run.
- **verify:** On a test PR, post a plain comment and edit the body: no job takes a runner. Post the command, edit the title and change the base: the full checks run. On a PR with a red required check, a body edit leaves it red, because a skipped run must never overwrite a failed, pending or missing required result. Compare runs per day before and after.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/gate-irrelevant-events.md), [Mastra](https://github.com/mastra-ai/mastra/pull/22381), [OpenAI](https://github.com/openai/codex-security/pull/1708), [OpenAI](https://github.com/openai/openai-agents-python/pull/5264)

### defer-draft-work: Wait until a draft is ready for expensive checks

- **applies when:** `draft_runs` over 20% of PR runs, and the team agrees that expensive checks on drafts can wait.
- **how:** Add `ready_for_review` to the `pull_request` types and put a draft guard on each expensive job and its required aggregate. Marking the PR ready then starts a full run on its head commit. Without `ready_for_review`, a promoted draft keeps its skipped result on an untested commit (Shopify). Pushes to main and merge-queue runs keep their validation (Uber). Agents that open draft PRs and wait on CI lose their feedback, so check how agents open PRs in this repo first.
  ```yaml
  on:
    pull_request:
      types: [opened, synchronize, reopened, ready_for_review]
  jobs:
    test:
      if: github.event_name != 'pull_request' || !github.event.pull_request.draft
  ```
- **estimate:** `draft_runs` per day times the runner time of the guarded jobs. Ready PRs gain only through lower `wait_s` when runners are shared, so per-PR wall time for drafts does not drop.
- **verify:** Test draft, ready, reopened, main and merge-queue events. Drafts skip the expensive jobs, a ready PR runs every job on its head commit, and every required check reports before merge. Compare runner minutes per day before and after.
- **risk:** medium
- **mode:** report-only (weakens-check)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/defer-draft-work.md), [Shopify](https://github.com/Shopify/checkout-kit/pull/284), [Uber](https://github.com/uber/submitqueue/pull/180)

### build-only-consumed-inputs: Build only what the test or analysis consumes

- **applies when:** a test, scan or end-to-end job runs a broad build (`bazel build //...`, `turbo run build` with no filter, every Docker service, every app variant) and then tests or analyzes a subset of it, and that build is over 30% of the job's `run_s`.
- **how:** Declare what each lane consumes and build only that. In Bazel, add `--build_tests_only` to the test command and keep `bazel build //...` in a separate required job (Uber). Have each integration test declare the binaries, Dockerfiles and configs it uses, and stage a minimal Docker context from them, with image tags hashed from those contents (Uber). Build only the variant an end-to-end job tests, and skip packaging an analysis never reads (Stripe iOS stopped packaging XCFrameworks for an arm64-only API check). Keep every input the analysis reads: symbols, architectures, compiler settings and index completeness. Compile-only validation stays in a required job.
- **estimate:** The broad build's step seconds minus the scoped build's seconds, on the consuming job. With no CI history for the scoped build, time it once locally.
- **verify:** The discovered test count is the same before and after (`bazel query 'tests(//...)'`, JUnit totals). The compile-only job still builds everything and is still required, so a deliberate compile error in a target the lane no longer builds still fails the run. Compare job time over 10 runs.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/build-only-consumed-inputs.md), [Stripe](https://github.com/stripe/stripe-ios/pull/7336), [Uber](https://github.com/uber/submitqueue/pull/439), [Uber](https://github.com/uber/submitqueue/pull/701)

### sparse-checkout-for-gates: Check out only the gate's script

- **applies when:** a small aggregation or gate job (`ci-ok`, an all-succeeded check, a title or label check) does a full checkout and its `checkout_s` is over half of the job's time.
- **how:** Give the gate a sparse checkout that lists every script and local action it reads, including transitive ones, and keep its full success logic. A gate that reads only `needs` results needs no checkout at all. Sorbet's gate step took 27 s, 25 of them cloning the repository.
  ```yaml
  - uses: actions/checkout@v5
    with:
      sparse-checkout: |
        scripts/ci
        .github/actions
  ```
- **estimate:** The gate job's `checkout_s` minus about 2 s for the sparse checkout. The gate runs after every other job, so `pr_p50` drops by the same amount.
- **verify:** Compare the gate job's time over 10 runs. Push a deliberate failing test and confirm the gate goes red, and confirm it passes when every job passes.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/sparse-checkout-for-gates.md), [Stripe](https://github.com/sorbet/sorbet/pull/10214)

### drop-duplicate-image-workflow: Fold a duplicate image workflow into the shared build

- **applies when:** two workflows build overlapping images or artifacts from the same sources on the same events (static: two `docker build` or `docker/build-push-action` calls over the same context).
- **how:** Make the second image a stage of the shared Dockerfile, built on its existing build stage, build that target in the shared job, and delete the separate workflow and its Dockerfile. Move every check the deleted workflow ran into the shared build. If one of its job names is a required check, keep a job with that name.
- **estimate:** The deleted workflow's runner time per run (`setup_s` plus `image_pull_s` plus `run_s`). The shared build grows only by the new stage's own layers, because it reuses the build stage.
- **verify:** The image builds in the shared job and has the same entrypoint and files as before (`docker run --rm <image> ls`, or container-structure-test). Required checks are unchanged. Compare runner minutes per run over 10 runs.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/drop-duplicate-image-workflow.md), [Spotify](https://github.com/spotify/confidence-resolver/pull/132)

### profile-build-hotspots: Use build profiles to remove expensive work

- **applies when:** a compile or build step is over 50% of `run_s` on the `critical_path` job, and stays there with a warm cache.
- **how:** Profile before you change anything: `cargo build --timings`, `tsc --extendedDiagnostics` or `--generateTrace`, Bazel `--profile` with `bazel analyze-profile`, Gradle `--profile`. Compiler phases overlap, so their timings do not add up. Then remove the work the profile names. OpenAI removed async-trait wrappers from concrete tool handlers and kept boxing only at the registry adapter (rustc total 187.15 s to 68.98 s on a clean rebuild). Sorbet replaced a Protobuf serialization path with JSON to drop protoc from its main target (debug build 3:57.62 to 2:55.61), and added a Bazel query to its linters that fails on any new path back to protoc. A source refactor keeps behavior, public API, serialization formats and every test.
- **estimate:** The profiled share of the hotspot times the build step's seconds, confirmed by one clean build before and after on the same machine.
- **verify:** Clean-build time over 3 runs each, before and after, on the same machine. Every test passes unchanged, and a graph check fails if the removed dependency comes back.
- **risk:** high
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/profile-build-hotspots.md), [OpenAI](https://github.com/openai/codex/pull/16630), [Stripe](https://github.com/sorbet/sorbet/pull/10124)

### skip-warm-bundle-runner: Remove a redundant runner after verified cache delivery

- **applies when:** a job's only work is to recheck an artifact that a preparation job already restored, verified and uploaded, and on warm runs that job's `wait_s` plus `run_s` is spent on nothing else.
- **how:** Have the preparation job output whether it had an exact cache hit and whether verification and upload succeeded. Skip the bundle job only when all of those hold. An exact cache hit alone is not enough. Cold assembly and protected publication stay together in one job, and cold builds, platform proofs and release validation stay required. Consumers download the uploaded artifact directly.
- **estimate:** The bundle job's `wait_s` plus `setup_s` plus `run_s`, times the share of runs with an exact hit (`cache_hit_pr`). OpenAI measured a median 7 s across 29 warm attempts, so the gain is small unless `wait_s` is high.
- **verify:** On a warm run, the bundle job skips and consumers get the same artifact (compare checksums). Change a cache key input and the bundle job runs. Make the upload fail on purpose and confirm the bundle job runs or the run fails.
- **risk:** medium
- **mode:** report-only (weakens-check)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/skip-warm-bundle-runner.md), [OpenAI](https://github.com/openai/codex-security/pull/2042)

### avoid-emulator-build-contention: Build before starting the emulator

- **applies when:** a mobile job boots an Android emulator or iOS simulator before or while it compiles the app (static: the emulator step comes before the build, or the emulator action's script runs the build), and that build is over 30% of the job's `run_s`.
- **how:** Compile the app first, then boot the emulator and install the finished build. Build only the emulator's ABI in that lane (Stripe React Native built only x86_64), and keep the device and ABI coverage other lanes need. Measure disk headroom before removing a disk-cleanup step, which Stripe's author estimated at 20 s.
- **estimate:** The build step's seconds with the emulator running minus without it, from one run each, plus the build time of the ABIs dropped from this lane.
- **verify:** The same end-to-end tests pass. The release lane still builds every ABI. Compare job time over 10 runs.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/avoid-emulator-build-contention.md), [Stripe](https://github.com/stripe/stripe-react-native/pull/2111)

### separate-cheap-formatting: Run cheap formatting before semantic formatting

- **applies when:** a format check that loads the whole solution or project (such as `dotnet format` on a solution with generated code) takes over 60 s of `run_s`.
- **how:** Add a fast folder-based whitespace pass (`dotnet format whitespace --folder`) ahead of the full formatter, which still runs. Keep the semantic pass and its output. Keep the change only if the two passes together beat the old single pass.
- **estimate:** The old format step's seconds minus the two new passes' seconds, over 3 runs each. Keep it only when the result is positive.
- **verify:** A deliberate whitespace error and a deliberate semantic formatting error each still fail the check. Compare the format step's time over 10 runs.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/separate-cheap-formatting.md), [Stripe](https://github.com/stripe/stripe-dotnet/pull/3202)

### batch-semantic-validation: Validate shared declarations once without losing file boundaries

- **applies when:** a declaration or type validator runs once per file over shared, reopened namespaces (RBS with Steep is the documented case), and that step is over 30 s of `run_s`.
- **how:** Parse each file on its own for syntax, then run one consolidated semantic pass. Take the per-file path for the whole job when any file has NUL bytes or file-scoped directives, and when the fast path reports any error, rerun the original files for exact diagnostics. OpenAI's Ruby SDK has 1,209 RBS files and went from a 52.38 s per-file Steep run to 6.22 s consolidated.
- **estimate:** The validator step's seconds times (1 minus the batched ratio). Use OpenAI's ratio of about 0.12 until the repo measures its own.
- **verify:** Seed one syntax error, one semantic error and one file-scoped directive, and confirm each still fails with the same file and line as before. Compare the step's time over 10 runs.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/batch-semantic-validation.md), [OpenAI](https://github.com/openai/openai-ruby/pull/333)

### share-bazel-startup: Give build queries the same startup flags as the build

- **applies when:** a job runs `bazel query` or `cquery` before `bazel build` or `bazel test` with different startup flags (static), and its time stays high with every action cached.
- **how:** Put the CI startup flags in one place, such as `startup` lines in `.bazelrc` or one shared script, and run the queries with them, so they reuse the build's server instead of starting a second one. Check the queries return the same targets with the build's flags. OpenAI's Windows clippy job took over five minutes with every action cached until its queries shared the build's server.
- **estimate:** The query step's seconds with separate flags minus with shared flags. From logs alone, count the Bazel server starts after the first one in a job, times one startup's seconds.
- **verify:** Job logs show one Bazel server start per job. The query output is identical before and after (diff the target lists). Compare job time over 10 runs.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/share-bazel-startup.md), [OpenAI](https://github.com/openai/codex/pull/19232)

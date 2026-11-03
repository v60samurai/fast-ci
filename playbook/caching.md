# Caching and setup

These entries cut the time a job spends before the project's own commands start: checkout, toolchain and tool installs, dependency installs, image pulls and cache transfers. Read this file when `setup_share` is large, `cache_hit_pr` is low, or `checkout_s`, `install_s`, `tool_install_s` or `image_pull_s` stand out.

### fc-seed-cache-from-main: Seed the dependency cache from the default branch

- **applies when:** `cache_hit_pr` is 20 or more points below `cache_hit_main`, or `cache_hit_pr` is under 80%, or no job saves the dependency cache on pushes to the default branch (static), or `install_s` is over 20 s while the workflow caches only the package manager's download cache.
- **how:** GitHub scopes a PR's caches to its own branch plus the default branch, so a PR can only restore what its own earlier runs saved or what the default branch saved. If nothing saves on the default branch, most PRs start cold. Add a job that runs on pushes to the default branch and saves the cache. Cache the installed dependencies (`node_modules`, `.venv` or the equivalent), not only the package manager's download cache, keyed on OS, arch, the resolved runtime version and a hash of the lockfiles, `pnpm-workspace.yaml`, `.npmrc` and `patches/`. PR jobs restore the same key and run the install only on a miss. fast-ci's Baseline template (`templates/ci.yml`) already ships this as its `seed-cache` job.
  ```yaml
  seed-cache:
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      # checkout, then actions/setup-node@v5 with id: js, as in the other jobs
      - id: deps
        uses: actions/cache@v4
        with:
          path: node_modules
          key: node-modules-${{ runner.os }}-${{ runner.arch }}-node-${{ steps.js.outputs.node-version }}-${{ hashFiles('pnpm-lock.yaml', 'pnpm-workspace.yaml', '.npmrc', 'patches/**') }}
      - if: steps.deps.outputs.cache-hit != 'true'
        run: pnpm install --frozen-lockfile
  ```
- **estimate:** per PR job, `install_s` times (0.99 minus `cache_hit_pr`) times 0.6. Owen's PR misses fell from half to 1%, and a `node_modules` restore took 13 s against a 33 s install, so a hit saves about 60% of `install_s`. Multiply by the number of jobs that install.
- **verify:** compare `cache_hit_pr` and the install step's seconds over 10 PR runs before and after the seed job has run once on the default branch. The same jobs run, the same test count is reported, and a PR that changes the lockfile misses the cache, runs the install and still passes.
- **risk:** medium
- **mode:** auto
- **evidence:** [Owen Gretzinger](https://x.com/owengretzinger/status/2116291924219060319), [StarSling cache-write-ownership](https://starsling.dev/ci-playbooks/techniques/cache-write-ownership.md), [StarSling reuse-package-downloads](https://starsling.dev/ci-playbooks/techniques/reuse-package-downloads.md)

### reuse-package-downloads: Cache package downloads and dependency stores

- **applies when:** `install_s` is over 20 s and the setup step has no package cache (static: `actions/setup-node` without `cache:`, `actions/setup-go` with `cache: false`, `actions/setup-java` without `cache:`, Bazel without a repository or disk cache).
- **how:** turn on the ecosystem's own cache. Use `actions/setup-node@v5` with `cache: pnpm`, `yarn` or `npm` (install pnpm first with `pnpm/action-setup@v4` so setup-node can find it), `actions/setup-go@v5` with `go-version-file: go.mod` and its default cache, `actions/setup-java@v5` with `cache: gradle` or `gradle/actions/setup-gradle@v4` with `--build-cache`, and `bazel-contrib/setup-bazel` for Bazel's repository and disk caches. Keep the locked install (`--frozen-lockfile`, `npm ci`, `go test -count=1`) on every hit, so the cache only shortens the download.
- **estimate:** `install_s` minus a warm install's seconds, times the number of jobs that install. Measure one warm run on a branch, since the sources mix this change with others (Stripe React Native builds went from 8:03 to 2:34 across all of its PR's changes).
- **verify:** compare the install step over 10 runs before and after. The install command, its lockfile flag and every test and check still run on a hit, and the same test count is reported.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/reuse-package-downloads.md), [DoorDash](https://github.com/doordash-oss/agentic-orchestrator/pull/36), [Linear pnpm store](https://github.com/linear/linear/pull/1130), [Linear Yarn cache](https://github.com/linear/linear-zapier/pull/101), [Shopify](https://github.com/Shopify/checkout-kit/pull/182), [Spotify](https://github.com/spotify/target-determinator/pull/15), [Stripe](https://github.com/stripe/stripe-react-native/pull/2111), [Uber](https://github.com/uber/tango/pull/219)

### blobless-history: Keep full history and download old blobs on demand

- **applies when:** `checkout_s` is over 15 s on a checkout with `fetch-depth: 0` and no `filter: blob:none` (static), or a job uses a shallow clone and then deepens it or fails on a git history read (`git log`, `git describe`, changesets, `nx affected`, `turbo --filter=...[origin/main]`).
- **how:** use a blobless clone, not a shallow one. A shallow clone breaks anything that reads git history. Set `filter: blob:none` on `actions/checkout@v5`, with `fetch-depth: 0` where the job needs history. Git then fetches every commit and tree but only the file contents of the checked-out revision, and downloads older blobs on demand.
  ```yaml
  - uses: actions/checkout@v5
    with:
      filter: blob:none
      fetch-depth: 0
  ```
- **estimate:** `checkout_s` times about 0.67 on each job that needs history. Owen's checkout went from 36 s to 12 s, and Mastra's transfer fell from 1,572 MB to 189 MB, about 88% fewer bytes.
- **verify:** compare `checkout_s` over 10 runs before and after. Every step that reads history (change detection, versioning, changelog) gives the same output on the same commit as before.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/blobless-history.md), [Mastra](https://github.com/mastra-ai/mastra/pull/21298), [Owen Gretzinger](https://x.com/owengretzinger/status/2116291924219060319)

### fetch-needed-history: Fetch only the repository history a job needs

- **applies when:** a job checks out with `fetch-depth: 0` or `lfs: true` but never reads history or LFS files (static), or a job checks out code but only calls the GitHub API, or `checkout_s` is over 20 s on a change-detection job.
- **how:** for each job, read what it uses. A job that only tests the tree keeps the default single-commit checkout. A job that diffs against the base fetches the base and head and deepens in batches until `git merge-base` resolves, instead of fetching every branch. Release jobs fetch only the default branch's history, without tags unless they read tags. Drop `lfs: true` where nothing reads LFS files. Remove checkout from jobs that use only `gh` or the API, and pass `GH_REPO: ${{ github.repository }}` to them. Use `sparse-checkout` where a job reads a few paths.
- **estimate:** `checkout_s` minus about 5 s per job that drops full history, and all of `checkout_s` for a job that drops checkout. Linear's slowest change-detection gate went from 94 to 20 s by capping depth, and jobs that dropped checkout went from 27 to 7 s.
- **verify:** compare `checkout_s` over 10 runs before and after. Change detection lists the same changed files on the same PRs, release dry runs compute the same version, and when the merge base cannot be resolved the job runs the full check.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/fetch-needed-history.md), [Linear](https://linear.app/now/ci-bottleneck-reworked#fetch-only-what-each-job-needs), [Mastra release workflow](https://github.com/mastra-ai/mastra/blob/f92e947a448a47515acf14df1eddc5fd5c36f424/.github/workflows/npm-publish.yml), [Mastra PR](https://github.com/mastra-ai/mastra/pull/14432), [OpenAI](https://github.com/openai/frontier-evals/pull/53), [Stripe](https://github.com/stripe/stripe-ios/pull/7331)

### checkout-before-cache: Restore dependencies after their manifest exists

- **applies when:** a setup action with a cache input runs before `actions/checkout` (static), or its `cache-dependency-path` does not match the real lockfile location, or the setup step logs that it found no dependency file, or `cache_hit_pr` and `cache_hit_main` are both near 0.
- **how:** move `actions/checkout@v5` ahead of the language setup step. Point `cache-dependency-path` at the real lockfile, for example `**/go.sum` or `apps/web/pnpm-lock.yaml`, with a glob that matches only the intended modules. Remove cache steps for tools the repo no longer uses. Keep the install and integrity checks on a hit.
- **estimate:** `install_s` times (1 minus `cache_hit_pr`) per job, minus the restore time, since a cache that cannot find its manifest never hits.
- **verify:** the setup step reports a cache hit on the second run, and `install_s` drops over 10 runs. The same install command and tests run.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/checkout-before-cache.md), [Uber](https://github.com/uber/tchannel-go/pull/935)

### cache-write-ownership: Give shared cache writes deliberate ownership

- **applies when:** PR or merge-queue runs save cache entries (static: `actions/cache` with no restore-only split) while the repository is near its 10 GB cache quota or `cache_hit_main` is under 90%, or logs show "Unable to reserve cache" or parallel jobs racing to save the same key.
- **how:** decide who writes each cache. For caches every PR starts from, save only on pushes to the default branch and use `actions/cache/restore@v4` in PR and merge-queue jobs, so their writes stop evicting the entries PRs need. Where several jobs fill one key with different contents, give each job its own key prefix with a matching restore fallback, compute the key once and reuse it for restore and save, and skip the save on an exact hit.
- **estimate:** the cache save step's seconds on every PR job, plus `install_s` times the rise in `cache_hit_pr` once main's entries stop being evicted.
- **verify:** compare save-step seconds and `cache_hit_pr` over 10 PR runs before and after, and check that `gh cache list` shows fewer PR-ref entries. Every job still restores and builds cold on a miss, and the same tests run.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/cache-write-ownership.md), [Anthropic](https://github.com/anthropics/buffa/pull/288), [OpenAI](https://github.com/openai/codex/pull/18366)

### remove-expensive-caches: Remove caches that cost more than they save

- **applies when:** a cache's restore plus save seconds are more than 70% of the cold step it replaces, or its hit rate (`cache_hit_pr`) is under 30% while it saves on most runs. Read the cache step and post-job save step times from the job logs.
- **how:** measure first, per cache: restore seconds on a hit, save seconds, hit rate, and the cold install or build seconds. Before removing, try a narrower cache, the package manager's store instead of `node_modules`, a more stable key, or restore fallbacks. If the cache still costs more, delete its step and keep the install or build as it was.
- **estimate:** (restore seconds plus save seconds) minus cold seconds times hit rate, per job. Linear measured about 28 s to restore `node_modules` against about 7.5 s for a filtered install. OpenAI's release-tag runs spent 66,295 s saving caches against 1,515 s restoring them across 289 runs.
- **verify:** compare the job's total seconds over 10 runs before and after. The same install, build and test steps run, with the same test count.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/remove-expensive-caches.md), [Linear](https://linear.app/now/ci-bottleneck-reworked#don%27t-cache-when-it%27s-faster-to-rebuild), [OpenAI](https://github.com/openai/codex/pull/11540)

### cache-python-environments: Restore compatible Python environments

- **applies when:** a Python job's `install_s` is over 20 s on runs with an unchanged interpreter and lockfiles, and the workflow caches only pip downloads or nothing.
- **how:** if the repo uses uv, use `astral-sh/setup-uv` with `enable-cache: true`. Otherwise cache `.venv` with `actions/cache@v4`, keyed on `runner.os`, `runner.arch`, the resolved Python version from `actions/setup-python@v5`'s output and a hash of every lockfile. Keep the sync step (`uv sync --frozen`, `pip install -r ...`) after the restore, so a stale environment is repaired.
- **estimate:** `install_s` times (1 minus about 0.4) per Python job on a hit, using Owen's 13 s restore against a 33 s install as the ratio. OpenAI's jobs fell from 10m42s to 2m12s with this cache plus prebuilt wheels and a narrower suite.
- **verify:** compare `install_s` over 10 runs before and after. The sync step still runs, the same tests are collected, and a lockfile change rebuilds the environment.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/cache-python-environments.md), [OpenAI environment cache](https://github.com/openai/openai-python/pull/3573), [OpenAI move to uv](https://github.com/openai/openai-python/pull/3653)

### cache-tool-downloads: Reuse downloaded tools across runs

- **applies when:** `tool_install_s` is over 20 s for a pinned tool: Playwright browsers, a `cargo install`, a pinned `npx` tool, a JDK download, or a matrix leg that downloads the same packages each run.
- **how:** cache the tool's download or install directory with `actions/cache@v4`, keyed on the runner OS, arch, the exact tool version and every pinned revision it is built against. For Playwright, cache `~/.cache/ms-playwright` keyed on the Playwright version from the lockfile, and keep `npx playwright install --with-deps` after the restore so it repairs a partial cache and installs system packages. For downloaded toolchains, verify the published checksum and install to a temporary directory before moving it into place.
- **estimate:** `tool_install_s` minus the restore seconds, per job. Bun's cold lint run took about 6.5 minutes and the PR expected about 1.5 minutes warm.
- **verify:** compare `tool_install_s` over 10 runs before and after, including one run after a version bump. The tool's own install or check step still runs, and the job runs the same checks.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/cache-tool-downloads.md), [Anthropic](https://github.com/oven-sh/bun/pull/38459), [Linear](https://github.com/linear/linear/pull/1130), [Shopify](https://github.com/Shopify/checkout-kit/pull/972), [Stripe](https://github.com/stripe/stripe-android/pull/12402)

### nested-lockfile: Key nested installs from their own lockfile

- **applies when:** a job installs in a subdirectory (`working-directory:` or a second checkout under a `path:`) while its setup step keys the cache on the root lockfile or none (static).
- **how:** pass the nested lockfile to the setup step's `cache-dependency-path`, or add that input to the shared composite setup action and have each caller pass its own lockfile. Keep the frozen install after a hit, and keep caches from untrusted checkouts apart from trusted ones.
- **estimate:** that job's `install_s` times its current miss rate, minus the restore time.
- **verify:** the nested job reports a cache hit on its second run, and its `install_s` drops over 10 runs. The frozen install and the same tests still run.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/nested-lockfile.md), [Mastra](https://github.com/mastra-ai/mastra/pull/14432)

### content-based-cache-keys: Keep unrelated environment changes out of cache keys

- **applies when:** a content cache key includes `github.ref`, `github.head_ref`, `github.sha` or `github.run_id` with no stable restore prefix (static), or a Turborepo or Nx task hashes environment variables or secrets the build never reads, or the same tree misses the cache across different events or after a runner image update.
- **how:** key caches on what changes the output: lockfiles, config, tool versions, OS and arch. Remove branch names, event data and runtime-only secrets from task hash inputs (`turbo.json` `env` and `globalEnv`, Nx `inputs`) once you have checked the build never reads them. Where a tool hashes `PATH`, set an explicit `PATH` that keeps the tools the build uses.
- **estimate:** the cached step's seconds times the rise in hit rate. Compare hits on two runs of the same commit from different events.
- **verify:** two runs of the same commit from a PR and from the default branch produce the same key and the second hits. Build output is identical, and the same tests run.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/content-based-cache-keys.md), [Mastra task env](https://github.com/mastra-ai/mastra/pull/14432), [Mastra global env](https://github.com/mastra-ai/mastra/pull/12720), [OpenAI](https://github.com/openai/codex/pull/19161)

### cache-real-output-paths: Cache the directories the build actually uses

- **applies when:** the cache step reports a hit but the next step still downloads or rebuilds, or a cache `path:` does not match the tool's real cache directory (check `npm config get cache`, `pip cache dir`, `go env GOCACHE GOMODCACHE`, Bazel's `--disk_cache` and `--repository_cache`).
- **how:** export the directory once as a step output or env var, and use that same value for the tool's config, the restore and the save. Give each job its own entry when contents differ. For a content-addressed cache, save under a per-run suffix with a stable restore prefix so it can grow. Let a cache service error fall back to a cold build.
- **estimate:** the gap between the step's seconds on a warm run and a cold run, which should become most of the cold time. Uber's build went from about 10 minutes on a first run to 1m24s on the second.
- **verify:** the second run's logs show no re-download of cached content, and the step's seconds drop over 10 runs. The same tests and lint results come out.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/cache-real-output-paths.md), [OpenAI](https://github.com/openai/codex/pull/16740), [Uber](https://github.com/uber/submitqueue/pull/59)

### persist-tool-analysis: Persist a tool's incremental analysis state

- **applies when:** a lint or build step's `run_s` is about the same on warm and cold runs while the tool has a cache (`eslint --cache`, golangci-lint, `tsc --incremental`, mypy, Ruff, Gradle's configuration cache), or CI passes `--skip-nx-cache` or a cache input includes the commit SHA (static).
- **how:** give the tool's cache directory its own `actions/cache@v4` entry, keyed on the lockfile, tool version and the tool's config, saved per revision with restore fallbacks. Give that job sole ownership of the key so another job cannot save first with incomplete state. For Nx or Turborepo, declare cached targets with their real inputs and outputs and remove the bypass flag. Keep publishing and other incompatible tasks on the uncached path. Encrypt Gradle configuration caches, since they can hold secrets.
- **estimate:** `run_s` of the step times the share of work the tool reuses. Shopify's repeated builds restored 12 of 12 tasks from cache. Measure one warm run.
- **verify:** compare the step's seconds over 10 runs before and after. Introduce a deliberate lint error in a changed file and confirm the job still goes red, and confirm the same task list runs.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/persist-tool-analysis.md), [OpenAI](https://github.com/openai/openai-go/pull/996), [Shopify](https://github.com/Shopify/cli/pull/8239), [Stripe](https://github.com/stripe/stripe-android/pull/11749)

### persist-compiler-cache: Persist compiler output between runs

- **applies when:** a Rust, C, C++ or native-compiling job's build step is over 2 minutes of `run_s` on runs where most sources are unchanged, and no compiler cache is saved between runs.
- **how:** turn on a compiler cache and persist it: `Swatinem/rust-cache@v2` for Rust, or `sccache` or `ccache` with its directory saved by `actions/cache@v4`, keyed on the toolchain version, target, flags and lockfile, with restore prefixes. Save only from trusted runs. Tag-triggered release builds can only restore from their own tag or the default branch, so also run the build on pushes to the default branch with the same key prefix to warm it.
- **estimate:** the compile step's seconds times the cache hit share that sccache or ccache reports in its stats. Measure one warm run.
- **verify:** the cache tool's stats show hits, and the compile step drops over 10 runs. The native tests still run against the built binaries.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/persist-compiler-cache.md), [OpenAI](https://github.com/openai/codex/pull/23358), [Ramp](https://github.com/ramp-public/ramp-cli/commit/4fec456d52fd03f85e1b96c94e075d22b5306c51)

### declare-cache-inputs: Declare the inputs and outputs of cached builds

- **applies when:** the repo uses a task cache (Turborepo, Nx, Gradle) and a build task misses after edits that leave its output unchanged, such as test files or Markdown, or task definitions have no `inputs` or `outputs` (static).
- **how:** declare each build task's real inputs (sources, package manifests, compiler config, generators, imported assets) and outputs, excluding files the build never reads. Give composite tasks their own declarations. Apply this to build and transform tasks. Do not add caching to test tasks that are not cached today.
- **estimate:** the task's seconds times the rise in hit rate. OpenAI's R8 transform went from 45 s to 3 s with outputs restored.
- **verify:** a docs-only or test-only change restores the build from cache, a source change rebuilds it, and the built artifact matches a cold build. The same tests run.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/declare-cache-inputs.md), [Mastra](https://github.com/mastra-ai/mastra/pull/14432), [OpenAI](https://github.com/openai/openai-java/pull/1014)

### disable-unused-caches: Stop writing caches that no later run restores

- **applies when:** a build tool writes a large local cache on every CI run and no step saves or restores that directory (static), for example Next.js `.next/cache` with no cache step.
- **how:** either persist the cache and measure its hit rate, or turn it off in CI. For Next.js, disable the Webpack disk cache when `process.env.CI` is set, in `next.config.js`. Keep it on for developer machines.
- **estimate:** the build step's seconds with the cache on minus with it off. DoorDash saved 3 minutes per run, with a Webpack cache that could exceed 5 to 10 GB.
- **verify:** compare the build step over 10 runs before and after. The build output and every check are unchanged.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/disable-unused-caches.md), [DoorDash](https://careersatdoordash.com/blog/how-doordash-slashed-web-developer-build-times/)

### cache-uploads-off-gate: Move optional cache uploads off the merge gate

- **applies when:** a required job spends over 15 s of its `setup_s` in a cache save or post-job cache upload whose result only later runs use. Read the "Post" cache step seconds from the job logs.
- **how:** in the required job, replace `actions/cache@v4` with `actions/cache/restore@v4`. Save from a job that is not required: either a job on pushes to the default branch that builds and saves, or a job that `needs:` the tests and saves after them. Give the save step a timeout and `continue-on-error: true`. Keep every test, required status and artifact dependency as it is.
- **estimate:** the save step's seconds on each required job's critical path. Linear's change took 42 s off the merge path of every API PR.
- **verify:** compare the required check's duration over 10 PR runs before and after, and confirm `cache_hit_pr` holds. The same required checks exist, with the same tests.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/cache-uploads-off-gate.md), [Linear](https://linear.app/now/ci-bottleneck-reworked#minimize-what%27s-on-the-critical-path), [OpenAI](https://github.com/openai/openai-cli/pull/602)

### prebuilt-toolchains: Install prebuilt packages and toolchains

- **applies when:** install logs show a source build for a dependency or tool that ships a compatible binary: pip "Building wheel for", `node-gyp rebuild`, Bazel compiling `protoc`, or `cargo install` of a tool with a release binary, taking over 30 s.
- **how:** pick dependency versions that ship wheels or binaries for every interpreter and platform in the matrix, or register the tool's prebuilt release as the toolchain. Verify checksums and keep a source build for platforms with no binary release.
- **estimate:** the compile seconds shown in the install log. OpenAI's HTTPX 2 job went from 10m42s to 2m12s and its Python 3.14 job from 8m37s to 1m53s, with two related changes. Uber's cold build went from about 84 s to 11 s.
- **verify:** compare `install_s` over 10 runs before and after. The same tests pass on every matrix leg, and generated output matches the source-built version.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/prebuilt-toolchains.md), [OpenAI wheels](https://github.com/openai/openai-python/pull/3573), [OpenAI move to uv](https://github.com/openai/openai-python/pull/3653), [Uber](https://github.com/uber/submitqueue/pull/165)

### pin-small-tool-install: Install a pinned tool release

- **applies when:** setup runs `brew update`, `brew upgrade`, `brew install` or `apt-get update` on every job just to obtain one CLI (static), with `tool_install_s` over 20 s.
- **how:** download one pinned release from the tool's releases page in a shared setup step, check it against its SHA-256 with `sha256sum -c` before running it, and record who updates the version.
- **estimate:** `tool_install_s` minus a few seconds of download, per job.
- **verify:** compare `tool_install_s` over 10 runs before and after. The tool prints the expected version, and the steps that use it pass the same way.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/pin-small-tool-install.md), [Stripe](https://github.com/stripe/stripe-ios/pull/7331)

### reuse-shared-test-inputs: Prepare shared test inputs once

- **applies when:** `duplicate_steps` shows matrix or fixture jobs downloading or building the same test inputs (specs, fixtures, published local packages) each, and that step is over 20 s per job.
- **how:** add one producer job that prepares the inputs and uploads them with `actions/upload-artifact@v4`. Consumer jobs `needs:` it and use `actions/download-artifact@v4`. Bind the artifact to the commit and platform, and never fall back to public packages when it is missing.
- **estimate:** per consumer, the repeated step's seconds minus the artifact download, minus the producer's run time added to the critical path. A very small download can stay in each job.
- **verify:** compare `pr_p50` and runner minutes over 10 runs before and after. Every matrix leg runs the same tests against the same input version.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/reuse-shared-test-inputs.md), [Mastra](https://github.com/mastra-ai/mastra/pull/18821), [Stripe](https://github.com/stripe/stripe-dotnet/pull/3340)

### image-pins: Pin the service image used by integration tests

- **applies when:** `services:` or a `docker-compose` file used by CI pulls `latest`, an untagged image or a rolling tag (static).
- **how:** pin each service image to an explicit version, and set up Renovate or Dependabot to propose updates so the pin has a refresh policy. Keep tests on every service version the project supports.
- **estimate:** small on its own. It stops surprise pulls when a rolling tag moves, and makes `keep-image-on-runner` caches hit. Count `image_pull_s` on runs where the tag changed.
- **verify:** the same integration tests pass on the pinned version, and `image_pull_s` stays steady over 10 runs.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/image-pins.md), [Mastra ClickHouse](https://github.com/mastra-ai/mastra/blob/f92e947a448a47515acf14df1eddc5fd5c36f424/stores/clickhouse/docker-compose.yaml), [Mastra Chroma](https://github.com/mastra-ai/mastra/blob/f92e947a448a47515acf14df1eddc5fd5c36f424/stores/chroma/docker-compose.yaml), [Mastra PR](https://github.com/mastra-ai/mastra/pull/14520)

### keep-image-on-runner: Stop downloading the test image on every build

- **applies when:** `image_pull_s` is over 60 s per job for the same image on every run.
- **how:** on GitHub-hosted runners, which start empty, cache the image. A job that builds it uses a persisted layer cache (see `reuse-docker-layers`). A job that only pulls a prebuilt image can `docker save` it to a tarball cached with `actions/cache@v4`, keyed on the Dockerfile and the lockfiles it copies in, and `docker load` it on a hit. Ramp kept the image in the local Docker cache of self-hosted runners, which needs runners outside the repo.
- **estimate:** `image_pull_s` minus the cache restore and `docker load` seconds. Ramp saved over a minute of an about fifteen-minute run.
- **verify:** compare `image_pull_s` over 10 runs before and after. A Dockerfile or lockfile change rebuilds the image, and the same tests run.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/keep-image-on-runner.md), [Ramp](https://builders.ramp.com/post/faster-python-tests-part-two)

### reuse-docker-layers: Reuse Docker build layers across runners

- **applies when:** a job builds a Docker image with no `cache-from` (static), or one workflow uses a layer cache and another builds the same Dockerfile without it, and the build step is over 60 s.
- **how:** build with `docker/setup-buildx-action@v3` and `docker/build-push-action@v6`, reading the GitHub Actions cache backend (or a registry cache on GHCR) and writing it only from trusted default-branch builds. Separate caches by architecture.
  ```yaml
  - uses: docker/setup-buildx-action@v3
  - uses: docker/build-push-action@v6
    with:
      cache-from: type=gha,scope=${{ runner.arch }}
      cache-to: ${{ github.event_name == 'push' && format('type=gha,mode=max,scope={0}', runner.arch) || '' }}
  ```
- **estimate:** the build step's seconds minus a warm build's seconds, where only the source copy layer and later layers rebuild. Measure one warm run.
- **verify:** compare the image build step over 10 runs before and after. A cold build and a warm build produce equivalent images, and the tests run against the warm image pass.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/reuse-docker-layers.md), [Spotify](https://github.com/spotify/confidence-resolver/pull/132), [Stripe](https://github.com/stripe/sync-engine-fork/pull/223)

### resilient-checkout: Bound stalled transfers and retry them

- **applies when:** `infra_fail_rate` from checkout is over 1%, or the p95 of `checkout_s` is more than 3 times its p50 on a critical-path job.
- **how:** set `GIT_HTTP_LOW_SPEED_LIMIT: 1000` and `GIT_HTTP_LOW_SPEED_TIME: 30` in the job's `env`, so a stalled transfer aborts after about 30 s instead of hanging. Pair it with a retry: give the checkout step an `id` and `continue-on-error: true`, then run a second `actions/checkout@v5` with `if: steps.<id>.outcome == 'failure'`. Linear also used a persistent git mirror on a sticky disk, which needs a runner provider and is out of scope here.
- **estimate:** (p95 minus p50 of `checkout_s`) times the share of runs that stall, plus a full rerun's seconds times the checkout share of `infra_fail_rate`.
- **verify:** compare the p95 of `checkout_s` and `infra_fail_rate` over 30 runs before and after. The checked-out commit is the same, and every job still runs.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/resilient-checkout.md), [Linear](https://linear.app/now/ci-bottleneck-reworked#make-checkout-more-resilient)

### clean-merged-pr-caches: Release obsolete PR cache space after merge

- **applies when:** `gh cache list` shows merged PRs' `refs/pull/<n>/merge` caches taking over 20% of the 10 GB quota, and `cache_hit_main` is under 90% because main's entries are being evicted.
- **how:** add a workflow on `pull_request_target` closed that runs only for merged PRs, checks out nothing, and deletes that PR's caches with `gh`.
  ```yaml
  on: { pull_request_target: { types: [closed] } }
  jobs:
    clean:
      if: github.event.pull_request.merged
      runs-on: ubuntu-latest
      permissions: { actions: write }
      steps:
        - run: gh cache list --ref "refs/pull/$PR/merge" --limit 100 --json id --jq '.[].id' | xargs -r -n1 gh cache delete
          env: { GH_TOKEN: "${{ github.token }}", GH_REPO: "${{ github.repository }}", PR: "${{ github.event.pull_request.number }}" }
  ```
- **estimate:** no direct saving per run. Count `install_s` times the rise in `cache_hit_main` and `cache_hit_pr` once main's entries stop being evicted.
- **verify:** after a merge, `gh cache list --ref refs/pull/<n>/merge` is empty and main's entries remain. Compare `cache_hit_pr` over 10 runs before and after. No check changes.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/clean-merged-pr-caches.md), [OpenAI](https://github.com/openai/codex-security/pull/1997)

### compact-cache-contents: Archive the current build's cache entries

- **applies when:** a build cache entry grows run after run (`gh cache list` sizes) and its restore or save takes over 30 s, while the build uses only a small part of it.
- **how:** save only the entries the current build produces or reads. Import the restored entries into the tool's normal cache, collect this run's entries into a fresh directory, and save that directory instead of the accumulated history.
- **estimate:** (restore seconds plus save seconds) times (1 minus new size divided by old size). OpenAI's retained payload fell from 3,326,734,224 bytes to 123,910,919 bytes.
- **verify:** compare cache size and restore and save seconds over 10 runs before and after, and confirm the build's hit rate holds. The same tests run.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/compact-cache-contents.md), [OpenAI](https://github.com/openai/openai-java/pull/1203)

### cache-baseline-results: Reuse exact baseline analysis results

- **applies when:** a PR job builds or analyzes the base revision to compare against it, such as an API diff, size check or dead-code report (static: a checkout or build of the base SHA inside a PR job), and that job is on the `critical_path`.
- **how:** cache the baseline's result keyed on the exact base commit, toolchain version and build recipe. Have default-branch runs save it and PR runs restore it. Validate the artifact before use, rebuild the baseline when the entry is missing or invalid, and always analyze the PR's own revision.
- **estimate:** the baseline build's seconds times the baseline cache hit rate. Stripe's API check went from about 14 to about 4 minutes with a cached baseline.
- **verify:** compare the job over 10 PR runs before and after. The comparison reports the same findings as with a fresh baseline on the same PRs, and a PR with a deliberate API break still fails.
- **risk:** medium
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/cache-baseline-results.md), [Stripe](https://github.com/stripe/stripe-ios/pull/7336)

### cache-nix-store: Reuse a snapshot of the build store

- **applies when:** the workflow builds with Nix and `setup_share` is over 30%, spent rebuilding dependencies that change only with `flake.lock` and the packaging files.
- **how:** cache the Nix store as one snapshot per build variant, keyed on a hash of `flake.lock` and the dependency files plus the commit, restoring the newest snapshot with that prefix. `nix-community/cache-nix-action` does this on `actions/cache`. Save only from trusted runs and watch the 10 GB quota.
- **estimate:** the dependency build's seconds minus restore and save time. Shopify's restore took 0.5 to 2 minutes and save 0.3 to 1.6, against a median PR run of 61.8 minutes before its seven changes and 4.7 minutes on a warm run after.
- **verify:** compare `setup_s` over 10 runs before and after. The same checks run, and a `flake.lock` change rebuilds.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/cache-nix-store.md), [Shopify](https://github.com/Shopify/tecnix/pull/74)

### prebuild-runner-images: Bake stable dependencies into runner images

- **applies when:** `duplicate_steps` shows the same OS package or toolchain install (`apt-get install`, large versioned downloads) in more than two jobs, each over 5 s of `tool_install_s`.
- **how:** build a small, pinned CI image with those packages from a Dockerfile, publish it to a registry, refresh it on a schedule for security patches, and run jobs in it with `container:`. Keep secrets and mutable build outputs out of the image. For large versioned downloads, bake a prefetch store keyed by exact URL or version, and download fresh when a version changes.
- **estimate:** `tool_install_s` times the jobs that repeat it, minus `image_pull_s`. Linear's shards spent 7 to 8 s on one apt package, and the image with two other changes cut per-shard setup from 110 to 140 s down to 67 to 73 s.
- **verify:** compare `setup_s` over 10 runs before and after. The same jobs and tests run, and the image's pinned versions match what the install used to produce.
- **risk:** medium
- **mode:** report-only (needs-infra)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/prebuild-runner-images.md), [Anthropic](https://github.com/oven-sh/bun/pull/29568), [Linear caching](https://linear.app/now/ci-bottleneck-reworked#don%27t-cache-when-it%27s-faster-to-rebuild), [Linear CI image](https://linear.app/now/ci-bottleneck-reworked#preinstall-shared-dependencies-in-the-ci-image)

### warm-image-caches: Warm reusable caches while building the image

- **applies when:** `setup_share` is over 40% because jobs install dependencies and build before any test, and jobs already start from a prebuilt image.
- **how:** in the image build, install dependencies and run the app and test suite once, so the cache files they write are in the image. Rebuild the image on each push to the default branch, and keep jobs working from a cold start.
- **estimate:** `install_s` plus the first-run cache warm-up seconds, minus any extra `image_pull_s`.
- **verify:** compare `setup_s` over 10 runs before and after. Tests run the same way from the image and from a cold start.
- **risk:** medium
- **mode:** report-only (needs-infra)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/warm-image-caches.md), [Ramp](https://builders.ramp.com/post/why-we-built-our-background-agent)

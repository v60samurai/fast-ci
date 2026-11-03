# Queue and runner speed

Here the time goes before the project's commands run or into hardware that is too slow for them: jobs wait for a machine, CPU-bound work runs on small or emulated runners, or Windows file IO drags. Most fixes here cost money, need infrastructure or change the merge gate, so most entries are report-only.

### faster-runners: Move jobs to faster runners

- **applies when:** `wait_s` p50 is over 30 s on any job in a PR run, or the `critical_path` job is CPU-bound (CPU saturated for most of `run_s`, `setup_share` under 30%) after the cheaper setup, cache and test fixes are done.
- **how:** Benchmark the same workflow on a faster runner, and move every job, not only the slow one, because a 5-second job that waits 10 minutes for a machine is a 10-minute job. Owen moved to Blacksmith with one line per job (`runs-on: blacksmith-4vcpu-ubuntu-2204`), which took his queue from 11 minutes to 8 seconds. StarSling, Vercel CI and boat.dev are alternatives, as are GitHub's larger runners. Match operating system, architecture and event mix, and compare matched windows of runs. Some fork or event runs may need the old label.
- **estimate:** two numbers, both in the report. Seconds saved per PR: the sum of `wait_s` along the critical path minus about 8 s, plus `run_s` times 0.34 to 0.5 on CPU-bound jobs (Linear measured 34% faster jobs, Ramp about 50% from a faster CPU, Mastra 29m 56s to 5m 06s p95 together with test fixes). Monthly cost: billed minutes per month (`runs_per_day` times 30 times the summed job minutes per run) times the provider's current per-minute price, set against the current bill. Owen's bill went from 230 to 4,300 dollars a month.
- **verify:** for the user, after they decide: compare p50 and p95 `pr_p50` and `wait_s` over matched windows of at least 20 runs before and after, with the same jobs, test counts and required checks.
- **risk:** low
- **mode:** report-only (paid-runner)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/faster-runners.md), [Linear](https://linear.app/now/ci-bottleneck-reworked#upgraded-infrastructure-and-tooling), [Mastra](https://starsling.dev/customers/mastra), [Mastra](https://github.com/mastra-ai/mastra/pull/13466), [OpenAI](https://github.com/openai/codex/pull/24952), [Ramp](https://builders.ramp.com/post/faster-python-tests-part-two), [Owen Gretzinger](https://x.com/owengretzinger/status/2116291924219060319)

### native-architecture-builds: Build each architecture on native runners

- **applies when:** a static pattern shows arm64 images or binaries built on an x86 runner through emulation (`docker/setup-qemu-action` with `platforms: linux/amd64,linux/arm64` in a `docker/build-push-action` step), and that job's `run_s` is over 300 s.
- **how:** Run one matrix job per platform on a matching runner, push each image by digest, and add a final job that merges the digests into one manifest with `docker buildx imagetools create`, only after every platform succeeds. Drop the QEMU step. In a public repo, GitHub's arm64 runners (`ubuntu-24.04-arm`) are free, so the user can approve it at no cost. In a private repo they are paid.
  ```yaml
  strategy:
    matrix:
      include:
        - { platform: linux/amd64, runner: ubuntu-24.04 }
        - { platform: linux/arm64, runner: ubuntu-24.04-arm }
  runs-on: ${{ matrix.runner }}
  ```
- **estimate:** the emulated job's `run_s` times about 0.88, from Spotify's 2 hours 28 minutes under QEMU against about 17 minutes native (8.7 times faster), minus the manifest job's `setup_s`. For a private repo, add the monthly cost of the arm64 minutes at GitHub's current per-minute price.
- **verify:** for the user, after they decide: compare the build workflow's wall time over 3 runs before and after, and confirm the manifest lists every platform it listed before.
- **risk:** low
- **mode:** report-only (paid-runner)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/native-architecture-builds.md), [Spotify](https://github.com/spotify/confidence-resolver/pull/479), [Stripe](https://github.com/stripe/sync-engine-fork/pull/212)

### dev-drive-io: Move Windows build IO onto a Dev Drive

- **applies when:** a job runs on `windows-*`, its `run_s` is over 1.5 times the same steps on Linux, and the steps are heavy on file IO (compiles, package caches, Bazel or Cargo output).
- **how:** Create a Dev Drive at the start of the job with `samypr100/setup-dev-drive@v3` (MIT), then point build output, package caches and temp files at it through the `DEV_DRIVE` variable it sets (`CARGO_HOME`, `CARGO_TARGET_DIR`, `TEMP`, `TMP`, the Bazel output base).
- **estimate:** the Windows job's IO-heavy step seconds times about 0.3, from OpenAI's traced Bazel test step (16m22s to 12m05s and 16m48s to 11m08s, one sample each), minus about 10 to 20 s to create the drive.
- **verify:** compare p50 Windows job `run_s` over 10 runs before and after on the same runner type, and confirm the same tests run with the same count.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/dev-drive-io.md), [OpenAI](https://github.com/openai/codex/pull/31357)

### merge-without-retest: Merge without re-testing against the latest main, except migrations

- **applies when:** branch protection requires branches to be up to date (`gh api repos/{owner}/{repo}/branches/{branch}/protection` shows `required_status_checks.strict: true`), merges to the default branch run over 3 a day, and most PR runs come from updating the branch after another merge.
- **how:** For the user to decide: turn off the up-to-date rule, require the full suite to pass on the default branch before every deploy, and make database migrations conflict in Git (Ramp committed `migrations/migration-hash.txt`, a hash of every migration filename) so two PRs that add migrations cannot both merge without an update.
- **estimate:** the up-to-date reruns per PR times `pr_p50`. Ramp's average time to merge went from over an hour to 12 minutes, the length of its suite.
- **verify:** for the user, after they decide: compare time from approval to merge over 20 PRs before and after, and confirm the default branch run before deploy stays required and goes red on a broken merge.
- **risk:** medium
- **mode:** report-only (merge-gate)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/merge-without-retest.md), [Ramp](https://builders.ramp.com/post/merge-queues)

### git-checkout-service: Serve checkouts from pre-warmed repository clones

- **applies when:** `checkout_s` is over 60 s on most jobs after `blobless-history` and `fetch-needed-history` are in place, and many jobs clone the same large repository.
- **how:** For the user to decide: run a service that keeps a bare clone per repository warm (updated on push, with a fetch every few minutes behind it) and serve jobs from it, such as a Git mirror on self-hosted runners. Let a job ask for the latest state when it needs it, since the mirror can lag.
- **estimate:** `checkout_s` minus about 1 s, on every job. Uber's clients get a full checkout in under 500 ms in place of 10 to 15 minute cold clones.
- **verify:** for the user, after they decide: compare p50 `checkout_s` over 10 runs before and after, and confirm every job checks out the exact commit SHA it ran before.
- **risk:** medium
- **mode:** report-only (needs-infra)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/git-checkout-service.md), [Uber](https://www.uber.com/us/en/blog/gitfarm-as-a-service/)

### prioritize-speculative-builds: Build the merge-queue speculations most likely to be needed

- **applies when:** the repo lands changes through a merge queue (a workflow triggered on `merge_group`), and over 10% of queue runs are cancelled or rebuilt when an earlier change lands.
- **how:** For the user to decide: in the merge queue, build changes that touch different targets at the same time, and run first the speculative builds most likely to decide a change, using predicted build times and pass rates. Tune the threshold from past queue data, because one set too high makes changes wait longer under load.
- **estimate:** the queue's p95 wait times 0.3 to 0.45, from Uber's P95 waiting time falling 44.67% for Go (33.69 to 18.64 minutes), 33.32% for iOS and 31.66% for Android, with CPU hours down 35% to 52%.
- **verify:** for the user, after they decide: compare p95 queue wait and cancelled queue runs over 2 weeks before and after, and confirm every merged change still passed the queue's required checks.
- **risk:** high
- **mode:** report-only (merge-gate)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/prioritize-speculative-builds.md), [Uber](https://www.uber.com/us/en/blog/slashing-ci-costs-at-uber/)

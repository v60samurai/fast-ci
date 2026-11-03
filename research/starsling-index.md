# StarSling CI playbooks index

Raw harvest of https://starsling.dev/ci-playbooks, read from https://starsling.dev/llms.txt and the `.md` version of every technique, category and company page on 2026-11-03. 141 techniques, 254 implementations, 10 company playbooks (Anthropic, DoorDash, Linear, Mastra, OpenAI, Ramp, Shopify, Spotify, Stripe, Uber).

The refresh path in `SKILL.md` diffs a new harvest against the `### <slug>` headings below. Each entry lists the fast-ci category file it lives in, the categories StarSling itself tags it with (most techniques carry no tag), the companies that implemented it, and every source link.

## Pages read

- https://starsling.dev/llms.txt
- https://starsling.dev/ci-playbooks.md
- https://starsling.dev/ci-playbooks/categories/agent-volume.md
- https://starsling.dev/ci-playbooks/categories/caching.md
- https://starsling.dev/ci-playbooks/categories/cost.md
- https://starsling.dev/ci-playbooks/categories/parallel.md
- https://starsling.dev/ci-playbooks/categories/runners.md
- https://starsling.dev/ci-playbooks/categories/selection.md
- https://starsling.dev/ci-playbooks/categories/slow-tests.md
- https://starsling.dev/ci-playbooks/categories/unnecessary.md
- https://starsling.dev/ci-playbooks/anthropic.md
- https://starsling.dev/ci-playbooks/doordash.md
- https://starsling.dev/ci-playbooks/linear.md
- https://starsling.dev/ci-playbooks/mastra.md
- https://starsling.dev/ci-playbooks/openai.md
- https://starsling.dev/ci-playbooks/ramp.md
- https://starsling.dev/ci-playbooks/shopify.md
- https://starsling.dev/ci-playbooks/spotify.md
- https://starsling.dev/ci-playbooks/stripe.md
- https://starsling.dev/ci-playbooks/uber.md
- the technique pages, one per entry below

## Techniques

### advisory-before-required

- title: Start an agent as a suggestion and put it on autopilot once it has proven reliable
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: Linear
- page: https://starsling.dev/ci-playbooks/techniques/advisory-before-required.md
- implementations:
  - Linear: Start an agent as a suggestion and put it on autopilot once it has proven reliable (https://starsling.dev/ci-playbooks/linear#advisory-before-required): https://linear.app/now/how-we-use-linear-agent-at-linear

### agent-conformance-suite

- title: Give agents a conformance suite to test against
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/agent-conformance-suite.md
- implementations:
  - OpenAI: Give agents a conformance suite to test against (https://starsling.dev/ci-playbooks/openai#agent-conformance-suite): https://openai.com/index/scaling-git-at-openai/

### agent-dead-code-sweep

- title: Have an agent prove code is unused, then delete it in reviewed batches
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/agent-dead-code-sweep.md
- implementations:
  - OpenAI: Have an agent prove code is unused, then delete it in reviewed batches (https://starsling.dev/ci-playbooks/openai#agent-dead-code-sweep): https://developers.openai.com/blog/maintaining-software-with-the-gpt-6-family

### agent-import-cycles

- title: Let an agent break import cycles and make the app load lazily
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: Slow tests
- companies: Ramp
- page: https://starsling.dev/ci-playbooks/techniques/agent-import-cycles.md
- implementations:
  - Ramp: Let an agent break import cycles and make the app load lazily (https://starsling.dev/ci-playbooks/ramp#agent-import-cycles): https://claude.com/customers/ramp-boris-office-hours

### agent-metric-loop

- title: Let an agent iterate against one CI metric
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: Shopify
- page: https://starsling.dev/ci-playbooks/techniques/agent-metric-loop.md
- implementations:
  - Shopify: Let an agent iterate against one CI metric (https://starsling.dev/ci-playbooks/shopify#agent-metric-loop): https://shopify.engineering/autoresearch

### agent-migration-recipes

- title: Constrain agent migrations with repeatable validation
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: Spotify, Stripe, Uber
- page: https://starsling.dev/ci-playbooks/techniques/agent-migration-recipes.md
- implementations:
  - Spotify: Find every consumer from lineage data and open one agent pull request per repository (https://starsling.dev/ci-playbooks/spotify#lineage-scoped-agent-migrations): https://engineering.atspotify.com/2026/4/background-coding-agents-dataset-migrations-honk-part-4
  - Stripe: Upgrade the JDK in bounded pull requests computed from the build graph (https://starsling.dev/ci-playbooks/stripe#bounded-jdk-upgrades): https://stripe.dev/blog/modern-java-at-stripe-language-upgrades-as-a-service
  - Uber: Migrate a test framework with a recipe that keeps only passing targets (https://starsling.dev/ci-playbooks/uber#recipe-gated-test-migration): https://www.uber.com/us/en/blog/junit-migration/

### agent-per-ticket

- title: Give every open ticket its own agent
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/agent-per-ticket.md
- implementations:
  - OpenAI: Give every open ticket its own agent (https://starsling.dev/ci-playbooks/openai#agent-per-ticket): https://openai.com/index/open-source-codex-orchestration-symphony/

### agent-readable-lint-feedback

- title: Give agents actionable lint feedback
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: OpenAI, Spotify
- page: https://starsling.dev/ci-playbooks/techniques/agent-readable-lint-feedback.md
- implementations:
  - OpenAI: Write lint errors that tell the agent how to fix them (https://starsling.dev/ci-playbooks/openai#remediation-lints): https://openai.com/index/harness-engineering/
  - Spotify: Give agents the same lint feedback as developers (https://starsling.dev/ci-playbooks/spotify#lint-guardrails-for-agents): https://engineering.atspotify.com/2026/6/code-with-claude-coding-is-no-longer-the-constraint

### agent-readable-test-output

- title: Print a few lines from the test harness and log the rest to a file
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: Anthropic
- page: https://starsling.dev/ci-playbooks/techniques/agent-readable-test-output.md
- implementations:
  - Anthropic: Print a few lines from the test harness and log the rest to a file (https://starsling.dev/ci-playbooks/anthropic#agent-readable-test-output): https://www.anthropic.com/research/building-c-compiler

### agent-shepherds-merge

- title: Give an agent the last mile: watch CI, rebase and retry flaky checks
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/agent-shepherds-merge.md
- implementations:
  - OpenAI: Give an agent the last mile: watch CI, rebase and retry flaky checks (https://starsling.dev/ci-playbooks/openai#agent-shepherds-merge): https://openai.com/index/open-source-codex-orchestration-symphony/

### automated-pr-review

- title: Run an agent review on pull requests
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: Linear, Ramp, Uber
- page: https://starsling.dev/ci-playbooks/techniques/automated-pr-review.md
- implementations:
  - Linear: Have a coding agent review every pull request before a human approves (https://starsling.dev/ci-playbooks/linear#agent-reviews-every-pr): https://linear.app/now/how-we-use-linear-agent-at-linear
  - Ramp: Build the review bot on the same agent that writes the code (https://starsling.dev/ci-playbooks/ramp#review-bot-on-agent): https://claude.com/customers/ramp-boris-office-hours
  - Uber: Run an AI reviewer on every commit and post the comments that pass a quality filter (https://starsling.dev/ci-playbooks/uber#ai-review-in-ci): https://www.uber.com/us/en/blog/ureview/

### avoid-duplicate-builds

- title: Remove repeated build steps
- fast-ci file: `playbook/unnecessary.md`
- StarSling categories: Compute waste, Unnecessary work
- companies: Mastra, OpenAI, Spotify
- page: https://starsling.dev/ci-playbooks/techniques/avoid-duplicate-builds.md
- implementations:
  - Mastra: Build release artifacts after the final version change (https://starsling.dev/ci-playbooks/mastra#release-build-once): https://github.com/mastra-ai/mastra/pull/22380
  - OpenAI: Let the package lifecycle build once (https://starsling.dev/ci-playbooks/openai#avoid-lifecycle-rebuilds): https://github.com/openai/codex-security/pull/397
  - Spotify: Let test and lint stages reuse the build stage (https://starsling.dev/ci-playbooks/spotify#docker-stage-reuse): https://github.com/spotify/confidence-resolver/pull/355
  - Spotify: Stop rebuilding just to export artifacts (https://starsling.dev/ci-playbooks/spotify#drop-artifact-extraction): https://github.com/spotify/confidence-resolver/pull/81

### avoid-duplicate-validation

- title: Run shared validation once
- fast-ci file: `playbook/unnecessary.md`
- StarSling categories: Compute waste, Unnecessary work
- companies: DoorDash, Mastra, Stripe
- page: https://starsling.dev/ci-playbooks/techniques/avoid-duplicate-validation.md
- implementations:
  - DoorDash: Run platform-independent checks on one matrix leg (https://starsling.dev/ci-playbooks/doordash#checks-on-one-leg): https://github.com/doordash-oss/agentic-orchestrator/pull/139
  - Mastra: Avoid repeating CI checks in a version bot’s commit hook (https://starsling.dev/ci-playbooks/mastra#version-hooks): https://github.com/mastra-ai/mastra/pull/2952
  - Stripe: Run snapshot checks once in a dedicated lane (https://starsling.dev/ci-playbooks/stripe#delegate-snapshots-once): https://github.com/stripe/stripe-ios/pull/7332
  - Stripe: Stop invoking tests twice through overlapping tasks (https://starsling.dev/ci-playbooks/stripe#remove-duplicate-tests): https://github.com/stripe/stripe-android/pull/13033

### avoid-emulator-build-contention

- title: Build before starting the emulator
- fast-ci file: `playbook/unnecessary.md`
- StarSling categories: Unnecessary work
- companies: Stripe
- page: https://starsling.dev/ci-playbooks/techniques/avoid-emulator-build-contention.md
- implementations:
  - Stripe: Build before starting the emulator (https://starsling.dev/ci-playbooks/stripe#avoid-emulator-build-contention): https://github.com/stripe/stripe-react-native/pull/2111

### avoid-incidental-test-dns

- title: Use a loopback address for local mock servers
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: none
- companies: Stripe
- page: https://starsling.dev/ci-playbooks/techniques/avoid-incidental-test-dns.md
- implementations:
  - Stripe: Use a loopback address for local mock servers (https://starsling.dev/ci-playbooks/stripe#avoid-incidental-test-dns): https://github.com/stripe/stripe-python/pull/1849

### balance-test-shards

- title: Balance test work across shards
- fast-ci file: `playbook/parallel.md`
- StarSling categories: Parallelization and sharding, Slow tests
- companies: Linear, OpenAI, Ramp, Stripe
- page: https://starsling.dev/ci-playbooks/techniques/balance-test-shards.md
- implementations:
  - Linear: Balance test files before buying more shards (https://starsling.dev/ci-playbooks/linear#balance-the-shards): https://linear.app/now/ci-bottleneck-reworked#balance-work-the-way-the-test-runner-sees-it
  - OpenAI: Split long test jobs into balanced shards (https://starsling.dev/ci-playbooks/openai#balanced-shards): https://github.com/openai/codex/pull/22408
  - Ramp: Pack tests onto workers so they finish together (https://starsling.dev/ci-playbooks/ramp#pack-tests-by-duration): https://builders.ramp.com/post/faster-python-tests-part-two
  - Stripe: Balance shards and keep a catch-all for new tests (https://starsling.dev/ci-playbooks/stripe#rebalance-and-cover-shards): https://github.com/stripe/stripe-ios/pull/7333

### batch-historical-restores

- title: Restore a historical test set in one operation
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/batch-historical-restores.md
- implementations:
  - OpenAI: Restore a historical test set in one operation (https://starsling.dev/ci-playbooks/openai#batch-historical-restores): https://github.com/openai/openai-go/pull/1152

### batch-semantic-validation

- title: Validate shared declarations once without losing file boundaries
- fast-ci file: `playbook/unnecessary.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/batch-semantic-validation.md
- implementations:
  - OpenAI: Validate shared declarations once without losing file boundaries (https://starsling.dev/ci-playbooks/openai#batch-semantic-validation): https://github.com/openai/openai-ruby/pull/333

### blobless-history

- title: Keep full history and download old blobs on demand
- fast-ci file: `playbook/caching.md`
- StarSling categories: Unnecessary work
- companies: Mastra
- page: https://starsling.dev/ci-playbooks/techniques/blobless-history.md
- implementations:
  - Mastra: Keep full history and download old blobs on demand (https://starsling.dev/ci-playbooks/mastra#blobless-history): https://github.com/mastra-ai/mastra/pull/21298

### bound-job-runtime

- title: Put time limits on jobs that can hang
- fast-ci file: `playbook/cost.md`
- StarSling categories: Compute waste
- companies: Anthropic, Mastra, Shopify, Spotify
- page: https://starsling.dev/ci-playbooks/techniques/bound-job-runtime.md
- implementations:
  - Anthropic: Bound flaky job runtime (https://starsling.dev/ci-playbooks/anthropic#flaky-job-timeouts): https://claude.com/resources/articles/agentic-coding-is-straining-ci-heres-how-we-scaled-test-impact-analysis-at-anthropic
  - Mastra: Bound integration jobs that can hang (https://starsling.dev/ci-playbooks/mastra#bounded-jobs): https://github.com/mastra-ai/mastra/blob/f92e947a448a47515acf14df1eddc5fd5c36f424/.github/workflows/test-combined-stores.yml https://github.com/mastra-ai/mastra/pull/14098
  - Shopify: Bound a test job that can hang (https://starsling.dev/ci-playbooks/shopify#bound-hung-tests): https://github.com/Shopify/job-iteration/pull/717
  - Spotify: Cap hung test jobs with timeouts (https://starsling.dev/ci-playbooks/spotify#job-timeouts): https://github.com/spotify/confidence-sdk-flutter/pull/72

### bounded-agent-execution

- title: Bound agent execution and retries
- fast-ci file: `playbook/cost.md`
- StarSling categories: Compute waste
- companies: DoorDash, Spotify, Stripe
- page: https://starsling.dev/ci-playbooks/techniques/bounded-agent-execution.md
- implementations:
  - DoorDash: Give every agent in a CI gate a soft and a hard timeout (https://starsling.dev/ci-playbooks/doordash#bounded-agent-timeouts): https://careersatdoordash.com/blog/doordash-built-an-ai-code-reviewer-engineers-actually-listen-to/
  - Spotify: Cap an agent's turns and session retries (https://starsling.dev/ci-playbooks/spotify#agent-session-limits): https://engineering.atspotify.com/2025/11/context-engineering-background-coding-agents-part-2
  - Stripe: Auto-apply test fixes and cap agent CI rounds (https://starsling.dev/ci-playbooks/stripe#bound-agent-ci-rounds): https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents-part-2

### build-once-for-shards

- title: Build once and share the output with test shards
- fast-ci file: `playbook/parallel.md`
- StarSling categories: none
- companies: OpenAI, Stripe
- page: https://starsling.dev/ci-playbooks/techniques/build-once-for-shards.md
- implementations:
  - OpenAI: Build once, test on every shard (https://starsling.dev/ci-playbooks/openai#build-once): https://github.com/openai/codex/pull/23358
  - Stripe: Build once and hand the artifact to every shard (https://starsling.dev/ci-playbooks/stripe#build-once-for-shards): https://github.com/stripe/stripe-react-native/pull/2137

### build-only-consumed-inputs

- title: Build only what the test or analysis consumes
- fast-ci file: `playbook/unnecessary.md`
- StarSling categories: Unnecessary work
- companies: Stripe, Uber
- page: https://starsling.dev/ci-playbooks/techniques/build-only-consumed-inputs.md
- implementations:
  - Stripe: Build only what the analysis consumes (https://starsling.dev/ci-playbooks/stripe#build-only-analysis-inputs): https://github.com/stripe/stripe-ios/pull/7336
  - Uber: Build only the services each test consumes (https://starsling.dev/ci-playbooks/uber#declare-test-build-inputs): https://github.com/uber/submitqueue/pull/439
  - Uber: Build test dependencies in the test lane (https://starsling.dev/ci-playbooks/uber#build-test-targets): https://github.com/uber/submitqueue/pull/701

### cache-baseline-results

- title: Reuse exact baseline analysis results
- fast-ci file: `playbook/caching.md`
- StarSling categories: none
- companies: Stripe
- page: https://starsling.dev/ci-playbooks/techniques/cache-baseline-results.md
- implementations:
  - Stripe: Reuse exact baseline analysis results (https://starsling.dev/ci-playbooks/stripe#cache-baseline-results): https://github.com/stripe/stripe-ios/pull/7336

### cache-nix-store

- title: Reuse a snapshot of the build store
- fast-ci file: `playbook/caching.md`
- StarSling categories: Caching and setup
- companies: Shopify
- page: https://starsling.dev/ci-playbooks/techniques/cache-nix-store.md
- implementations:
  - Shopify: Reuse a snapshot of the build store (https://starsling.dev/ci-playbooks/shopify#cache-nix-store): https://github.com/Shopify/tecnix/pull/74

### cache-python-environments

- title: Restore compatible Python environments
- fast-ci file: `playbook/caching.md`
- StarSling categories: Caching and setup
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/cache-python-environments.md
- implementations:
  - OpenAI: Restore compatible Python environments (https://starsling.dev/ci-playbooks/openai#cache-python-environments): https://github.com/openai/openai-python/pull/3573 https://github.com/openai/openai-python/pull/3653

### cache-real-output-paths

- title: Cache the directories the build actually uses
- fast-ci file: `playbook/caching.md`
- StarSling categories: Caching and setup
- companies: OpenAI, Uber
- page: https://starsling.dev/ci-playbooks/techniques/cache-real-output-paths.md
- implementations:
  - OpenAI: Cache the directory the build actually uses (https://starsling.dev/ci-playbooks/openai#align-cache-paths): https://github.com/openai/codex/pull/16740
  - Uber: Cache the paths the build actually writes (https://starsling.dev/ci-playbooks/uber#repair-cache-contract): https://github.com/uber/submitqueue/pull/59

### cache-tool-downloads

- title: Reuse downloaded tools across runs
- fast-ci file: `playbook/caching.md`
- StarSling categories: Caching and setup
- companies: Anthropic, Linear, Shopify, Stripe
- page: https://starsling.dev/ci-playbooks/techniques/cache-tool-downloads.md
- implementations:
  - Anthropic: Cache compiled lint tools between runs (https://starsling.dev/ci-playbooks/anthropic#cache-lint-tools): https://github.com/oven-sh/bun/pull/38459
  - Linear: Cache pinned tool and matrix downloads (https://starsling.dev/ci-playbooks/linear#cache-tool-downloads): https://github.com/linear/linear/pull/1130
  - Shopify: Reuse browser downloads and keep the repair step (https://starsling.dev/ci-playbooks/shopify#cache-browser-downloads): https://github.com/Shopify/checkout-kit/pull/972
  - Stripe: Reuse a downloaded toolchain (https://starsling.dev/ci-playbooks/stripe#reuse-downloaded-toolchains): https://github.com/stripe/stripe-android/pull/12402

### cache-uploads-off-gate

- title: Move optional cache uploads off the merge gate
- fast-ci file: `playbook/caching.md`
- StarSling categories: none
- companies: Linear, OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/cache-uploads-off-gate.md
- implementations:
  - Linear: Let optional cache writes finish after the merge gate (https://starsling.dev/ci-playbooks/linear#cache-writes-off-the-merge-path): https://linear.app/now/ci-bottleneck-reworked#minimize-what%27s-on-the-critical-path
  - OpenAI: Keep cache uploads outside required test jobs (https://starsling.dev/ci-playbooks/openai#restore-without-saving): https://github.com/openai/openai-cli/pull/602

### cache-write-ownership

- title: Give shared cache writes deliberate ownership
- fast-ci file: `playbook/caching.md`
- StarSling categories: none
- companies: Anthropic, OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/cache-write-ownership.md
- implementations:
  - Anthropic: Save shared caches only from the default branch (https://starsling.dev/ci-playbooks/anthropic#cache-write-hygiene): https://github.com/anthropics/buffa/pull/288
  - OpenAI: Give concurrent cache writers deliberate ownership (https://starsling.dev/ci-playbooks/openai#isolate-cache-writers): https://github.com/openai/codex/pull/18366

### cancel-superseded-runs

- title: Cancel superseded pull request runs
- fast-ci file: `playbook/cost.md`
- StarSling categories: Agent PR volume, Compute waste, Unnecessary work
- companies: Anthropic, Mastra, Stripe, Uber
- page: https://starsling.dev/ci-playbooks/techniques/cancel-superseded-runs.md
- implementations:
  - Anthropic: Cancel superseded runs, never on main (https://starsling.dev/ci-playbooks/anthropic#cancel-superseded-runs): https://github.com/anthropics/anthropic-sdk-python/commit/c8e75ece9e407966ed077a8e4e924e7ebd041c71
  - Mastra: Cancel obsolete runs using the correct event identity (https://starsling.dev/ci-playbooks/mastra#cancel-superseded): https://github.com/mastra-ai/mastra/pull/14432
  - Stripe: Cancel superseded pull request runs (https://starsling.dev/ci-playbooks/stripe#cancel-only-obsolete-validation): https://github.com/stripe/stripe-ios/pull/7337
  - Uber: Cancel superseded pull request runs (https://starsling.dev/ci-playbooks/uber#cancel-superseded-runs): https://github.com/uber/baseweb/pull/5407

### check-cleanup-at-test-end

- title: Check for leaks after this test cleans up
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: none
- companies: Uber
- page: https://starsling.dev/ci-playbooks/techniques/check-cleanup-at-test-end.md
- implementations:
  - Uber: Check for leaks after this test cleans up (https://starsling.dev/ci-playbooks/uber#check-cleanup-at-test-end): https://github.com/cadence-workflow/cadence/pull/7969

### checkout-before-cache

- title: Restore dependencies after their manifest exists
- fast-ci file: `playbook/caching.md`
- StarSling categories: Caching and setup
- companies: Uber
- page: https://starsling.dev/ci-playbooks/techniques/checkout-before-cache.md
- implementations:
  - Uber: Restore dependencies after their manifest exists (https://starsling.dev/ci-playbooks/uber#checkout-before-cache): https://github.com/uber/tchannel-go/pull/935

### classify-merged-prs

- title: Classify every merged pull request by the work it contains
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: Spotify
- page: https://starsling.dev/ci-playbooks/techniques/classify-merged-prs.md
- implementations:
  - Spotify: Classify every merged pull request by the work it contains (https://starsling.dev/ci-playbooks/spotify#classify-merged-prs): https://engineering.atspotify.com/2026/9/ai-changed-how-spotify-builds-what-we-learned-and-fixed-about-quality-at-higher-velocity

### clean-merged-pr-caches

- title: Release obsolete PR cache space after merge
- fast-ci file: `playbook/caching.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/clean-merged-pr-caches.md
- implementations:
  - OpenAI: Release obsolete PR cache space after merge (https://starsling.dev/ci-playbooks/openai#clean-merged-pr-caches): https://github.com/openai/codex-security/pull/1997

### compact-cache-contents

- title: Archive the current build’s cache entries
- fast-ci file: `playbook/caching.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/compact-cache-contents.md
- implementations:
  - OpenAI: Archive the current build’s cache entries (https://starsling.dev/ci-playbooks/openai#compact-cache-contents): https://github.com/openai/openai-java/pull/1203

### compile-historical-api-probes

- title: Give historical API probes a precise validation contract
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/compile-historical-api-probes.md
- implementations:
  - OpenAI: Give historical API probes a precise validation contract (https://starsling.dev/ci-playbooks/openai#compile-historical-api-probes): https://github.com/openai/openai-go/pull/1152

### compile-test-sources-once

- title: Transpile test sources once per run
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/compile-test-sources-once.md
- implementations:
  - OpenAI: Transpile test sources once per run (https://starsling.dev/ci-playbooks/openai#compile-test-sources-once): https://github.com/openai/openai-node/pull/2713

### content-based-cache-keys

- title: Keep unrelated environment changes out of cache keys
- fast-ci file: `playbook/caching.md`
- StarSling categories: Caching and setup
- companies: Mastra, OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/content-based-cache-keys.md
- implementations:
  - Mastra: Keep runtime API keys out of unrelated build hashes (https://starsling.dev/ci-playbooks/mastra#task-cache-env): https://github.com/mastra-ai/mastra/pull/14432
  - Mastra: Remove branch identity from content cache keys (https://starsling.dev/ci-playbooks/mastra#global-cache-env): https://github.com/mastra-ai/mastra/pull/12720
  - OpenAI: Remove unrelated environment churn from cache inputs (https://starsling.dev/ci-playbooks/openai#stabilize-cache-environment): https://github.com/openai/codex/pull/19161

### coordinate-test-setup

- title: Build the test database once for all workers
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: Parallelization and sharding, Slow tests
- companies: Ramp
- page: https://starsling.dev/ci-playbooks/techniques/coordinate-test-setup.md
- implementations:
  - Ramp: Build the test database once for all workers (https://starsling.dev/ci-playbooks/ramp#coordinate-test-setup): https://builders.ramp.com/post/faster-python-tests

### declare-cache-inputs

- title: Declare the inputs and outputs of cached builds
- fast-ci file: `playbook/caching.md`
- StarSling categories: Caching and setup
- companies: Mastra, OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/declare-cache-inputs.md
- implementations:
  - Mastra: Make build cache keys describe the build (https://starsling.dev/ci-playbooks/mastra#build-inputs): https://github.com/mastra-ai/mastra/pull/14432
  - OpenAI: Declare every input and output of expensive transforms (https://starsling.dev/ci-playbooks/openai#cache-transform-outputs): https://github.com/openai/openai-java/pull/1014

### defer-draft-work

- title: Wait until a draft is ready for expensive checks
- fast-ci file: `playbook/unnecessary.md`
- StarSling categories: Agent PR volume, Compute waste, Unnecessary work
- companies: Shopify, Uber
- page: https://starsling.dev/ci-playbooks/techniques/defer-draft-work.md
- implementations:
  - Shopify: Run expensive checks when a draft becomes ready (https://starsling.dev/ci-playbooks/shopify#defer-draft-work): https://github.com/Shopify/checkout-kit/pull/284
  - Uber: Wait until a draft is ready for expensive checks (https://starsling.dev/ci-playbooks/uber#draft-gating): https://github.com/uber/submitqueue/pull/180

### defer-heavy-validation

- title: Move selected heavy checks after merge
- fast-ci file: `playbook/selection.md`
- StarSling categories: Agent PR volume, Test selection
- companies: OpenAI, Shopify
- page: https://starsling.dev/ci-playbooks/techniques/defer-heavy-validation.md
- implementations:
  - OpenAI: Run the heavy matrix after merge (https://starsling.dev/ci-playbooks/openai#defer-duplicate-validation): https://github.com/openai/codex/pull/16072
  - Shopify: Move heavyweight checks after merge, by decision (https://starsling.dev/ci-playbooks/shopify#schedule-heavy-validation): https://github.com/Shopify/tecnix/pull/74

### dev-drive-io

- title: Move Windows build IO onto a Dev Drive
- fast-ci file: `playbook/runners.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/dev-drive-io.md
- implementations:
  - OpenAI: Move Windows build IO onto a Dev Drive (https://starsling.dev/ci-playbooks/openai#dev-drive-io): https://github.com/openai/codex/pull/31357

### disable-unused-caches

- title: Stop writing caches that no later run restores
- fast-ci file: `playbook/caching.md`
- StarSling categories: Caching and setup, Compute waste
- companies: DoorDash
- page: https://starsling.dev/ci-playbooks/techniques/disable-unused-caches.md
- implementations:
  - DoorDash: Turn off a build cache that CI never restores (https://starsling.dev/ci-playbooks/doordash#drop-unrestored-build-cache): https://careersatdoordash.com/blog/how-doordash-slashed-web-developer-build-times/

### doc-gardening-agent

- title: Run a recurring agent that fixes stale documentation
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/doc-gardening-agent.md
- implementations:
  - OpenAI: Run a recurring agent that fixes stale documentation (https://starsling.dev/ci-playbooks/openai#doc-gardening-agent): https://openai.com/index/harness-engineering/

### drop-duplicate-image-workflow

- title: Fold a duplicate image workflow into the shared build
- fast-ci file: `playbook/unnecessary.md`
- StarSling categories: none
- companies: Spotify
- page: https://starsling.dev/ci-playbooks/techniques/drop-duplicate-image-workflow.md
- implementations:
  - Spotify: Fold a duplicate image workflow into the shared build (https://starsling.dev/ci-playbooks/spotify#drop-duplicate-image-workflow): https://github.com/spotify/confidence-resolver/pull/132

### example-auto-runner

- title: Run every example in auto mode and check each log against its source
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/example-auto-runner.md
- implementations:
  - OpenAI: Run every example in auto mode and check each log against its source (https://starsling.dev/ci-playbooks/openai#example-auto-runner): https://developers.openai.com/blog/skills-agents-sdk

### failures-as-work-queue

- title: Write every failure to a file and let fixer agents work through it by area
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: Anthropic
- page: https://starsling.dev/ci-playbooks/techniques/failures-as-work-queue.md
- implementations:
  - Anthropic: Write every failure to a file and let fixer agents work through it by area (https://starsling.dev/ci-playbooks/anthropic#failures-as-work-queue): https://bun.sh/blog/bun-in-rust

### faster-release-linker

- title: Link release builds with a faster linker
- fast-ci file: `playbook/cost.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/faster-release-linker.md
- implementations:
  - OpenAI: Link release builds with a faster linker (https://starsling.dev/ci-playbooks/openai#faster-release-linker): https://github.com/openai/codex/pull/27315

### faster-runners

- title: Move bottlenecked jobs to faster runners
- fast-ci file: `playbook/runners.md`
- StarSling categories: Queue and runner speed
- companies: Linear, Mastra, OpenAI, Ramp
- page: https://starsling.dev/ci-playbooks/techniques/faster-runners.md
- implementations:
  - Linear: Benchmark the same job on faster hardware (https://starsling.dev/ci-playbooks/linear#faster-runners): https://linear.app/now/ci-bottleneck-reworked#upgraded-infrastructure-and-tooling
  - Mastra: Move the slowest test workflow onto StarSling runners (https://starsling.dev/ci-playbooks/mastra#starsling-runners): https://starsling.dev/customers/mastra https://github.com/mastra-ai/mastra/pull/13466
  - OpenAI: Put the slowest job on a faster runner (https://starsling.dev/ci-playbooks/openai#faster-runner): https://github.com/openai/codex/pull/24952
  - Ramp: Move a CPU-bound test suite to a faster CPU (https://starsling.dev/ci-playbooks/ramp#faster-cpu): https://builders.ramp.com/post/faster-python-tests-part-two

### fetch-needed-history

- title: Fetch only the repository history a job needs
- fast-ci file: `playbook/caching.md`
- StarSling categories: Unnecessary work
- companies: Linear, Mastra, OpenAI, Stripe
- page: https://starsling.dev/ci-playbooks/techniques/fetch-needed-history.md
- implementations:
  - Linear: Give each checkout only the files and history it uses (https://starsling.dev/ci-playbooks/linear#fetch-only-what-each-job-needs): https://linear.app/now/ci-bottleneck-reworked#fetch-only-what-each-job-needs
  - Mastra: Fetch only the release history the job consumes (https://starsling.dev/ci-playbooks/mastra#shallow-checkout): https://github.com/mastra-ai/mastra/blob/f92e947a448a47515acf14df1eddc5fd5c36f424/.github/workflows/npm-publish.yml https://github.com/mastra-ai/mastra/pull/14432
  - OpenAI: Check out only the history the job reads (https://starsling.dev/ci-playbooks/openai#shallow-checkout): https://github.com/openai/frontier-evals/pull/53
  - Stripe: Fetch the comparison, not every branch (https://starsling.dev/ci-playbooks/stripe#fetch-needed-history): https://github.com/stripe/stripe-ios/pull/7331

### finish-fixtures-before-timeout

- title: Complete the fixture before its timeout fires
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: Slow tests
- companies: Uber
- page: https://starsling.dev/ci-playbooks/techniques/finish-fixtures-before-timeout.md
- implementations:
  - Uber: Complete the fixture before its timeout fires (https://starsling.dev/ci-playbooks/uber#finish-fixtures-before-timeout): https://github.com/cadence-workflow/cadence/pull/8290

### first-responder-agent

- title: Put an agent on call to post an evidence-grounded analysis on every CI and CD failure
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: Anthropic
- page: https://starsling.dev/ci-playbooks/techniques/first-responder-agent.md
- implementations:
  - Anthropic: Put an agent on call to post an evidence-grounded analysis on every CI and CD failure (https://starsling.dev/ci-playbooks/anthropic#first-responder-agent): https://claude.com/resources/articles/ai-ci-cd-on-call

### flakiness-gate-before-blocking

- title: Prove a new test is stable before it joins the blocking suite
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: none
- companies: Shopify
- page: https://starsling.dev/ci-playbooks/techniques/flakiness-gate-before-blocking.md
- implementations:
  - Shopify: Prove a new test is stable before it joins the blocking suite (https://starsling.dev/ci-playbooks/shopify#flakiness-gate-before-blocking): https://shopify.engineering/mobile-e2e-testing

### flaky-tests

- title: Fix flaky tests from CI history
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/flaky-tests.md
- implementations:
  - OpenAI: Fix flaky tests from CI history (https://starsling.dev/ci-playbooks/openai#flaky-tests): https://developers.openai.com/blog/maintaining-software-with-the-gpt-6-family#other-ideas-to-try

### gate-agent-evaluations

- title: Replay fixed evaluations before merging agent changes
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: DoorDash, Stripe
- page: https://starsling.dev/ci-playbooks/techniques/gate-agent-evaluations.md
- implementations:
  - DoorDash: Gate agent changes on a simulated, fixture-backed eval run (https://starsling.dev/ci-playbooks/doordash#simulated-eval-gate): https://careersatdoordash.com/blog/building-ask-doordash-part-three-evaluation/
  - Stripe: Replay a golden dataset on every pull request (https://starsling.dev/ci-playbooks/stripe#golden-dataset-gate): https://stripe.dev/blog/microservice-testing-with-apache-spark

### gate-irrelevant-events

- title: Reject irrelevant events before allocating runners
- fast-ci file: `playbook/unnecessary.md`
- StarSling categories: Agent PR volume, Unnecessary work
- companies: Mastra, OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/gate-irrelevant-events.md
- implementations:
  - Mastra: Do not start a runner for irrelevant comments (https://starsling.dev/ci-playbooks/mastra#comment-gates): https://github.com/mastra-ai/mastra/pull/22381
  - OpenAI: Keep metadata edits from restarting source validation (https://starsling.dev/ci-playbooks/openai#isolate-metadata-edits): https://github.com/openai/codex-security/pull/1708
  - OpenAI: Skip irrelevant jobs before allocating runners (https://starsling.dev/ci-playbooks/openai#gate-before-runner): https://github.com/openai/openai-agents-python/pull/5264

### git-checkout-service

- title: Serve checkouts from pre-warmed repository clones
- fast-ci file: `playbook/runners.md`
- StarSling categories: Unnecessary work
- companies: Uber
- page: https://starsling.dev/ci-playbooks/techniques/git-checkout-service.md
- implementations:
  - Uber: Serve checkouts from pre-warmed repository clones (https://starsling.dev/ci-playbooks/uber#git-checkout-service): https://www.uber.com/us/en/blog/gitfarm-as-a-service/

### guided-review-order

- title: Lead a large pull request with its core change and keep formatting noise out of the review
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: Linear
- page: https://starsling.dev/ci-playbooks/techniques/guided-review-order.md
- implementations:
  - Linear: Lead a large pull request with its core change and keep formatting noise out of the review (https://starsling.dev/ci-playbooks/linear#guided-review-order): https://linear.app/now/code-review-should-be-fast

### image-pins

- title: Pin the service image used by integration tests
- fast-ci file: `playbook/caching.md`
- StarSling categories: none
- companies: Mastra
- page: https://starsling.dev/ci-playbooks/techniques/image-pins.md
- implementations:
  - Mastra: Pin the service image used by integration tests (https://starsling.dev/ci-playbooks/mastra#image-pins): https://github.com/mastra-ai/mastra/blob/f92e947a448a47515acf14df1eddc5fd5c36f424/stores/clickhouse/docker-compose.yaml https://github.com/mastra-ai/mastra/blob/f92e947a448a47515acf14df1eddc5fd5c36f424/stores/chroma/docker-compose.yaml https://github.com/mastra-ai/mastra/pull/14520

### independent-agent-review

- title: Review agent changes with independent reviewers
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: Anthropic, DoorDash, OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/independent-agent-review.md
- implementations:
  - Anthropic: Review each agent change with reviewers that see only the diff (https://starsling.dev/ci-playbooks/anthropic#adversarial-review-agents): https://bun.sh/blog/bun-in-rust
  - DoorDash: Review pull requests with a scout and deep reviewers (https://starsling.dev/ci-playbooks/doordash#staged-review-agent): https://careersatdoordash.com/blog/doordash-built-an-ai-code-reviewer-engineers-actually-listen-to/
  - OpenAI: Let agents review agents until the reviewers are satisfied (https://starsling.dev/ci-playbooks/openai#agent-review-loop): https://openai.com/index/harness-engineering/

### install-consumed-tools

- title: Install tools only in the jobs that need them
- fast-ci file: `playbook/unnecessary.md`
- StarSling categories: Unnecessary work
- companies: Mastra, Stripe
- page: https://starsling.dev/ci-playbooks/techniques/install-consumed-tools.md
- implementations:
  - Mastra: Install only what the change detector needs (https://starsling.dev/ci-playbooks/mastra#discovery-install): https://github.com/mastra-ai/mastra/blob/f92e947a448a47515acf14df1eddc5fd5c36f424/.github/workflows/prebuild.yml https://github.com/mastra-ai/mastra/pull/12246
  - Stripe: Install tools only where they are used (https://starsling.dev/ci-playbooks/stripe#install-only-consumed-tools): https://github.com/stripe/stripe-android/pull/10184

### isolated-agent-checkouts

- title: Give each parallel agent its own checkout and a claimed task
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: Anthropic
- page: https://starsling.dev/ci-playbooks/techniques/isolated-agent-checkouts.md
- implementations:
  - Anthropic: Give each parallel agent its own checkout and a claimed task (https://starsling.dev/ci-playbooks/anthropic#isolated-agent-checkouts): https://www.anthropic.com/research/building-c-compiler

### isolated-parallel-tests

- title: Isolate state before running tests in parallel
- fast-ci file: `playbook/parallel.md`
- StarSling categories: Parallelization and sharding, Slow tests
- companies: DoorDash, Ramp, Shopify, Stripe, Uber
- page: https://starsling.dev/ci-playbooks/techniques/isolated-parallel-tests.md
- implementations:
  - DoorDash: Run isolated end-to-end journeys in parallel (https://starsling.dev/ci-playbooks/doordash#parallel-e2e): https://github.com/doordash-oss/agentic-orchestrator/pull/139
  - Ramp: Give parallel test workers more databases (https://starsling.dev/ci-playbooks/ramp#test-databases): https://builders.ramp.com/post/faster-python-tests-part-two
  - Shopify: Isolate tests before adding workers (https://starsling.dev/ci-playbooks/shopify#isolate-before-parallel): https://github.com/Shopify/cli/pull/7309
  - Stripe: Give concurrent tests their own state (https://starsling.dev/ci-playbooks/stripe#isolate-parallel-test-state): https://github.com/stripe/sync-engine-fork/pull/124
  - Uber: Give concurrent suites their own services (https://starsling.dev/ci-playbooks/uber#isolate-test-services): https://github.com/uber/submitqueue/pull/41

### keep-agent-ci-current

- title: Validate every new agent commit
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: Anthropic, Shopify
- page: https://starsling.dev/ci-playbooks/techniques/keep-agent-ci-current.md
- implementations:
  - Anthropic: Run the existing test suite on every agent commit so new commits cannot break existing code (https://starsling.dev/ci-playbooks/anthropic#ci-blocks-agent-regressions): https://www.anthropic.com/research/building-c-compiler
  - Shopify: Re-run CI on every new head and act only on that head's verdict (https://starsling.dev/ci-playbooks/shopify#retrigger-ci-on-new-head): https://shopify.engineering/river-vulnerability-remediation

### keep-image-on-runner

- title: Stop downloading the test image on every build
- fast-ci file: `playbook/caching.md`
- StarSling categories: Caching and setup
- companies: Ramp
- page: https://starsling.dev/ci-playbooks/techniques/keep-image-on-runner.md
- implementations:
  - Ramp: Stop downloading the test image on every build (https://starsling.dev/ci-playbooks/ramp#keep-image-on-runner): https://builders.ramp.com/post/faster-python-tests-part-two

### lint-before-the-push

- title: Fix lint before the push reaches CI
- fast-ci file: `playbook/unnecessary.md`
- StarSling categories: none
- companies: Stripe
- page: https://starsling.dev/ci-playbooks/techniques/lint-before-the-push.md
- implementations:
  - Stripe: Fix lint before the push reaches CI (https://starsling.dev/ci-playbooks/stripe#lint-before-the-push): https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents-part-2

### lint-without-types

- title: Keep the lint rule, remove its type-graph dependency
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: none
- companies: Linear
- page: https://starsling.dev/ci-playbooks/techniques/lint-without-types.md
- implementations:
  - Linear: Keep the lint rule, remove its type-graph dependency (https://starsling.dev/ci-playbooks/linear#lint-without-types): https://linear.app/now/ci-bottleneck-reworked#lint-without-the-type-checker

### matrix-by-supported-runtime

- title: Test supported runtimes concurrently
- fast-ci file: `playbook/parallel.md`
- StarSling categories: Parallelization and sharding, Slow tests, Unnecessary work
- companies: Stripe
- page: https://starsling.dev/ci-playbooks/techniques/matrix-by-supported-runtime.md
- implementations:
  - Stripe: Test supported runtimes concurrently (https://starsling.dev/ci-playbooks/stripe#matrix-by-supported-runtime): https://github.com/stripe/stripe-dotnet/pull/3340

### measure-gc-memory-budget

- title: Measure the analyzer’s garbage-collection budget
- fast-ci file: `playbook/cost.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/measure-gc-memory-budget.md
- implementations:
  - OpenAI: Measure the analyzer’s garbage-collection budget (https://starsling.dev/ci-playbooks/openai#measure-gc-memory-budget): https://github.com/openai/openai-go/pull/996

### merge-without-retest

- title: Merge without re-testing against the latest main, except migrations
- fast-ci file: `playbook/runners.md`
- StarSling categories: none
- companies: Ramp
- page: https://starsling.dev/ci-playbooks/techniques/merge-without-retest.md
- implementations:
  - Ramp: Merge without re-testing against the latest main, except migrations (https://starsling.dev/ci-playbooks/ramp#merge-without-retest): https://builders.ramp.com/post/merge-queues

### minimal-merge-gates

- title: Keep blocking merge gates minimal and follow flakes with a rerun
- fast-ci file: `playbook/selection.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/minimal-merge-gates.md
- implementations:
  - OpenAI: Keep blocking merge gates minimal and follow flakes with a rerun (https://starsling.dev/ci-playbooks/openai#minimal-merge-gates): https://openai.com/index/harness-engineering/

### mock-external-dependencies

- title: Keep unit tests independent of slow services
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: Slow tests
- companies: OpenAI, Uber
- page: https://starsling.dev/ci-playbooks/techniques/mock-external-dependencies.md
- implementations:
  - OpenAI: Mock the slow dependency (https://starsling.dev/ci-playbooks/openai#mock-dependencies): https://developers.openai.com/blog/maintaining-software-with-the-gpt-6-family#other-ideas-to-try
  - Uber: Keep unit tests independent of database servers (https://starsling.dev/ci-playbooks/uber#separate-unit-dependencies): https://github.com/cadence-workflow/cadence/pull/6800

### native-architecture-builds

- title: Build each architecture on native runners
- fast-ci file: `playbook/runners.md`
- StarSling categories: Queue and runner speed
- companies: Spotify, Stripe
- page: https://starsling.dev/ci-playbooks/techniques/native-architecture-builds.md
- implementations:
  - Spotify: Build arm64 on native arm64 runners (https://starsling.dev/ci-playbooks/spotify#native-arm-runners): https://github.com/spotify/confidence-resolver/pull/479
  - Stripe: Build each container architecture natively (https://starsling.dev/ci-playbooks/stripe#native-container-builds): https://github.com/stripe/sync-engine-fork/pull/212

### native-lint-tools

- title: Use a faster native linter without losing rules
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: none
- companies: Linear, Spotify
- page: https://starsling.dev/ci-playbooks/techniques/native-lint-tools.md
- implementations:
  - Linear: Run native lint without losing unsupported rules (https://starsling.dev/ci-playbooks/linear#oxlint): https://linear.app/now/ci-bottleneck-reworked#lint-without-the-type-checker
  - Spotify: Lint with one fast native tool (https://starsling.dev/ci-playbooks/spotify#ruff-lint): https://github.com/spotify/luigi/pull/3395

### native-type-checking

- title: Accelerate required type checking with a native compiler
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: none
- companies: Linear
- page: https://starsling.dev/ci-playbooks/techniques/native-type-checking.md
- implementations:
  - Linear: Accelerate required type checking with a native compiler (https://starsling.dev/ci-playbooks/linear#native-type-checking): https://linear.app/now/ci-bottleneck-reworked#upgraded-infrastructure-and-tooling

### nested-lockfile

- title: Key nested installs from their own lockfile
- fast-ci file: `playbook/caching.md`
- StarSling categories: Caching and setup
- companies: Mastra
- page: https://starsling.dev/ci-playbooks/techniques/nested-lockfile.md
- implementations:
  - Mastra: Key nested installs from their own lockfile (https://starsling.dev/ci-playbooks/mastra#nested-lockfile): https://github.com/mastra-ai/mastra/pull/14432

### normalize-unordered-results

- title: Make unordered results deterministic before comparing
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: none
- companies: Uber
- page: https://starsling.dev/ci-playbooks/techniques/normalize-unordered-results.md
- implementations:
  - Uber: Make unordered results deterministic before comparing (https://starsling.dev/ci-playbooks/uber#normalize-unordered-results): https://github.com/cadence-workflow/cadence/pull/6831

### one-machine-build

- title: Build on one machine when the long pole leaves it idle
- fast-ci file: `playbook/parallel.md`
- StarSling categories: none
- companies: Anthropic
- page: https://starsling.dev/ci-playbooks/techniques/one-machine-build.md
- implementations:
  - Anthropic: Build on one machine when the long pole leaves it idle (https://starsling.dev/ci-playbooks/anthropic#one-machine-build): https://github.com/oven-sh/bun/pull/37733

### overlap-independent-setup

- title: Overlap independent setup with explicit joins
- fast-ci file: `playbook/parallel.md`
- StarSling categories: Parallelization and sharding
- companies: Stripe
- page: https://starsling.dev/ci-playbooks/techniques/overlap-independent-setup.md
- implementations:
  - Stripe: Overlap independent setup with explicit joins (https://starsling.dev/ci-playbooks/stripe#overlap-independent-setup): https://github.com/stripe/sync-engine-fork/pull/223

### package-on-available-runner

- title: Package other architectures on the runner that is free
- fast-ci file: `playbook/parallel.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/package-on-available-runner.md
- implementations:
  - OpenAI: Package other architectures on the runner that is free (https://starsling.dev/ci-playbooks/openai#package-on-available-runner): https://github.com/openai/codex/pull/28001

### package-once

- title: Package once, and build full installers after merge
- fast-ci file: `playbook/selection.md`
- StarSling categories: Agent PR volume, Compute waste, Test selection, Unnecessary work
- companies: DoorDash
- page: https://starsling.dev/ci-playbooks/techniques/package-once.md
- implementations:
  - DoorDash: Package once, and build full installers after merge (https://starsling.dev/ci-playbooks/doordash#package-once): https://github.com/doordash-oss/agentic-orchestrator/pull/139

### parallel-build-targets

- title: Build every target framework in one parallel call
- fast-ci file: `playbook/parallel.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/parallel-build-targets.md
- implementations:
  - OpenAI: Build every target framework in one parallel call (https://starsling.dev/ci-playbooks/openai#parallel-build-targets): https://github.com/openai/openai-dotnet/pull/1009

### parallel-cleanup

- title: Clean up independent test resources concurrently
- fast-ci file: `playbook/parallel.md`
- StarSling categories: Parallelization and sharding
- companies: Mastra
- page: https://starsling.dev/ci-playbooks/techniques/parallel-cleanup.md
- implementations:
  - Mastra: Clean up independent test resources concurrently (https://starsling.dev/ci-playbooks/mastra#parallel-cleanup): https://github.com/mastra-ai/mastra/pull/13965

### parallel-independent-checks

- title: Run independent checks in parallel
- fast-ci file: `playbook/parallel.md`
- StarSling categories: Parallelization and sharding
- companies: Anthropic, DoorDash, Mastra, OpenAI, Shopify, Uber
- page: https://starsling.dev/ci-playbooks/techniques/parallel-independent-checks.md
- implementations:
  - Anthropic: Run build-free checks without waiting for the build (https://starsling.dev/ci-playbooks/anthropic#lint-off-build-path): https://github.com/oven-sh/bun/pull/34682
  - DoorDash: Run lint beside the build, as its own step (https://starsling.dev/ci-playbooks/doordash#lint-beside-build): https://careersatdoordash.com/blog/how-doordash-slashed-web-developer-build-times/
  - Mastra: Run independent lint and formatting checks together (https://starsling.dev/ci-playbooks/mastra#parallel-quality): https://github.com/mastra-ai/mastra/pull/18428
  - OpenAI: Run independent checks alongside each other (https://starsling.dev/ci-playbooks/openai#parallel-independent-checks): https://github.com/openai/openai-cli/pull/489
  - Shopify: Let tests start without waiting for lint (https://starsling.dev/ci-playbooks/shopify#remove-false-dependency): https://github.com/Shopify/tecnix/pull/74
  - Uber: Run independent checks at the same time (https://starsling.dev/ci-playbooks/uber#parallel-independent-checks): https://www.uber.com/us/en/blog/how-we-halved-go-monorepo-ci-build-time/

### parallel-packaging

- title: Compress release artifacts in parallel
- fast-ci file: `playbook/parallel.md`
- StarSling categories: Parallelization and sharding
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/parallel-packaging.md
- implementations:
  - OpenAI: Compress release artifacts in parallel (https://starsling.dev/ci-playbooks/openai#parallel-packaging): https://github.com/openai/codex/pull/27855

### parallel-test-framework

- title: Move unit tests to a parallel-by-default framework, gated on ten clean runs
- fast-ci file: `playbook/parallel.md`
- StarSling categories: Parallelization and sharding, Slow tests
- companies: DoorDash
- page: https://starsling.dev/ci-playbooks/techniques/parallel-test-framework.md
- implementations:
  - DoorDash: Move unit tests to a parallel-by-default framework, gated on ten clean runs (https://starsling.dev/ci-playbooks/doordash#parallel-test-framework): https://careersatdoordash.com/blog/doordash-using-cursor-to-accelerate-migration-to-swift-testing/

### parallel-test-packages

- title: Run independent test packages concurrently
- fast-ci file: `playbook/parallel.md`
- StarSling categories: Parallelization and sharding, Slow tests
- companies: Anthropic, Spotify, Uber
- page: https://starsling.dev/ci-playbooks/techniques/parallel-test-packages.md
- implementations:
  - Anthropic: Run independent test packages concurrently (https://starsling.dev/ci-playbooks/anthropic#parallel-crates): https://github.com/oven-sh/bun/pull/39218
  - Spotify: Run the slowest test environment in parallel workers (https://starsling.dev/ci-playbooks/spotify#pytest-xdist): https://github.com/spotify/luigi/pull/3398
  - Uber: Let the test runner schedule independent packages (https://starsling.dev/ci-playbooks/uber#parallel-package-tests): https://github.com/cadence-workflow/cadence/pull/6801

### per-stage-automation

- title: Set each stage of the issue pipeline to auto or manual
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: Mastra
- page: https://starsling.dev/ci-playbooks/techniques/per-stage-automation.md
- implementations:
  - Mastra: Set each stage of the issue pipeline to auto or manual (https://starsling.dev/ci-playbooks/mastra#per-stage-automation): https://mastra.ai/blog/announcing-mastra-factory-beta

### persist-compiler-cache

- title: Persist compiler output between runs
- fast-ci file: `playbook/caching.md`
- StarSling categories: Caching and setup
- companies: OpenAI, Ramp
- page: https://starsling.dev/ci-playbooks/techniques/persist-compiler-cache.md
- implementations:
  - OpenAI: Cache the cross-compile producer’s objects (https://starsling.dev/ci-playbooks/openai#cache-cross-compile-objects): https://github.com/openai/codex/pull/23358
  - Ramp: Persist the compiler cache and warm it from the default branch (https://starsling.dev/ci-playbooks/ramp#cache-the-compiler): https://github.com/ramp-public/ramp-cli/commit/4fec456d52fd03f85e1b96c94e075d22b5306c51

### persist-tool-analysis

- title: Persist a tool’s incremental analysis state
- fast-ci file: `playbook/caching.md`
- StarSling categories: Caching and setup
- companies: OpenAI, Shopify, Stripe
- page: https://starsling.dev/ci-playbooks/techniques/persist-tool-analysis.md
- implementations:
  - OpenAI: Persist the tool’s analysis state separately (https://starsling.dev/ci-playbooks/openai#persist-tool-analysis): https://github.com/openai/openai-go/pull/996
  - Shopify: Let the build tool reuse unchanged work (https://starsling.dev/ci-playbooks/shopify#enable-tool-cache): https://github.com/Shopify/cli/pull/8239
  - Stripe: Cache Gradle configuration as well as dependencies (https://starsling.dev/ci-playbooks/stripe#cache-gradle-configuration): https://github.com/stripe/stripe-android/pull/11749

### pin-small-tool-install

- title: Install a pinned tool release
- fast-ci file: `playbook/caching.md`
- StarSling categories: none
- companies: Stripe
- page: https://starsling.dev/ci-playbooks/techniques/pin-small-tool-install.md
- implementations:
  - Stripe: Install a pinned tool release (https://starsling.dev/ci-playbooks/stripe#pin-small-tool-install): https://github.com/stripe/stripe-ios/pull/7331

### poll-readiness

- title: Wait for observable readiness instead of sleeping
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: Slow tests
- companies: Mastra, Stripe, Uber
- page: https://starsling.dev/ci-playbooks/techniques/poll-readiness.md
- implementations:
  - Mastra: Poll the condition the test actually needs (https://starsling.dev/ci-playbooks/mastra#poll-indexing): https://github.com/mastra-ai/mastra/pull/13808
  - Mastra: Wait until the database answers a query (https://starsling.dev/ci-playbooks/mastra#query-readiness): https://github.com/mastra-ai/mastra/pull/14520
  - Stripe: Wait for readiness with a bounded poll (https://starsling.dev/ci-playbooks/stripe#wait-for-observable-state): https://github.com/stripe/sync-engine-fork/pull/124
  - Uber: Wait for the connection the test actually uses (https://starsling.dev/ci-playbooks/uber#protocol-readiness): https://github.com/uber/submitqueue/pull/64

### prebuild-runner-images

- title: Bake stable dependencies into runner images
- fast-ci file: `playbook/caching.md`
- StarSling categories: Caching and setup, Unnecessary work
- companies: Anthropic, Linear
- page: https://starsling.dev/ci-playbooks/techniques/prebuild-runner-images.md
- implementations:
  - Anthropic: Bake versioned build downloads into the runner image (https://starsling.dev/ci-playbooks/anthropic#prefetch-build-inputs): https://github.com/oven-sh/bun/pull/29568
  - Linear: Bake stable system dependencies into the CI image (https://starsling.dev/ci-playbooks/linear#preinstall-in-the-ci-image): https://linear.app/now/ci-bottleneck-reworked#don%27t-cache-when-it%27s-faster-to-rebuild https://linear.app/now/ci-bottleneck-reworked#preinstall-shared-dependencies-in-the-ci-image

### prebuilt-toolchains

- title: Install prebuilt packages and toolchains
- fast-ci file: `playbook/caching.md`
- StarSling categories: Caching and setup
- companies: OpenAI, Uber
- page: https://starsling.dev/ci-playbooks/techniques/prebuilt-toolchains.md
- implementations:
  - OpenAI: Install prebuilt packages (https://starsling.dev/ci-playbooks/openai#prebuilt-packages): https://github.com/openai/openai-python/pull/3573 https://github.com/openai/openai-python/pull/3653
  - Uber: Download the compiler your build depends on (https://starsling.dev/ci-playbooks/uber#prebuilt-toolchain): https://github.com/uber/submitqueue/pull/165

### precompile-test-imports

- title: Precompile repeated imports in disposable test copies
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/precompile-test-imports.md
- implementations:
  - OpenAI: Precompile repeated imports in disposable test copies (https://starsling.dev/ci-playbooks/openai#precompile-test-imports): https://github.com/openai/codex-security/pull/2036

### prioritize-speculative-builds

- title: Build the merge-queue speculations most likely to be needed
- fast-ci file: `playbook/runners.md`
- StarSling categories: none
- companies: Uber
- page: https://starsling.dev/ci-playbooks/techniques/prioritize-speculative-builds.md
- implementations:
  - Uber: Build the merge-queue speculations most likely to be needed (https://starsling.dev/ci-playbooks/uber#prioritize-speculative-builds): https://www.uber.com/us/en/blog/slashing-ci-costs-at-uber/

### profile-build-hotspots

- title: Use build profiles to remove expensive work
- fast-ci file: `playbook/unnecessary.md`
- StarSling categories: none
- companies: OpenAI, Stripe
- page: https://starsling.dev/ci-playbooks/techniques/profile-build-hotspots.md
- implementations:
  - OpenAI: Remove the compiler work a profile identifies (https://starsling.dev/ci-playbooks/openai#profile-compiler-hotspots): https://github.com/openai/codex/pull/16630
  - Stripe: Remove expensive dependencies from the hot build graph (https://starsling.dev/ci-playbooks/stripe#profile-build-dependencies): https://github.com/sorbet/sorbet/pull/10124

### profile-release-linking

- title: Measure the cost of the release build profile
- fast-ci file: `playbook/cost.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/profile-release-linking.md
- implementations:
  - OpenAI: Measure the cost of the release build profile (https://starsling.dev/ci-playbooks/openai#profile-release-linking): https://github.com/openai/codex/pull/23710

### rank-by-minutes

- title: Rank fixes by the minutes they save
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/rank-by-minutes.md
- implementations:
  - OpenAI: Rank fixes by the minutes they save (https://starsling.dev/ci-playbooks/openai#rank-by-minutes): https://developers.openai.com/blog/maintaining-software-with-the-gpt-6-family#other-ideas-to-try

### reduce-test-process-overhead

- title: Reduce repeated process and build-graph startup
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: Slow tests
- companies: Anthropic, OpenAI, Stripe
- page: https://starsling.dev/ci-playbooks/techniques/reduce-test-process-overhead.md
- implementations:
  - Anthropic: Run reliable test files in one parallel invocation per shard (https://starsling.dev/ci-playbooks/anthropic#batch-test-processes): https://github.com/oven-sh/bun/pull/36175
  - OpenAI: Run tests in fewer processes (https://starsling.dev/ci-playbooks/openai#fewer-processes): https://github.com/openai/openai-python/pull/3830
  - Stripe: Build related test targets in one graph (https://starsling.dev/ci-playbooks/stripe#share-framework-build-graph): https://github.com/stripe/stripe-ios/pull/7332

### release-query-results

- title: Release query results before they become a timeout
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: none
- companies: Mastra
- page: https://starsling.dev/ci-playbooks/techniques/release-query-results.md
- implementations:
  - Mastra: Release query results before they become a timeout (https://starsling.dev/ci-playbooks/mastra#release-query-results): https://github.com/mastra-ai/mastra/pull/25613

### release-readiness-review

- title: Review the diff since the last release tag before shipping
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/release-readiness-review.md
- implementations:
  - OpenAI: Review the diff since the last release tag before shipping (https://starsling.dev/ci-playbooks/openai#release-readiness-review): https://github.com/openai/openai-agents-python/pull/2480

### remove-expensive-caches

- title: Remove caches that cost more than they save
- fast-ci file: `playbook/caching.md`
- StarSling categories: Caching and setup, Compute waste
- companies: Linear, OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/remove-expensive-caches.md
- implementations:
  - Linear: Remove a cache when restoring it costs more than rebuilding (https://starsling.dev/ci-playbooks/linear#drop-a-cache-that-costs-more): https://linear.app/now/ci-bottleneck-reworked#don%27t-cache-when-it%27s-faster-to-rebuild
  - OpenAI: Drop a cache that costs more than it saves (https://starsling.dev/ci-playbooks/openai#costly-cache): https://github.com/openai/codex/pull/11540

### resilient-checkout

- title: Bound stalled transfers and retry them
- fast-ci file: `playbook/caching.md`
- StarSling categories: none
- companies: Linear
- page: https://starsling.dev/ci-playbooks/techniques/resilient-checkout.md
- implementations:
  - Linear: Bound stalled transfers and retry them (https://starsling.dev/ci-playbooks/linear#resilient-checkout): https://linear.app/now/ci-bottleneck-reworked#make-checkout-more-resilient

### retry-infra-failures-only

- title: Retry only infrastructure failures
- fast-ci file: `playbook/cost.md`
- StarSling categories: none
- companies: Anthropic
- page: https://starsling.dev/ci-playbooks/techniques/retry-infra-failures-only.md
- implementations:
  - Anthropic: Retry only infrastructure failures (https://starsling.dev/ci-playbooks/anthropic#retry-infra-failures-only): https://github.com/oven-sh/bun/pull/34684

### reuse-docker-layers

- title: Reuse Docker build layers across runners
- fast-ci file: `playbook/caching.md`
- StarSling categories: Caching and setup
- companies: Spotify, Stripe
- page: https://starsling.dev/ci-playbooks/techniques/reuse-docker-layers.md
- implementations:
  - Spotify: Restore image layers from the registry cache (https://starsling.dev/ci-playbooks/spotify#registry-layer-cache): https://github.com/spotify/confidence-resolver/pull/132
  - Stripe: Persist Docker build layers across runners (https://starsling.dev/ci-playbooks/stripe#cache-docker-layers): https://github.com/stripe/sync-engine-fork/pull/223

### reuse-package-downloads

- title: Cache package downloads and dependency stores
- fast-ci file: `playbook/caching.md`
- StarSling categories: Caching and setup
- companies: DoorDash, Linear, Shopify, Spotify, Stripe, Uber
- page: https://starsling.dev/ci-playbooks/techniques/reuse-package-downloads.md
- implementations:
  - DoorDash: Cache Go modules and build output (https://starsling.dev/ci-playbooks/doordash#cache-go-modules): https://github.com/doordash-oss/agentic-orchestrator/pull/36
  - Linear: Cache the pnpm store, in the right setup order (https://starsling.dev/ci-playbooks/linear#cache-pnpm-store): https://github.com/linear/linear/pull/1130
  - Linear: Cache Yarn downloads while keeping a locked install (https://starsling.dev/ci-playbooks/linear#cache-yarn-store): https://github.com/linear/linear-zapier/pull/101
  - Shopify: Cache the native dependencies behind a JavaScript build (https://starsling.dev/ci-playbooks/shopify#cache-native-dependencies): https://github.com/Shopify/checkout-kit/pull/182
  - Spotify: Cache Bazel downloads and build outputs (https://starsling.dev/ci-playbooks/spotify#bazel-caches): https://github.com/spotify/target-determinator/pull/15
  - Stripe: Use the ecosystem’s cache integration (https://starsling.dev/ci-playbooks/stripe#use-managed-gradle-cache): https://github.com/stripe/stripe-react-native/pull/2111
  - Uber: Persist the build cache between runners (https://starsling.dev/ci-playbooks/uber#cache-build-inputs): https://github.com/uber/tango/pull/219

### reuse-shared-test-inputs

- title: Prepare shared test inputs once
- fast-ci file: `playbook/caching.md`
- StarSling categories: Caching and setup
- companies: Mastra, Stripe
- page: https://starsling.dev/ci-playbooks/techniques/reuse-shared-test-inputs.md
- implementations:
  - Mastra: Publish test packages once and hand off the registry (https://starsling.dev/ci-playbooks/mastra#publish-once): https://github.com/mastra-ai/mastra/pull/18821
  - Stripe: Download shared test inputs once (https://starsling.dev/ci-playbooks/stripe#handoff-shared-test-inputs): https://github.com/stripe/stripe-dotnet/pull/3340

### review-rules-in-agents-md

- title: Write the review questions you keep repeating into AGENTS.md
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/review-rules-in-agents-md.md
- implementations:
  - OpenAI: Write the review questions you keep repeating into AGENTS.md (https://starsling.dev/ci-playbooks/openai#review-rules-in-agents-md): https://developers.openai.com/blog/custom-code-review-rules-for-codex

### run-ci-once

- title: Run CI once per pull request commit
- fast-ci file: `playbook/unnecessary.md`
- StarSling categories: Agent PR volume, Compute waste, Unnecessary work
- companies: Anthropic, Shopify, Spotify
- page: https://starsling.dev/ci-playbooks/techniques/run-ci-once.md
- implementations:
  - Anthropic: Run CI once per change (https://starsling.dev/ci-playbooks/anthropic#one-run-per-change): https://claude.com/resources/articles/agentic-coding-is-straining-ci-heres-how-we-scaled-test-impact-analysis-at-anthropic
  - Shopify: Run each pull-request commit once (https://starsling.dev/ci-playbooks/shopify#run-commit-once): https://github.com/Shopify/vscode-shopify-ruby/pull/808
  - Spotify: Run push builds only on the default branch (https://starsling.dev/ci-playbooks/spotify#push-main-only): https://github.com/spotify/target-determinator/pull/15

### scan-only-the-diff

- title: After the first full agent scan, review only what changed
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: Agent PR volume, Test selection
- companies: Shopify
- page: https://starsling.dev/ci-playbooks/techniques/scan-only-the-diff.md
- implementations:
  - Shopify: After the first full agent scan, review only what changed (https://starsling.dev/ci-playbooks/shopify#scan-only-the-diff): https://shopify.engineering/building-an-agentic-harness-that-outlasts-the-model

### scheduled-cleanup-prs

- title: Schedule agents to open small cleanup pull requests for review
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/scheduled-cleanup-prs.md
- implementations:
  - OpenAI: Schedule agents to open small cleanup pull requests for review (https://starsling.dev/ci-playbooks/openai#scheduled-cleanup-prs): https://openai.com/index/harness-engineering/

### schema-snapshots

- title: Load a schema snapshot without abandoning migration tests
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: none
- companies: Linear
- page: https://starsling.dev/ci-playbooks/techniques/schema-snapshots.md
- implementations:
  - Linear: Load a schema snapshot without abandoning migration tests (https://starsling.dev/ci-playbooks/linear#schema-snapshots): https://linear.app/now/ci-bottleneck-reworked#avoid-replaying-unchanged-setup

### scope-workspace-builds

- title: Install and build only the workspace packages a job uses
- fast-ci file: `playbook/selection.md`
- StarSling categories: Agent PR volume, Test selection, Unnecessary work
- companies: Linear, Mastra, Shopify
- page: https://starsling.dev/ci-playbooks/techniques/scope-workspace-builds.md
- implementations:
  - Linear: Install or build only the workspace packages this step needs (https://starsling.dev/ci-playbooks/linear#filtered-installs): https://linear.app/now/ci-bottleneck-reworked#install-only-the-dependencies-each-job-needs
  - Mastra: Build only the dependencies the test consumes (https://starsling.dev/ci-playbooks/mastra#scope-build): https://github.com/mastra-ai/mastra/pull/22381
  - Shopify: Give each CI lane a defined package set (https://starsling.dev/ci-playbooks/shopify#scope-package-lanes): https://github.com/Shopify/shopify-app-js/pull/2777

### security-agent-failing-test

- title: Have security agents write a failing integration test before they fix
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: Ramp
- page: https://starsling.dev/ci-playbooks/techniques/security-agent-failing-test.md
- implementations:
  - Ramp: Have security agents write a failing integration test before they fix (https://starsling.dev/ci-playbooks/ramp#security-agent-failing-test): https://builders.ramp.com/post/100-vulnerabilities-patched-with-0-humans

### select-affected-tests

- title: Run only the tests a change can affect
- fast-ci file: `playbook/selection.md`
- StarSling categories: Agent PR volume, Test selection
- companies: Anthropic, Mastra, Ramp, Stripe
- page: https://starsling.dev/ci-playbooks/techniques/select-affected-tests.md
- implementations:
  - Anthropic: Run only affected tests (https://starsling.dev/ci-playbooks/anthropic#affected-tests): https://claude.com/resources/articles/agentic-coding-is-straining-ci-heres-how-we-scaled-test-impact-analysis-at-anthropic
  - Mastra: Route tests through the dependency graph (https://starsling.dev/ci-playbooks/mastra#affected-tests): https://github.com/mastra-ai/mastra/pull/18819
  - Ramp: Build only the data models a change modified (https://starsling.dev/ci-playbooks/ramp#build-modified-models): https://builders.ramp.com/post/cost-efficient-snowflake-ci
  - Stripe: Run only the tests a change can reach (https://starsling.dev/ci-playbooks/stripe#select-tests-by-observed-files): https://stripe.dev/blog/selective-test-execution-at-stripe-fast-ci-for-a-50m-line-ruby-monorepo
  - Stripe: Select changed modules and their dependents (https://starsling.dev/ci-playbooks/stripe#scope-affected-modules): https://github.com/stripe/stripe-ios/pull/7332

### separate-cheap-formatting

- title: Run cheap formatting before semantic formatting
- fast-ci file: `playbook/unnecessary.md`
- StarSling categories: none
- companies: Stripe
- page: https://starsling.dev/ci-playbooks/techniques/separate-cheap-formatting.md
- implementations:
  - Stripe: Run cheap formatting before semantic formatting (https://starsling.dev/ci-playbooks/stripe#separate-cheap-formatting): https://github.com/stripe/stripe-dotnet/pull/3202

### setup-cost-limits-sharding

- title: Reduce the setup floor before increasing shard count
- fast-ci file: `playbook/parallel.md`
- StarSling categories: Agent PR volume, Caching and setup, Compute waste, Parallelization and sharding, Test selection, Slow tests, Unnecessary work
- companies: Linear
- page: https://starsling.dev/ci-playbooks/techniques/setup-cost-limits-sharding.md
- implementations:
  - Linear: Reduce the setup floor before increasing shard count (https://starsling.dev/ci-playbooks/linear#setup-cost-limits-sharding): https://linear.app/now/ci-bottleneck-reworked#sharding-is-limited-by-setup-overhead

### shard-test-suites

- title: Split long test suites across runners
- fast-ci file: `playbook/parallel.md`
- StarSling categories: Parallelization and sharding, Slow tests
- companies: Anthropic, DoorDash, Mastra, OpenAI, Shopify, Spotify, Stripe
- page: https://starsling.dev/ci-playbooks/techniques/shard-test-suites.md
- implementations:
  - Anthropic: Split test files across CI shards that stay balanced to within one file (https://starsling.dev/ci-playbooks/anthropic#shard-test-files): https://bun.sh/blog/bun-v1.3.13
  - DoorDash: Shard the test phase across agents (https://starsling.dev/ci-playbooks/doordash#shard-test-phase): https://careersatdoordash.com/blog/how-doordash-slashed-web-developer-build-times/
  - Mastra: Split a long end-to-end suite across runners (https://starsling.dev/ci-playbooks/mastra#test-shards): https://github.com/mastra-ai/mastra/blob/f92e947a448a47515acf14df1eddc5fd5c36f424/.github/workflows/e2e-tests.yml https://github.com/mastra-ai/mastra/pull/15888
  - OpenAI: Split the slowest job across runners (https://starsling.dev/ci-playbooks/openai#split-slow-job): https://github.com/openai/openai-cli/pull/511
  - Shopify: Give a long suite more than one runner (https://starsling.dev/ci-playbooks/shopify#measure-shards): https://github.com/Shopify/cli/pull/7350
  - Spotify: Shard a serial end-to-end suite across runners (https://starsling.dev/ci-playbooks/spotify#shard-e2e): https://github.com/spotify/confidence-cli/pull/73
  - Stripe: Shard a long suite across runners (https://starsling.dev/ci-playbooks/stripe#shard-with-complete-discovery): https://github.com/stripe/stripe-android/pull/13225

### share-bazel-startup

- title: Give build queries the same startup flags as the build
- fast-ci file: `playbook/unnecessary.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/share-bazel-startup.md
- implementations:
  - OpenAI: Give build queries the same startup flags as the build (https://starsling.dev/ci-playbooks/openai#share-bazel-startup): https://github.com/openai/codex/pull/19232

### share-module-state

- title: Share module initialization only for explicitly safe tests
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: Slow tests
- companies: Linear
- page: https://starsling.dev/ci-playbooks/techniques/share-module-state.md
- implementations:
  - Linear: Share module initialization only for explicitly safe tests (https://starsling.dev/ci-playbooks/linear#share-module-state): https://linear.app/now/ci-bottleneck-reworked#share-module-state-only-with-strict-isolation-rules

### share-small-job-setup

- title: Share setup across small checks
- fast-ci file: `playbook/cost.md`
- StarSling categories: Compute waste, Parallelization and sharding
- companies: Linear, Stripe
- page: https://starsling.dev/ci-playbooks/techniques/share-small-job-setup.md
- implementations:
  - Linear: Pay setup twice instead of seven times (https://starsling.dev/ci-playbooks/linear#batch-short-checks): https://linear.app/now/ci-bottleneck-reworked#batch-short-checks-into-fewer-jobs
  - Stripe: Share setup across compatible small checks (https://starsling.dev/ci-playbooks/stripe#share-small-job-setup): https://github.com/stripe/stripe-ios/pull/6969

### shorten-proven-test-waits

- title: Shorten deliberate test waits
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: Slow tests
- companies: Anthropic, Mastra
- page: https://starsling.dev/ci-playbooks/techniques/shorten-proven-test-waits.md
- implementations:
  - Anthropic: Shorten deliberate sleeps in tests and examples (https://starsling.dev/ci-playbooks/anthropic#shorten-deliberate-sleeps): https://github.com/anthropics/claude-agent-sdk-python/pull/760
  - Mastra: Shorten only waits whose consistency is already proved (https://starsling.dev/ci-playbooks/mastra#shorter-waits): https://github.com/mastra-ai/mastra/pull/13866

### size-agents-to-graph-width

- title: Size the agent pool to the widest layer of the build graph
- fast-ci file: `playbook/parallel.md`
- StarSling categories: none
- companies: DoorDash
- page: https://starsling.dev/ci-playbooks/techniques/size-agents-to-graph-width.md
- implementations:
  - DoorDash: Size the agent pool to the widest layer of the build graph (https://starsling.dev/ci-playbooks/doordash#size-agents-to-graph-width): https://careersatdoordash.com/blog/how-doordash-slashed-web-developer-build-times/

### skip-identical-validation

- title: Reuse validation for unchanged inputs
- fast-ci file: `playbook/selection.md`
- StarSling categories: none
- companies: Linear, OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/skip-identical-validation.md
- implementations:
  - Linear: Skip jobs whose tests already passed for the same inputs (https://starsling.dev/ci-playbooks/linear#skip-work-already-passed): https://linear.app/now/ci-bottleneck-reworked#optimize-the-jobs-that-gate-other-work
  - OpenAI: Avoid revalidating a transformation that changed nothing (https://starsling.dev/ci-playbooks/openai#skip-identical-revalidation): https://github.com/openai/openai-ruby/pull/966

### skip-unaffected-jobs

- title: Skip jobs whose inputs have not changed
- fast-ci file: `playbook/selection.md`
- StarSling categories: Agent PR volume, Test selection, Unnecessary work
- companies: Anthropic, DoorDash, Mastra, OpenAI, Shopify, Stripe
- page: https://starsling.dev/ci-playbooks/techniques/skip-unaffected-jobs.md
- implementations:
  - Anthropic: Skip workflows a change cannot affect (https://starsling.dev/ci-playbooks/anthropic#path-filters): https://claude.com/resources/articles/agentic-coding-is-straining-ci-heres-how-we-scaled-test-impact-analysis-at-anthropic
  - DoorDash: Start the native matrix when its inputs change (https://starsling.dev/ci-playbooks/doordash#gate-native-matrix): https://github.com/doordash-oss/agentic-orchestrator/pull/180
  - Mastra: Skip whole jobs only when their inputs are unchanged (https://starsling.dev/ci-playbooks/mastra#affected-jobs): https://github.com/mastra-ai/mastra/pull/22381
  - OpenAI: Skip independent jobs only for proven narrow edits (https://starsling.dev/ci-playbooks/openai#scope-independent-jobs): https://github.com/openai/codex-security/pull/2002
  - Shopify: Run the platform checks a binding change affects (https://starsling.dev/ci-playbooks/shopify#filter-platform-consumers): https://github.com/Shopify/checkout-kit/pull/546
  - Shopify: Skip platform jobs for documentation-only changes (https://starsling.dev/ci-playbooks/shopify#skip-docs-only): https://github.com/Shopify/checkout-kit/pull/349
  - Stripe: Gate expensive checks on their real inputs (https://starsling.dev/ci-playbooks/stripe#skip-unrelated-checks): https://github.com/stripe/stripe-ios/pull/7336

### skip-warm-bundle-runner

- title: Remove a redundant runner after verified cache delivery
- fast-ci file: `playbook/unnecessary.md`
- StarSling categories: none
- companies: OpenAI
- page: https://starsling.dev/ci-playbooks/techniques/skip-warm-bundle-runner.md
- implementations:
  - OpenAI: Remove a redundant runner after verified cache delivery (https://starsling.dev/ci-playbooks/openai#skip-warm-bundle-runner): https://github.com/openai/codex-security/pull/2042

### sparse-checkout-for-gates

- title: Check out only the gate’s script
- fast-ci file: `playbook/unnecessary.md`
- StarSling categories: none
- companies: Stripe
- page: https://starsling.dev/ci-playbooks/techniques/sparse-checkout-for-gates.md
- implementations:
  - Stripe: Check out only the gate’s script (https://starsling.dev/ci-playbooks/stripe#sparse-checkout-for-gates): https://github.com/sorbet/sorbet/pull/10214

### split-long-lanes

- title: Split independent work off the longest job
- fast-ci file: `playbook/parallel.md`
- StarSling categories: Parallelization and sharding, Slow tests
- companies: Stripe
- page: https://starsling.dev/ci-playbooks/techniques/split-long-lanes.md
- implementations:
  - Stripe: Split independent work off the longest job (https://starsling.dev/ci-playbooks/stripe#split-long-lanes): https://github.com/stripe/stripe-ios/pull/7334

### suite-under-leak-sanitizer

- title: Run the whole test suite under a leak sanitizer with a curated suppression list
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: none
- companies: Anthropic
- page: https://starsling.dev/ci-playbooks/techniques/suite-under-leak-sanitizer.md
- implementations:
  - Anthropic: Run the whole test suite under a leak sanitizer with a curated suppression list (https://starsling.dev/ci-playbooks/anthropic#suite-under-leak-sanitizer): https://github.com/oven-sh/bun/pull/30875

### synchronize-assertions

- title: Wait for the state transition before asserting
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: none
- companies: Uber
- page: https://starsling.dev/ci-playbooks/techniques/synchronize-assertions.md
- implementations:
  - Uber: Wait for the state transition before asserting (https://starsling.dev/ci-playbooks/uber#synchronize-assertions): https://github.com/uber/submitqueue/pull/274

### trace-screenshots

- title: Record trace screenshots only when someone reads them
- fast-ci file: `playbook/slow-tests.md`
- StarSling categories: none
- companies: DoorDash
- page: https://starsling.dev/ci-playbooks/techniques/trace-screenshots.md
- implementations:
  - DoorDash: Record trace screenshots only when someone reads them (https://starsling.dev/ci-playbooks/doordash#trace-screenshots): https://github.com/doordash-oss/agentic-orchestrator/pull/139

### triage-investigation

- title: Have an agent investigate every new issue before a person does
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: Mastra
- page: https://starsling.dev/ci-playbooks/techniques/triage-investigation.md
- implementations:
  - Mastra: Have an agent investigate every new issue before a person does (https://starsling.dev/ci-playbooks/mastra#triage-investigation): https://mastra.ai/blog/announcing-mastra-factory-beta

### tune-test-workers

- title: Match test concurrency to the runner
- fast-ci file: `playbook/parallel.md`
- StarSling categories: Parallelization and sharding, Queue and runner speed, Slow tests
- companies: Anthropic, Mastra, OpenAI, Stripe
- page: https://starsling.dev/ci-playbooks/techniques/tune-test-workers.md
- implementations:
  - Anthropic: Set test worker width from the actual host (https://starsling.dev/ci-playbooks/anthropic#tune-worker-width): https://github.com/oven-sh/bun/pull/36175
  - Mastra: Fit test concurrency to the runner’s memory (https://starsling.dev/ci-playbooks/mastra#test-workers): https://github.com/mastra-ai/mastra/pull/13937 https://github.com/mastra-ai/mastra/blob/f92e947a448a47515acf14df1eddc5fd5c36f424/packages/memory/integration-tests/vitest.config.ts
  - OpenAI: Measure how many tests to run at once (https://starsling.dev/ci-playbooks/openai#measured-concurrency): https://github.com/openai/codex/pull/31352
  - Stripe: Measure workers against the runner (https://starsling.dev/ci-playbooks/stripe#measure-worker-count): https://github.com/stripe/stripe-ios/pull/7333

### uncluster-no-op-projects

- title: Let shared packages without a build step stay cacheable
- fast-ci file: `playbook/parallel.md`
- StarSling categories: Parallelization and sharding
- companies: DoorDash
- page: https://starsling.dev/ci-playbooks/techniques/uncluster-no-op-projects.md
- implementations:
  - DoorDash: Let shared packages without a build step stay cacheable (https://starsling.dev/ci-playbooks/doordash#uncluster-no-op-projects): https://careersatdoordash.com/blog/how-doordash-slashed-web-developer-build-times/

### verify-before-agent-pr

- title: Require verification before an agent hands over a pull request
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: DoorDash, OpenAI, Ramp, Spotify
- page: https://starsling.dev/ci-playbooks/techniques/verify-before-agent-pr.md
- implementations:
  - DoorDash: Let an agent open a pull request only after build, tests, coverage and lint pass (https://starsling.dev/ci-playbooks/doordash#gate-agent-pull-requests): https://careersatdoordash.com/blog/automating-feature-flag-cleanup-at-scale-with-a-multi-agent-llm-system/
  - OpenAI: Make the verification stack a skill the agent must pass (https://starsling.dev/ci-playbooks/openai#verification-skill): https://developers.openai.com/blog/skills-agents-sdk
  - Ramp: Have the coding agent hand over a visually validated pull request (https://starsling.dev/ci-playbooks/ramp#agent-opens-reviewed-pr): https://ramp.com/blog/introducing-inspect
  - Spotify: Run verifiers and a judge before an agent opens a pull request (https://starsling.dev/ci-playbooks/spotify#agent-verification-loop): https://engineering.atspotify.com/2025/12/feedback-loops-background-coding-agents-part-3

### warm-agent-environments

- title: Keep prepared environments ready for agent work
- fast-ci file: `playbook/agent-volume.md`
- StarSling categories: none
- companies: DoorDash, Shopify
- page: https://starsling.dev/ci-playbooks/techniques/warm-agent-environments.md
- implementations:
  - DoorDash: Run agent builds and tests in isolated cloud sandboxes that start in seconds (https://starsling.dev/ci-playbooks/doordash#cloud-agent-sandboxes): https://careersatdoordash.com/blog/delegating-engineering-work-to-cloud-based-agents/
  - Shopify: Keep warm, prebuilt machines ready for agent sessions (https://starsling.dev/ci-playbooks/shopify#warm-agent-machines): https://shopify.engineering/remote-dev

### warm-image-caches

- title: Warm reusable caches while building the image
- fast-ci file: `playbook/caching.md`
- StarSling categories: none
- companies: Ramp
- page: https://starsling.dev/ci-playbooks/techniques/warm-image-caches.md
- implementations:
  - Ramp: Run the app and test suite once in the image build to warm its caches (https://starsling.dev/ci-playbooks/ramp#warm-image-with-a-test-run): https://builders.ramp.com/post/why-we-built-our-background-agent

### weighted-build-and-test

- title: Weight memory-heavy steps so build and test run in parallel on separate agents
- fast-ci file: `playbook/parallel.md`
- StarSling categories: Parallelization and sharding
- companies: DoorDash
- page: https://starsling.dev/ci-playbooks/techniques/weighted-build-and-test.md
- implementations:
  - DoorDash: Weight memory-heavy steps so build and test run in parallel on separate agents (https://starsling.dev/ci-playbooks/doordash#weighted-build-and-test): https://careersatdoordash.com/blog/how-doordash-slashed-web-developer-build-times/

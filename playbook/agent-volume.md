# Agent PR volume

As agents open more pull requests, CI time goes to obsolete runs on superseded commits, longer queues, checks that run twice, and fix rounds an agent could have avoided. Diagnose first: compare queue time, runs per commit, cancellation rate and critical-path time before choosing more compute, narrower test selection or a merge-queue change. Most entries here are agent processes outside CI, so the Speedup loop puts them in the report as recommendations; only the two CI changes at the top are auto.

### keep-agent-ci-current: Run CI on every new agent commit and act only on that head's result

- **applies when:** `agent_prs_per_day` over 5, and the PR workflow either sets `pull_request` `types:` without `synchronize`, has `no_concurrency`, or shows `superseded_running` over 0.
- **how:** Make every new head of a PR start a run, cancel the run for the head it replaced, and make agents and merges read only the run whose `head_sha` matches the PR's current head. Keep the default `pull_request` types (they include `synchronize`). Key the concurrency group on the PR number for PRs and on the commit SHA on the default branch, so default-branch runs never cancel each other. Agents wait with `gh run watch <id>` on the run for the current head, never on a notification that may belong to an earlier head (Shopify's River saw CI-passed notices for force-pushed heads arrive after the push). Pushes made with a workflow's own `GITHUB_TOKEN` start no new run, so an agent that pushes from inside Actions needs a token that does; flag that in the report rather than changing it. If `cancel-superseded-runs` already landed, this entry only checks the triggers and the head check.
  ```yaml
  on:
    pull_request:
    push:
      branches: [main]
  concurrency:
    group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.sha }}
    cancel-in-progress: ${{ github.event_name == 'pull_request' }}
  ```
- **estimate:** runner seconds freed per day are `superseded_running` per day times the mean remaining `run_s` of a superseded run. When jobs queue, each agent PR's wall time also drops by the share of `wait_s` those runs caused.
- **verify:** Over 10 PRs with at least 2 pushes each, every head SHA has exactly one run that completed (`gh run list --json headSha,status,conclusion,event`), no default-branch push run was cancelled, and the required jobs and the `ci-ok` gate are the same as before. Push a deliberately failing commit on top of a green one and confirm the PR shows red for the new head.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/keep-agent-ci-current.md), [Anthropic](https://www.anthropic.com/research/building-c-compiler), [Shopify](https://shopify.engineering/river-vulnerability-remediation)

### agent-readable-test-output: Print a short test summary and keep the full log as an artifact

- **applies when:** `agent_prs_per_day` over 5 and the test step prints one line or more per passing test (a verbose or default reporter in CI), or the test step's log runs past a few thousand lines.
- **how:** Switch the CI test reporter to a quiet one that prints progress and one line per failure, write the full results to a file, and upload that file as an artifact with `if: always()` so people and agents read the same detail. For Vitest use `--reporter=dot` plus `--reporter=junit`; for pytest use `-q -rfE --junitxml=...`. Each failure line carries the test name and the reason, so `grep` finds it. Anthropic's compiler harness prints at most a few lines, puts ERROR and the reason on one line, and precomputes summary counts. Do not copy its `--fast` 1% or 10% sample into CI, because that skips tests; it belongs only in an agent's local loop.
  ```yaml
  - run: pnpm vitest run --reporter=dot --reporter=junit --outputFile.junit=test-results/junit.xml
  - if: always()
    uses: actions/upload-artifact@v4
    with:
      name: test-results-${{ github.job }}-${{ strategy.job-index }}
      path: test-results/
  ```
- **estimate:** a few seconds per run at most from printing and streaming less log. The larger saving is in agent rounds: each red run an agent misreads costs another `pr_p50`, so count red agent runs whose fix took more than one push, before and after.
- **verify:** Over 10 runs before and after, the test step's time does not rise and its log line count drops sharply. The junit file's test count equals the count the old reporter printed, the required jobs are unchanged, and a deliberately failing test still turns the job red and appears by name on one line in the log and in the artifact.
- **risk:** low
- **mode:** auto
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/agent-readable-test-output.md), [Anthropic](https://www.anthropic.com/research/building-c-compiler)

### verify-before-agent-pr: Agents pass the repo's checks before they open a pull request

- **applies when:** `agent_prs_per_day` over 5 and more than 20% of agent PRs fail their first CI run, or parallel agents share one checkout.
- **how:** Recommend that the agent's definition of done is the same command list CI runs. Put that list in one script both CI and the agent call, so it cannot drift. Run it from a hook the agent cannot skip, because agents skip steps written only in `AGENTS.md`; fast-ci's Baseline pre-push hook (`lefthook.yml`, format, lint and typecheck on changed files in under 10 seconds) is the local half of this. DoorDash's flag-cleanup agents may open a PR only after the build, the tests, 95% patch coverage on changed lines and Detekt pass, with up to four agents per repository each in its own worktree and Gradle run with `--no-daemon`; 45 of the 50 latest stale flags got usable PRs at 4.79 dollars and 13.8 minutes each. OpenAI's Agents SDK uses a code-change-verification skill that docs-only changes skip. Spotify runs verifiers chosen from the repository's contents from the Claude Code stop hook, each returning a short error summary, then an LLM judge that reads the diff against the prompt and vetoes about a quarter of sessions. Ramp's Inspect attaches visual proof before review and accounts for 74% of Ramp's merged PRs.
- **estimate:** agent PRs per day whose first run fails, times one `pr_p50` per avoided round, plus the runner minutes of those red runs (`run_s` summed over their jobs).
- **verify:** Over two weeks before and after, the share of agent PRs whose first run is red drops, and CI's required checks and their test counts are unchanged, since the local gate only runs earlier and never replaces CI.
- **risk:** low
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/verify-before-agent-pr.md), [DoorDash](https://careersatdoordash.com/blog/automating-feature-flag-cleanup-at-scale-with-a-multi-agent-llm-system/), [OpenAI](https://developers.openai.com/blog/skills-agents-sdk), [Ramp](https://ramp.com/blog/introducing-inspect), [Spotify](https://engineering.atspotify.com/2025/12/feedback-loops-background-coding-agents-part-3)

### agent-readable-lint-feedback: Lint errors that tell the agent how to fix them

- **applies when:** `agent_prs_per_day` over 5 and the same lint or structural-test rule fails agent PRs again and again (count failing rule ids across red agent runs), or review comments repeat a convention no check enforces.
- **how:** Recommend that the rules reviewers correct most often become lint rules or structural tests, and that each error message carries the repair, not only the rule name. OpenAI's agent-first team enforces dependency direction between layers, structured logging, naming conventions for schemas and types and file size limits with custom lints whose messages carry remediation instructions. Spotify gives Claude the same lint feedback developers get, so a ruled-out pattern fails at once and the agent corrects itself. Update the message in the same change as the rule, and keep the check deterministic. The output-format half (one line per error, such as `oxlint --format github`) is a CI change the loop can land with `agent-readable-test-output`.
- **estimate:** red agent runs per day caused by repeat lint rules, times one `pr_p50` per round the message saves.
- **verify:** Over two weeks, red agent runs caused by those rules drop; every rule enforced before is still enforced, and a deliberate violation still fails with the new message.
- **risk:** low
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/agent-readable-lint-feedback.md), [OpenAI](https://openai.com/index/harness-engineering/), [Spotify](https://engineering.atspotify.com/2026/6/code-with-claude-coding-is-no-longer-the-constraint)

### rank-by-minutes: Rank CI fixes by the minutes they save

- **applies when:** the repo has at least 150 runs of history (`runs_per_day` times the window) and no ranked list of CI fixes exists yet.
- **how:** The fast-ci Speedup loop is this method: its Audit step reads the last 150 runs and its Rank step orders every playbook item by seconds saved on the critical path, then by risk. Report it to the user as the method already applied, and for work outside the loop, recommend the same order. Rank total CI minutes separately from time spent waiting on a merge, because the two lists differ. OpenAI's team asked an agent to read the repository's run history, list ideas and rank them by CI minutes saved per day; about 30 CI optimization PRs followed.
- **estimate:** each candidate's seconds saved per run times `runs_per_day`, for minutes per day; the critical-path share comes from `critical_path`.
- **verify:** the report's measured before and after times for each landed fix match the order the ranking predicted; nothing about any check changes.
- **risk:** low
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/rank-by-minutes.md), [OpenAI](https://developers.openai.com/blog/maintaining-software-with-the-gpt-6-family#other-ideas-to-try)

### agent-metric-loop: Let an agent iterate against one CI metric

- **applies when:** one step's `run_s` sets the `critical_path` (over 50% of `pr_p50`) and changes to it can be tested one at a time.
- **how:** The fast-ci Speedup loop is this method: it lands one change at a time, measures each against the baseline from real runs, keeps what is green and faster, and reverts the rest. For a single slow step it cannot fix from the catalog, recommend the same loop by hand: profile the step, write one hypothesis down, test it, keep it only if the metric beats the baseline and the output is the same. Read the diff of every kept change and discard any that removes files. Shopify's Polaris loop took build time from a 19.1 second baseline to 65% faster, after finding the TypeScript transform ran over all 580 component files when 105 needed it; the same approach produced an upstream pnpm PR that skips redundant linking on a warm reinstall.
- **estimate:** the step's `run_s` times the fraction the loop removes; use Shopify's 65% only as an upper bound.
- **verify:** compare 10 runs of the step before and after; the build output (file list and hashes) and the test count stay the same.
- **risk:** low
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/agent-metric-loop.md), [Shopify](https://shopify.engineering/autoresearch)

### automated-pr-review: Run an agent review on every pull request before a human approves

- **applies when:** `agent_prs_per_day` over 10 and PRs wait longer for a first human review than for CI (review wait over `pr_p50`).
- **how:** Recommend an agent reviewer as the first read on every PR, with the human approval kept as the merge gate and required checks unchanged. Linear has a coding agent review every PR before an engineer approves, so reviewers spend their time on fit and the customer's problem. Ramp built its review bot on Inspect, the same background agent API that writes its PRs, with team-written skill files for what to check. Uber's uReview reviews every commit across six monorepos, scores each comment for confidence, merges near duplicates and suppresses low-value categories; engineers mark 75% of comments useful, over 65% are addressed, and Uber estimates about 1,500 hours saved a week. Tune thresholds from developer ratings and prune noisy categories.
- **estimate:** this saves review wait, not CI seconds: agent PRs per day times the hours of human review wait removed, from PR timelines (`gh pr view --json reviews`).
- **verify:** over four weeks, time from PR open to first review drops, the share of agent comments acted on stays high, and branch protection and required checks are identical.
- **risk:** medium
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/automated-pr-review.md), [Linear](https://linear.app/now/how-we-use-linear-agent-at-linear), [Ramp](https://claude.com/customers/ramp-boris-office-hours), [Uber](https://www.uber.com/us/en/blog/ureview/)

### independent-agent-review: Review agent changes with reviewers that did not write them

- **applies when:** `agent_prs_per_day` over 10 and the agent that wrote a change is also its only reviewer, or one bot posts comments authors skip.
- **how:** Recommend a review job that reads each agent PR with a fresh agent that sees only the diff and is told to find how the change is wrong, then hands findings back to the author's agent to fix before merge. Bun's Rust port ran about 50 workflows with one implementer, two or more adversarial reviewers and one fixer per loop, and every line was reviewed twice. DoorDash runs a scout, two deep reviewers on a full clone and a disprove-it pass, reviewing over 10,000 PRs a week across 56 repositories at about 3 dollars and seven minutes per review; 60.2% of settled high and critical findings lead to a code change. OpenAI's agent-first team loops agent reviews until every reviewer is satisfied, at 3.5 PRs per engineer per day. Cap reviewers per PR, post only findings anchored to a changed line, and keep a person deciding what merges.
- **estimate:** agent PRs per day that would have needed a later fix PR, times one full `pr_p50` each, minus the review job's own minutes.
- **verify:** read what the reviewers catch for two weeks before the job becomes required; required checks and approvals stay unchanged.
- **risk:** medium
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/independent-agent-review.md), [Anthropic](https://bun.sh/blog/bun-in-rust), [DoorDash](https://careersatdoordash.com/blog/doordash-built-an-ai-code-reviewer-engineers-actually-listen-to/), [OpenAI](https://openai.com/index/harness-engineering/)

### review-rules-in-agents-md: Write the review questions you keep repeating into AGENTS.md

- **applies when:** `agent_prs_per_day` over 5, an agent reviewer runs on PRs, and reviewers keep leaving the same comment about one compatibility rule or data boundary.
- **how:** Recommend short, scoped rules in `AGENTS.md`: repository-wide rules at the root, service rules in that directory's nested `AGENTS.md`, each stating the invariant and the safe path. Keep formatting and other mechanical checks in CI, not in rules. Start with two or three rules, and test each with one change that should trigger it, one safe counterexample and one unrelated change. In OpenAI's evaluation, rule-guided Codex review recovered 98% of required custom findings against 58.3% without rules.
- **estimate:** repeat review comments per week the rules replace, times the review round each one costs; no CI seconds change.
- **verify:** for each rule, the triggering change gets a finding that cites it, the counterexample gets none, and CI is untouched.
- **risk:** low
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/review-rules-in-agents-md.md), [OpenAI](https://developers.openai.com/blog/custom-code-review-rules-for-codex)

### advisory-before-required: Start an agent check as advice, then make it required once it has a record

- **applies when:** `agent_prs_per_day` over 5 and a new agent check on PRs, or an agent that opens its own PRs, is about to become a required check (static: a new workflow job that calls an agent).
- **how:** Recommend that the agent check first runs as a non-required job that only comments. Set the promotion bar before the trial starts, such as the share of findings people acted on, read its record, and only then ask the user to make it required. Linear's teams ask an agent for suggestions, watch it, add guidance, and put it on autopilot once it has proven reliable, keeping work in small steps. A person's approval stays on the merge.
- **estimate:** no CI seconds saved; it avoids blocked PRs from a noisy required check, counted as advisory runs that would have failed falsely times `pr_p50`.
- **verify:** the advisory run's findings are tallied against what people acted on before promotion; until then, required checks are unchanged.
- **risk:** low
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/advisory-before-required.md), [Linear](https://linear.app/now/how-we-use-linear-agent-at-linear)

### agent-shepherds-merge: Give an agent the last mile: watch CI, rebase and retry flaky checks

- **applies when:** `agent_prs_per_day` over 10 and landing a PR takes repeated manual rebases or reruns, with `rerun_rate` over 2%.
- **how:** Recommend that the agent that opened a PR also lands it: it reads CI logs with `gh`, waits on the current head with `gh run watch <id>`, rebases when main moves, resolves conflicts and retries a flaky check a bounded number of times, recording each flake so it gets fixed. Follow fast-ci's push rules: in a stack, rebase locally and push only the top branch, and never subscribe the agent to PR or CI webhooks. OpenAI's Symphony gives each ticket's agent these skills, so a ticket reaching Merging lands without babysitting. Required checks and approvals stay in force.
- **estimate:** human minutes per PR spent on rebases and reruns, times agent PRs per day; CI seconds stay the same, and each recorded flake feeds `rerun_rate` fixes.
- **verify:** retries per PR stay under the cap, every retried flake has an issue, and branch protection is unchanged.
- **risk:** medium
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/agent-shepherds-merge.md), [OpenAI](https://openai.com/index/open-source-codex-orchestration-symphony/)

### first-responder-agent: Put an agent on call for every default-branch CI and deploy failure

- **applies when:** default-branch runs fail more than once a week (`runs_per_day` on main times its failure rate), or `infra_fail_rate` over 2%, and each failure waits for a person to open the logs.
- **how:** Recommend a read-only workflow that runs when a required check fails on the default branch, reads the failed run's logs, the triggering commit and recent runs of the same job, and posts an analysis citing the lines and runs it used for the person on call. Keep standing instructions as skills in the repo and a lessons file the agent reads first. Start with default-branch failures, compare its analyses with what the person finds, and only then widen it to deploys. Anthropic's Claude posts its first evidence-grounded analysis a median of 14 minutes after an incident opens, naming the root cause within 4 minutes in the fastest cases.
- **estimate:** default-branch failures per week times the minutes from failure to first diagnosis it removes; CI seconds stay the same.
- **verify:** over a month, time to first diagnosis drops and the agent's root cause matches the person's in most cases; the agent makes no commits.
- **risk:** low
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/first-responder-agent.md), [Anthropic](https://claude.com/resources/articles/ai-ci-cd-on-call)

### isolated-agent-checkouts: Give each parallel agent its own checkout and a claimed task

- **applies when:** several agents push to one repository (`agent_prs_per_day` over 10 from more than one agent), or two agent PRs address the same task.
- **how:** Recommend one git worktree or container per agent, and a task lock as a file the agent commits (for example under `current_tasks/`) so git rejects a second claim. Tell agents to avoid `git stash`, `git reset` and any git command beyond committing their own files, and keep slow shared commands out of their loop. Anthropic's compiler project gave each agent its own Docker container and workspace; Bun's Rust port ran 4 shards in their own worktrees with 16 Claudes each.
- **estimate:** duplicate agent PRs per day times their full CI minutes (`run_s` summed), plus the red runs caused by shared-checkout collisions.
- **verify:** no two open agent PRs share a task over two weeks, and CI is unchanged.
- **risk:** low
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/isolated-agent-checkouts.md), [Anthropic](https://www.anthropic.com/research/building-c-compiler)

### warm-agent-environments: Keep prepared environments ready for agent sessions

- **applies when:** agent sessions or agent CI jobs spend minutes on checkout, install and build before any work: `setup_share` over 40% on agent runs, or `checkout_s` plus `install_s` over 2 minutes.
- **how:** Inside CI, the cache and prebuilt-image entries in [`caching.md`](caching.md) are the auto version. Outside CI, recommend prebuilt environments for agents: an image with the repo, tools and dependencies baked in, refreshed from main on a schedule, claimed per session and thrown away after it. DoorDash's Flux runs each task in a Firecracker microVM with a p95 target under five seconds for full setup, scoping secrets and tools per task, and automated 130,000 tasks in one month. Shopify keeps a pool of warm Macs with main checked out and apps built, which cut setup from over 30 minutes to a few minutes. Size any pool to the sessions run, because idle machines cost money.
- **estimate:** agent sessions per day times their setup seconds (`setup_s` for agent CI jobs), minus the claim time of a warm environment.
- **verify:** measure setup time as its own number per session before and after; the checks the agent runs are the same.
- **risk:** medium
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/warm-agent-environments.md), [DoorDash](https://careersatdoordash.com/blog/delegating-engineering-work-to-cloud-based-agents/), [Shopify](https://shopify.engineering/remote-dev)

### guided-review-order: Lead a large pull request with its core change and keep formatting in its own commit

- **applies when:** `agent_prs_per_day` over 5 and agent PRs often exceed 500 changed lines with formatting edits mixed into the change.
- **how:** Recommend that agents write the PR description in reading order (the core change, then its consequences, then glue code) and put formatting-only changes in their own commit, so blame and revert stay clean and the reviewer sees the real change. Linear's Diffs break a PR into chapters in the order the work was reasoned through and strip formatting changes, so a 2,000-line PR becomes legible in one sitting. The diff itself stays complete.
- **estimate:** review hours per large agent PR saved; no CI seconds change.
- **verify:** sample large agent PRs: formatting sits in its own commit and the description leads with the core change; CI is unchanged.
- **risk:** low
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/guided-review-order.md), [Linear](https://linear.app/now/code-review-should-be-fast)

### classify-merged-prs: Classify every merged pull request by the work it contains

- **applies when:** `agent_prs_per_day` rose by more than half over the last quarter, and nobody tracks whether review, tests and rollout kept pace.
- **how:** Recommend one label per merged PR from a fixed set (feature, quality and optimization, maintenance, documentation), applied by an agent or a scheduled script, and a monthly look at the mix and at incidents where change volume put pressure on review or testing. Spotify's merged changes went from about 8,100 to 17,000 a month year over year, quality work rose from 27% to 31% of the mix and maintenance fell from 31% to 25%.
- **estimate:** no CI seconds saved; it shows which share of `runs_per_day` comes from which kind of work, to aim the other entries.
- **verify:** every merged PR in a month has exactly one label; CI is unchanged.
- **risk:** low
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/classify-merged-prs.md), [Spotify](https://engineering.atspotify.com/2026/9/ai-changed-how-spotify-builds-what-we-learned-and-fixed-about-quality-at-higher-velocity)

### per-stage-automation: Set each stage of the issue pipeline to auto or manual

- **applies when:** `agent_prs_per_day` comes in bursts (a day over three times the median), for example after a backlog import, and jobs queue (`wait_s` p90 over 60 s on those days).
- **how:** Recommend that each stage of the agent pipeline (intake, triage, planning, build, review) has its own auto or manual switch, starting with the stages that have the clearest inputs, such as automatic triage while planning and implementation stay manual, or bug fixes flowing through while feature requests do not. Mastra moved from full automatic mode to per-stage settings after a backlog import flooded its pipeline; Factory has automated 25 to 35% of its PRs and closed 50 to 60% of its issues, with 200 to 250 PRs merged a week.
- **estimate:** on burst days, `wait_s` times the runs the burst added; spreading the same work flattens queue time without changing run time.
- **verify:** compare several weeks of `wait_s` on peak days before and after; CI is unchanged.
- **risk:** low
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/per-stage-automation.md), [Mastra](https://mastra.ai/blog/announcing-mastra-factory-beta)

### agent-per-ticket: Give every open ticket its own agent

- **applies when:** one engineer steers a few agent sessions by hand while open tasks grow, and the runner pool has headroom (`wait_s` p90 under 30 s).
- **how:** Recommend a board-driven loop where every open ticket gets an agent, a planning ticket can create dependent tickets, and agents start only unblocked ones, with people reviewing results. Before raising the number of parallel agents, check runner capacity and queue time, because more agents open more PRs at once. OpenAI's Symphony reports a 500% rise in landed PRs on some teams in its first three weeks; most people managed three to five sessions by hand before.
- **estimate:** this adds CI load: expected new `agent_prs_per_day` times the per-PR CI minutes (`run_s` summed), checked against runner capacity before rollout.
- **verify:** `wait_s` stays flat as agent PRs rise; CI is unchanged.
- **risk:** medium
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/agent-per-ticket.md), [OpenAI](https://openai.com/index/open-source-codex-orchestration-symphony/)

### triage-investigation: Have an agent investigate every new issue before a person does

- **applies when:** many new issues a week are too vague to reproduce or come from setup mistakes, and agent PRs start from them (`agent_prs_per_day` over 5).
- **how:** Recommend an agent that posts a diagnosis on each new issue: evidence, assumptions and reproduction results, naming the likely owner. A person reviews the assumptions before planning starts, since a wrong one carries into every later stage. Mastra Factory's A2A investigation documented six failing reproduction assertions and named the server integration as the owner, helped by a compressed line-by-line log of files, searches and test output.
- **estimate:** agent PRs per day closed without merging because they started from a wrong diagnosis, times their CI minutes.
- **verify:** the share of agent PRs closed unmerged drops; CI is unchanged.
- **risk:** low
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/triage-investigation.md), [Mastra](https://mastra.ai/blog/announcing-mastra-factory-beta)

### failures-as-work-queue: Write every failure to a file and let fixer agents work through it by area

- **applies when:** `agent_prs_per_day` over 5 and a change leaves over 100 failing test files or errors (static: a migration or port branch with a red suite), or the failure log is too large for one agent to read.
- **how:** Recommend that the test runner writes per-file results as JSON (Vitest `--reporter=json --outputFile=...`, pytest `--junitxml`), grouped by package, and that each group goes to an implementer, two reviewers and a fixer. Run the failing check once at the start of each group and commit at the end, so parallel agents do not start overlapping builds, and have a person read the loop's output and fix its instructions when it drifts. Bun's Rust port wrote about 16,000 compiler errors to a file by crate for 64 Claudes; two days after the first CI run, failing test files dropped from 972 to 23.
- **estimate:** CI runs avoided by fixing a group per run instead of one failure per run: failing groups times `pr_p50` saved per merged round.
- **verify:** the failing count falls run over run and no test is skipped or deleted to get there (same test count).
- **risk:** medium
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/failures-as-work-queue.md), [Anthropic](https://bun.sh/blog/bun-in-rust)

### scheduled-cleanup-prs: Schedule agents to open small cleanup pull requests for review

- **applies when:** cleanup work piles up until it needs a dedicated day, and `agent_prs_per_day` over 5 adds more of it.
- **how:** Recommend golden principles written into the repo (such as shared utility packages and validating data at boundaries) and a scheduled agent that scans for deviations, updates quality grades and opens small refactor PRs. Automerge only changes small enough to review in a minute and covered by required checks. OpenAI's agent-first team replaced a Friday it spent on cleanup, 20% of its week, this way.
- **estimate:** no CI seconds saved per run; it adds small PRs, so count their CI minutes against the engineer hours freed.
- **verify:** cleanup PRs pass the same required checks as any other PR; branch protection is unchanged.
- **risk:** low
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/scheduled-cleanup-prs.md), [OpenAI](https://openai.com/index/harness-engineering/)

### agent-dead-code-sweep: Have an agent prove code is unused, then delete it in reviewed batches

- **applies when:** the test step's `run_s` includes suites, snapshots or images for code nobody calls, or artifact size grows release over release.
- **how:** Recommend an agent that finds dead code, tests and snapshots, cites its evidence for each deletion (past PRs, flags, production profiling, threads), and opens one deletion PR per area for the team that owns it. Past incidents came from mistaken removals, so every deletion needs its evidence and an owner's review. OpenAI engineers ran this across repositories; one cleanup removed about 400 visual snapshot variants from a test suite. A removed test lowers the test count, so this stays a team decision and never an automatic CI change.
- **estimate:** the `run_s` of the deleted tests and snapshots, measured from the test reporter's per-file times.
- **verify:** each deletion PR lists its evidence and owner approval; the remaining suite passes and coverage of live code holds.
- **risk:** medium
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/agent-dead-code-sweep.md), [OpenAI](https://developers.openai.com/blog/maintaining-software-with-the-gpt-6-family)

### doc-gardening-agent: Validate docs in CI and let a scheduled agent fix stale ones

- **applies when:** agents act on stale `AGENTS.md` or docs text (red agent runs that follow an outdated instruction), and `agent_prs_per_day` over 5.
- **how:** Recommend a short `AGENTS.md` as a map (OpenAI's is about 100 lines) pointing into a structured docs directory, deterministic CI checks that docs are current, cross-linked and well formed, and a scheduled agent that opens fix-up PRs for stale docs, reviewed like any other change.
- **estimate:** red agent runs per week traced to stale instructions, times `pr_p50` each.
- **verify:** the docs checks are deterministic and pass on main; fix-up PRs go through the same review and required checks.
- **risk:** low
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/doc-gardening-agent.md), [OpenAI](https://openai.com/index/harness-engineering/)

### scan-only-the-diff: After one full agent scan, review only what changed

- **applies when:** a scheduled or per-commit agent scan (security or review) covers the whole repository and its job's `run_s` is over 10 minutes, while most commits touch a small part of the code.
- **how:** Recommend one full scan that stores its artifacts (partitions, notes on the APIs and data models), then per-commit scans of only the diff against the previous commit that also update the stored artifacts. Run the full scan again when the partitions or artifacts change materially. Shopify's Dispatch runs one hunting agent per partition, and verifier agents one after another so tests that prove findings do not collide on ports and databases; a full scan costs 50 to 300 dollars and a diff scan 5 to 50.
- **estimate:** the scan job's `run_s` times (1 minus the diff's share of the code), per commit.
- **verify:** compare scan time over 10 commits; a planted issue in a changed file is still found, and the full scan still runs on schedule.
- **risk:** medium
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/scan-only-the-diff.md), [Shopify](https://shopify.engineering/building-an-agentic-harness-that-outlasts-the-model)

### security-agent-failing-test: Security agents write a failing test before they fix

- **applies when:** `agent_prs_per_day` over 5 from security tooling, or security findings arrive faster than people can validate them and the affected endpoints already have integration tests (static: an integration test directory per endpoint).
- **how:** Recommend that a validator agent turns each finding into an endpoint-level integration test that reproduces the attack and asserts the secure result, and confirms it fails; a test that already passes marks a false positive and no code changes. A fixer agent then patches the code until that test passes without editing the test, and opens a PR a person reviews and lands. In Ramp's one-week experiment, test-based validation caught nearly all the false positives from its triage pipeline.
- **estimate:** false-positive security PRs per week avoided, times their CI minutes and review time; each fix adds one test's `run_s`.
- **verify:** every fix PR carries a test that fails on main and passes on the branch; no existing test changes.
- **risk:** low
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/security-agent-failing-test.md), [Ramp](https://builders.ramp.com/post/100-vulnerabilities-patched-with-0-humans)

### gate-agent-evaluations: Replay fixed evaluations before merging changes to agent behavior

- **applies when:** `agent_prs_per_day` over 5 touching agent behavior, where the repo ships prompts, model settings or agent code (static: prompt files or an eval directory), and those changes merge after a manual check.
- **how:** Recommend a check that replays fixed scenarios or a golden dataset against recorded fixtures on every PR that touches agent behavior, gated on a pass rate set before evaluation. Refresh fixtures from production traces so the gate tests current behavior, and replace sensitive identifiers with stable test ones. DoorDash's simulated user and calibrated LLM judge cut generating a 400-conversation sweep from over six hours to about 20 minutes. Stripe runs a golden dataset of common flows, boundaries and past incidents on every PR and blocks on unexpected differences. Making it required is a branch-protection change for the user.
- **estimate:** this adds a job: its `run_s` per PR that touches agent files, against the manual eval hours it replaces.
- **verify:** a change that breaks a known scenario fails the eval job; existing checks are unchanged.
- **risk:** medium
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/gate-agent-evaluations.md), [DoorDash](https://careersatdoordash.com/blog/building-ask-doordash-part-three-evaluation/), [Stripe](https://stripe.dev/blog/microservice-testing-with-apache-spark)

### agent-conformance-suite: Give agents a conformance suite to test against

- **applies when:** `agent_prs_per_day` over 5 and agents change code that must match a reference (a protocol, file format, public API or a system being reimplemented), and agent PRs regress that behavior (red runs after merge on those paths).
- **how:** Recommend a conformance suite whose expected results come from the reference implementation itself, run by agents on every change and by a CI job on every PR, with a new case each time an agent finds a difference. OpenAI built Pando, its Git backend, with Codex in ten weeks against a suite of standard Git behavior, plus deterministic simulation tests that found race conditions.
- **estimate:** this adds a job; it saves the fix rounds of reference regressions found after merge, times `pr_p50` each.
- **verify:** a deliberate deviation from the reference fails the suite; existing checks are unchanged.
- **risk:** low
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/agent-conformance-suite.md), [OpenAI](https://openai.com/index/scaling-git-at-openai/)

### example-auto-runner: Run every example unattended and check each log against its source

- **applies when:** `agent_prs_per_day` over 5 and the repo has an examples or sample-apps directory that CI checks by exit code alone, or not at all.
- **how:** Recommend a runner that executes each example non-interactively, answers common prompts, keeps examples that need extra setup on a skip list, writes one log per example and a rerun file listing only the examples that need another run, then has an agent read each log against the example's source. The Agents SDK repositories built this; the JavaScript one also publishes packages to a local registry and tests installs on Node.js, Bun, Deno, Cloudflare Workers and a Vite React app.
- **estimate:** reruns cover only the listed examples: total example `run_s` times (1 minus the share that passed), per rerun.
- **verify:** a deliberately broken example shows up in the rerun file and in the agent's report; the skip list is reviewed and does not grow silently.
- **risk:** low
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/example-auto-runner.md), [OpenAI](https://developers.openai.com/blog/skills-agents-sdk)

### release-readiness-review: Review the diff since the last release tag before shipping

- **applies when:** `agent_prs_per_day` over 5 and releases ship from the default branch after a manual skim of the changelog (static: a release workflow on tags with no review step).
- **how:** Recommend an agent review that finds the previous release tag, diffs it against main, checks for compatibility breaks, regressions and missing migration or release-note updates, and makes a readiness call with an unblock checklist when blocked. Treat a green call as one reviewer's finding and keep every release check CI already runs. OpenAI's openai-agents-python#2480 carries such a report in its description, with the Python 3.9 drop rated moderate.
- **estimate:** no CI seconds saved; it saves hotfix releases, each costing one release run plus `pr_p50`.
- **verify:** the report appears on each release PR; release checks are unchanged.
- **risk:** low
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/release-readiness-review.md), [OpenAI](https://github.com/openai/openai-agents-python/pull/2480)

### agent-migration-recipes: Constrain agent migrations with a bounded recipe and validation

- **applies when:** a deprecation, upgrade or framework migration touches many targets or repositories, and large waves of agent PRs swamp review or conflict (`agent_prs_per_day` spikes over three times the median).
- **how:** Recommend a recipe per migration with every mapping spelled out, applied in bounded batches computed from the dependency graph, keeping only targets whose tests still pass and handing judgement calls to the owning team. Spotify listed about 1,800 downstream pipelines from lineage data and opened 240 migration PRs, against about 10 engineering weeks by hand. Stripe's AutoJDK opens bounded, rerunnable upgrade PRs from the build graph and merged 160+ in three months. Uber migrated over 75,000 test classes to JUnit 5 with OpenRewrite recipes per Bazel target, over 1.25 million lines in 4 months, reverting any target whose tests changed outcome.
- **estimate:** batching bounds concurrent runs: wave size times per-PR CI minutes, set below runner capacity so `wait_s` stays flat.
- **verify:** every migrated target's tests have the same outcome before and after; required checks are unchanged.
- **risk:** medium
- **mode:** report-only (agent-workflow)
- **evidence:** [StarSling](https://starsling.dev/ci-playbooks/techniques/agent-migration-recipes.md), [Spotify](https://engineering.atspotify.com/2026/4/background-coding-agents-dataset-migrations-honk-part-4), [Stripe](https://stripe.dev/blog/modern-java-at-stripe-language-upgrades-as-a-service), [Uber](https://www.uber.com/us/en/blog/junit-migration/)

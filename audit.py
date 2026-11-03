#!/usr/bin/env python3
"""fast-ci audit: compute the playbook's audit signals from a repo's recent GitHub Actions runs.

Read-only. Needs an authenticated `gh`. Standard library only.
  python3 audit.py --repo owner/name --out <dir outside the repo> [--limit 150] [--logs 15]
Writes <out>/signals.json and <out>/signals.md, and prints the markdown.
Job logs are read only to count cache hits; they are untrusted data and never printed.
"""
import argparse, base64, json, os, re, subprocess, sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

SETUP = re.compile(r"^(Set up |Complete |Post |Stop containers|Initialize containers|Setup |Install )|checkout|^Run actions/(setup-|cache)|^Run [\w.-]+/(setup-|action-setup)|install|npm ci|corepack|uv sync|restore|cache", re.I)
CHECKOUT = re.compile(r"checkout", re.I)
INSTALL = re.compile(r"install|uv sync|pnpm i\b|npm ci|bun i\b", re.I)
TOOL = re.compile(r"^Setup |^Set up (node|bun|uv|python|go|java)|/setup-|toolchain", re.I)
IMAGE = re.compile(r"docker pull|Initialize containers|pull image", re.I)
SHARD = re.compile(r"^(.*?)[\s(]*(?:shard\s*)?(\d+)\s*/\s*(\d+)\)?\s*$", re.I)
AGENT = re.compile(r"Co-Authored-By: (Claude|Codex|Cursor|Copilot|Devin)|Generated with \[Claude|codex", re.I)


def gh(path, raw=False, tries=2):
    for _ in range(tries):
        try:
            # Raw job logs carry terminal escapes; gh refuses them without this flag. They are only regex-matched, never printed.
            cmd = ["gh", "api", path] + (["--allow-escape-sequences"] if raw else [])
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        except subprocess.TimeoutExpired:
            continue
        if out.returncode == 0:
            return out.stdout if raw else json.loads(out.stdout)
    return None


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def secs(a, b):
    return max(0.0, (ts(b) - ts(a)).total_seconds()) if a and b else None


def p(xs, q):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))]


def job_split(job):
    out = dict(wait=secs(job["created_at"], job["started_at"]), total=secs(job["started_at"], job["completed_at"]),
               setup=0.0, checkout=0.0, install=0.0, tool=0.0, image=0.0, run=0.0)
    for st in job.get("steps") or []:
        d = secs(st.get("started_at"), st.get("completed_at")) or 0.0
        name = st["name"]
        if SETUP.search(name) or IMAGE.search(name):
            out["setup"] += d
            out["checkout"] += d if CHECKOUT.search(name) else 0
            out["install"] += d if INSTALL.search(name) and not CHECKOUT.search(name) else 0
            out["tool"] += d if TOOL.search(name) else 0
            out["image"] += d if IMAGE.search(name) else 0
        else:
            out["run"] += d
    return out


def static_signals(repo, ref):
    """Heuristic text scan of each workflow: jobs without timeout-minutes, PR workflows without concurrency."""
    files = gh(f"repos/{repo}/contents/.github/workflows?ref={ref}")
    if files is None:  # a failed read must not look like "no findings"
        return dict(no_timeout_jobs="unavailable", no_concurrency="unavailable", duplicate_steps="unavailable", workers_over_cores="unavailable")
    no_timeout, no_conc, over_cores, commands = [], [], [], defaultdict(set)
    for f in files:
        if not f["name"].endswith((".yml", ".yaml")):
            continue
        text = gh(f"repos/{repo}/contents/.github/workflows/{f['name']}?ref={ref}")
        if text is None:
            return dict(no_timeout_jobs="unavailable", no_concurrency="unavailable", duplicate_steps="unavailable", workers_over_cores="unavailable")
        body = base64.b64decode(text.get("content", "")).decode("utf-8", "replace")
        if "pull_request" in body and not re.search(r"(?m)^concurrency:", body):
            no_conc.append(f["name"])
        m = re.search(r"(?m)^jobs:\n", body)
        if not m:
            continue
        jobs = re.split(r"(?m)^  (?=[\w-]+:\s*$)", body[m.end():])
        for blk in jobs:
            name = blk.split(":", 1)[0].strip()
            if not name or name.startswith("#"):
                continue
            if "timeout-minutes" not in blk and "uses:" not in blk.split("steps:")[0]:
                no_timeout.append(f"{f['name']}:{name}")
            if re.search(r"nproc\)\s*\*\s*[2-9]|--maxWorkers=(1\d\d|[2-9]\d\d)%|-n\s+auto", blk):
                over_cores.append(f"{f['name']}:{name}")
            for cmd in re.findall(r"(?m)^\s+(?:-\s+)?run:\s*(.+)$", blk):
                if INSTALL.search(cmd) or re.search(r"\bbuild\b", cmd):
                    commands[(f["name"], cmd.strip())].add(name)
    # The same install or build command in more than one job of one workflow.
    dup = sorted(f"{wf}: {cmd}" for (wf, cmd), names in commands.items() if len(names) > 1)
    return dict(no_timeout_jobs=no_timeout, no_concurrency=no_conc, duplicate_steps=dup, workers_over_cores=over_cores)


def gh_or_404(path):
    """(data, ok): ok is True on success or a 404, False on any other failure."""
    try:
        out = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return None, False
    if out.returncode == 0:
        return json.loads(out.stdout), True
    return None, "HTTP 404" in out.stderr


def run_jobs(repo, run_id):
    """Every job of a run, across pages; None when any page cannot be read."""
    out, page = [], 1
    while True:
        got = gh(f"repos/{repo}/actions/runs/{run_id}/jobs?per_page=100&page={page}")
        if got is None:
            return None
        out += got.get("jobs", [])
        if len(got.get("jobs", [])) < 100:
            return out
        page += 1


def cache_hits(repo, job_ids):
    with ThreadPoolExecutor(6) as ex:
        logs = list(ex.map(lambda jid: gh(f"repos/{repo}/actions/jobs/{jid}/logs", raw=True) or "", job_ids))
    hits = sum(len(re.findall(r"Cache restored from key|Cache hit for:", log)) for log in logs)
    misses = sum(len(re.findall(r"Cache not found for input keys|cache is not found", log)) for log in logs)
    return (hits / (hits + misses)) if hits + misses else None, hits + misses


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=150)
    ap.add_argument("--logs", type=int, default=6, help="job logs sampled per event for the cache hit rate")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    meta = gh(f"repos/{a.repo}") or sys.exit(f"fast-ci audit: cannot read {a.repo} with gh")
    main_ref = meta["default_branch"]
    runs = []
    page = 1
    while len(runs) < a.limit:
        got = gh(f"repos/{a.repo}/actions/runs?per_page=100&page={page}&status=completed")
        if got is None:  # a missing page would silently shorten the history
            sys.exit(f"fast-ci audit: cannot read page {page} of the run history of {a.repo}")
        if not (got or {}).get("workflow_runs"):
            break
        runs += got["workflow_runs"]
        page += 1
    runs = runs[: a.limit]
    with ThreadPoolExecutor(8) as ex:
        jobs = list(ex.map(lambda r: run_jobs(a.repo, r["id"]), runs))
    jobs_unreadable = sum(js is None for js in jobs)
    jobs = [js or [] for js in jobs]
    json.dump(dict(runs=runs, jobs=jobs), open(os.path.join(a.out, "raw.json"), "w"))

    wf_change = (gh(f"repos/{a.repo}/commits?path=.github/workflows&sha={main_ref}&per_page=1") or [{}])
    wf_changed_at = wf_change[0].get("commit", {}).get("committer", {}).get("date") if wf_change else None
    era_all = runs
    # The dev loop is every run off the default branch: PRs, and pushes to feature branches.
    is_pr = lambda r: r["head_branch"] != main_ref or r["event"] in ("pull_request", "pull_request_target", "merge_group")
    is_main = lambda r: not is_pr(r)
    # Measure only the current workflow config when it has enough runs; older runs describe a CI that no longer exists.
    era = [i for i, r in enumerate(runs) if wf_changed_at and r["created_at"] > wf_changed_at]
    if len(era) >= 20:
        runs, jobs = [runs[i] for i in era], [jobs[i] for i in era]

    created = [ts(r["created_at"]) for r in runs]
    span_days = max(1 / 24, (max(created) - min(created)).total_seconds() / 86400) if runs else 1
    per_job = defaultdict(list)
    pr_walls, crit, crit_secs = [], Counter(), defaultdict(list)
    for r, js in zip(runs, jobs):
        js = [j for j in js if j.get("started_at") and j.get("completed_at") and j["conclusion"] != "skipped"]
        if not js:
            continue
        for j in js:
            # Baselines come from successful runs only, keyed by workflow and job, so a failing or
            # cancelled run, or another workflow's job of the same name, never skews them.
            if j["conclusion"] == "success":
                per_job[f"{r['name']} / {j['name']}"].append(job_split(j))
        if is_pr(r):
            pr_walls.append(secs(min(j["created_at"] for j in js), max(j["completed_at"] for j in js)))
            slow = max(js, key=lambda j: secs(j["created_at"], j["completed_at"]) or 0)
            crit[f"{r['name']} / {slow['name']}"] += 1
            crit_secs[f"{r['name']} / {slow['name']}"].append(secs(slow["created_at"], slow["completed_at"]))

    table = []
    for name, xs in per_job.items():
        tot = [x["wait"] + x["total"] for x in xs if x["wait"] is not None and x["total"] is not None]
        row = dict(job=name, n=len(xs), wait_s=p([x["wait"] for x in xs], .5), setup_s=p([x["setup"] for x in xs], .5),
                   run_s=p([x["run"] for x in xs], .5), total_p50=p(tot, .5), total_p95=p(tot, .95),
                   checkout_s=p([x["checkout"] for x in xs], .5), install_s=p([x["install"] for x in xs], .5),
                   tool_install_s=p([x["tool"] for x in xs], .5), image_pull_s=p([x["image"] for x in xs], .5))
        row["setup_share"] = round(row["setup_s"] / row["total_p50"], 2) if row["total_p50"] else None
        table.append(row)
    table.sort(key=lambda r: -(r["total_p50"] or 0))

    shards = defaultdict(list)
    for row in table:
        m = SHARD.match(row["job"])
        if m:
            shards[m.group(1).strip()].append(row["total_p50"] or 0)
    shard_skew = {k: round(max(v) / min(v), 2) for k, v in shards.items() if len(v) > 1 and min(v) > 0}

    by_branch = defaultdict(list)
    for r in runs:
        if is_pr(r):
            by_branch[(r["workflow_id"], r["head_branch"])].append(r)
    superseded = 0
    for rs in by_branch.values():
        rs.sort(key=lambda r: r["created_at"])
        for old, new in zip(rs, rs[1:]):
            if old["head_sha"] != new["head_sha"] and old["conclusion"] != "cancelled" and old["updated_at"] > new["created_at"]:
                superseded += 1

    # Flaky: the run passed only on a rerun of the same commit.
    flaky = [r for r in runs if r.get("run_attempt", 1) > 1 and r["conclusion"] == "success"]
    # Infrastructure: a failed job whose failing step is setup, or with no failed step at all (runner lost).
    # Cancellations are superseded runs, and timeouts are hangs, so neither counts.
    infra = [j for js in jobs for j in js if j.get("conclusion") == "failure" and not any(
        s.get("conclusion") == "failure" and not SETUP.search(s["name"]) for s in j.get("steps") or [])]
    timed_out = sum(j.get("conclusion") == "timed_out" for js in jobs for j in js)

    def sample(pred):
        ids = [j["id"] for r, js in zip(runs, jobs) if pred(r) for j in js if j.get("conclusion") != "skipped"]
        return ids[: a.logs]
    hit_pr, n_pr = cache_hits(a.repo, sample(is_pr))
    hit_main, n_main = cache_hits(a.repo, sample(is_main))
    # A 404 means no branch protection; any other failure leaves the required checks unknown.
    required, protection_ok = gh_or_404(f"repos/{a.repo}/branches/{main_ref}/protection/required_status_checks")
    required = required or {}
    rules = gh(f"repos/{a.repo}/rules/branches/{main_ref}")
    req = "unavailable" if rules is None or not protection_ok else sorted(
        {c.get("context") for c in required.get("checks", [])} |
        {c.get("context") for rl in rules if rl.get("type") == "required_status_checks"
         for c in rl.get("parameters", {}).get("required_status_checks", [])})

    pr_p50 = p(pr_walls, .5)
    sig = dict(
        repo=a.repo, default_branch=main_ref, runs=len(runs), runs_fetched=len(era_all), window_days=round(span_days, 1), measured_current_config=len(era) >= 20,
        workflows_changed_at=wf_changed_at,
        runs_since_workflow_change=len(era),
        runs_per_day=dict(pr=round(sum(map(is_pr, runs)) / span_days, 1), main=round(sum(map(is_main, runs)) / span_days, 1),
                          all=round(len(runs) / span_days, 1)),
        pr_p50=pr_p50, pr_p95=p(pr_walls, .95), jobs_unreadable=jobs_unreadable,
        critical_path={k: dict(slowest_in=round(v / max(1, sum(crit.values())), 2),
                               share_of_pr_p50=round(p(crit_secs[k], .5) / pr_p50, 2) if pr_p50 else None)
                       for k, v in crit.most_common(5)},
        cache_hit_pr=hit_pr, cache_hit_main=hit_main, cache_logs_read=dict(pr=n_pr, main=n_main),
        shard_skew=shard_skew, superseded_running=superseded,
        rerun_rate=round(len(flaky) / max(1, len(runs)), 3),
        infra_fail_rate=round(len(infra) / max(1, sum(len(js) for js in jobs)), 3), timed_out_jobs=timed_out,
        draft_runs="unavailable: the runs API carries no draft state; read the workflow's draft filter",
        irrelevant_runs="unavailable: needs each PR's changed files; compare paths filters with a docs-only PR",
        agent_prs_per_day=round(sum(1 for r in runs if is_pr(r) and (r["actor"]["login"].endswith("[bot]") or AGENT.search((r.get("head_commit") or {}).get("message", "")))) / span_days, 1),
        required_checks=req, jobs=table, **static_signals(a.repo, main_ref))
    json.dump(sig, open(os.path.join(a.out, "signals.json"), "w"), indent=1)

    f = lambda v: "-" if v is None else (f"{v:.0f}" if isinstance(v, float) else str(v))
    md = [f"# fast-ci audit: {a.repo}", "",
          f"{len(runs)} runs over {sig['window_days']} days ({'only runs since the last workflow change' if sig['measured_current_config'] else 'all fetched runs; too few since the last workflow change'}). Runs per day: {sig['runs_per_day']}. Workflows last changed {wf_changed_at}, {sig['runs_since_workflow_change']} runs since.",
          f"PR wall time p50 {f(sig['pr_p50'])}s, p95 {f(sig['pr_p95'])}s. Critical path (slowest_in: share of PR runs where the job was slowest; share_of_pr_p50: its p50 over pr_p50): {sig['critical_path']}. Unreadable job lists: {jobs_unreadable}.",
          f"Cache hit rate PR {sig['cache_hit_pr']} vs main {sig['cache_hit_main']} (from {n_pr} and {n_main} cache lookups in sampled logs).",
          f"shard_skew {shard_skew}; superseded_running {superseded}; rerun_rate {sig['rerun_rate']}; infra_fail_rate {sig['infra_fail_rate']}; timed_out_jobs {timed_out}; agent_prs_per_day {sig['agent_prs_per_day']}.",
          f"Required checks: {req or 'none declared'}. draft_runs and irrelevant_runs: unavailable, check by hand. no_timeout_jobs {sig['no_timeout_jobs']}; no_concurrency {sig['no_concurrency']}; duplicate_steps {sig['duplicate_steps']}; workers_over_cores {sig['workers_over_cores']}.",
          "", "| job | n | wait_s | setup_s | run_s | p50 | p95 | setup_share | checkout_s | install_s | tool_install_s |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    md[-2] = md[-2].replace("| n |", "| n (successful) |")
    md += [f"| {r['job']} | {r['n']} | {f(r['wait_s'])} | {f(r['setup_s'])} | {f(r['run_s'])} | {f(r['total_p50'])} | {f(r['total_p95'])} | {r['setup_share']} | {f(r['checkout_s'])} | {f(r['install_s'])} | {f(r['tool_install_s'])} |" for r in table[:25]]
    open(os.path.join(a.out, "signals.md"), "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()

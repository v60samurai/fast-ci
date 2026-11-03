"""Offline check of audit.py's signal rules, with gh replaced by fixture data. Run: python3 -I tests/audit_test.py"""
import base64, importlib.util, json, pathlib, sys, tempfile

sys.dont_write_bytecode = True  # keep the checkout clean

root = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("audit", root / "audit.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

WORKFLOW = """name: CI
on: [pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - run: npm ci
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - run: npm ci
      - run: TEST_CONCURRENCY="$(( $(nproc) * 2 ))" npm test
"""


def job(i, name, conclusion, start, end, failed_step=None, steps_extra=()):
    steps = [dict(name="Set up job", conclusion="success", started_at=start, completed_at=start),
             dict(name="Run npm test", conclusion="failure" if failed_step == "test" else "success", started_at=start, completed_at=end)]
    if failed_step == "setup":
        steps[0]["conclusion"] = "failure"
    return dict(id=i, name=name, conclusion=conclusion, created_at=start, started_at=start, completed_at=end, steps=steps + list(steps_extra))


T = "2026-11-0{}T10:{:02d}:00Z"
runs = [dict(id=n, name="CI", workflow_id=1, event="pull_request", head_branch=f"b{n % 2}", head_sha=f"s{n}",
             conclusion="success", run_attempt=2 if n == 3 else 1, created_at=T.format(1 + n // 50, n % 50),
             updated_at=T.format(1 + n // 50, n % 50 + 1), actor=dict(login="dev"), head_commit=dict(message="x"))
        for n in range(4)]
jobs = {
    0: [job(1, "lint", "success", T.format(1, 0), T.format(1, 1)), job(2, "test", "success", T.format(1, 0), T.format(1, 5))],
    1: [job(3, "lint", "failure", T.format(1, 1), T.format(1, 2), failed_step="setup"), job(4, "test", "success", T.format(1, 1), T.format(1, 6))],
    2: [job(5, "lint", "cancelled", T.format(1, 2), T.format(1, 3)), job(6, "test", "failure", T.format(1, 2), T.format(1, 4), failed_step="test")],
    3: [job(7, "lint", "success", T.format(1, 3), T.format(1, 4)), job(8, "test", "success", T.format(1, 3), T.format(1, 9))],
}
# Run 0 has 150 jobs over two pages; only the first page of a naive fetch would see the slow one.
jobs[0] += [job(100 + k, f"extra {k}", "success", T.format(1, 0), T.format(1, 1)) for k in range(148)]
jobs[0].append(job(999, "late page", "success", T.format(1, 0), T.format(1, 30)))


def fake_gh(path, raw=False, tries=2):
    if path == "repos/o/r":
        return dict(default_branch="main")
    if path.startswith("repos/o/r/actions/runs?"):
        return dict(workflow_runs=runs if "&page=1&" in path else [])
    if "/jobs?" in path:
        rid = int(path.split("/runs/")[1].split("/")[0])
        page = int(path.split("&page=")[1])
        return dict(jobs=jobs[rid][(page - 1) * 100: page * 100])
    if path.startswith("repos/o/r/commits?"):
        return []
    if path.endswith("/logs"):
        return "Cache restored from key: x" if raw else None
    if path.startswith("repos/o/r/contents/.github/workflows?"):
        return [dict(name="ci.yml")]
    if path.startswith("repos/o/r/contents/.github/workflows/ci.yml"):
        return dict(content=base64.b64encode(WORKFLOW.encode()).decode())
    if path.startswith("repos/o/r/rules/"):
        return []
    return None


audit.gh = fake_gh
audit.gh_or_404 = lambda path: (None, True)  # no branch protection
out = tempfile.mkdtemp()
sys.argv = ["audit.py", "--repo", "o/r", "--out", out, "--logs", "2"]
audit.main()
sig = json.load(open(f"{out}/signals.json"))
jobs_by = {r["job"]: r for r in sig["jobs"]}

assert sig["duplicate_steps"] == ["ci.yml: npm ci"], sig["duplicate_steps"]
assert sig["no_timeout_jobs"] == ["ci.yml:lint"], sig["no_timeout_jobs"]
assert sig["workers_over_cores"] == ["ci.yml:test"], sig["workers_over_cores"]
assert "CI / late page" in jobs_by, "jobs on the second page were dropped"
assert jobs_by["CI / test"]["n"] == 3, "failed jobs must not enter the baseline"
assert sig["rerun_rate"] == 0.25, sig["rerun_rate"]  # one of four runs passed only on a rerun
assert abs(sig["infra_fail_rate"] - 1 / 157) < 1e-3, sig["infra_fail_rate"]  # only the setup failure; not the cancel, not the test failure
assert sig["critical_path"]["CI / late page"]["slowest_in"] == 0.25, sig["critical_path"]
assert sig["draft_runs"].startswith("unavailable") and sig["irrelevant_runs"].startswith("unavailable")
assert sig["required_checks"] == [] and sig["jobs_unreadable"] == 0
print("PASS audit.py: duplicates, timeouts, cores, pagination, baselines, flakes, infra failures, critical path")

# Branch protection that fails for any reason but a 404 leaves the required checks unknown.
audit.gh_or_404 = lambda path: (None, False)
audit.main()
assert json.load(open(f"{out}/signals.json"))["required_checks"] == "unavailable"
print("PASS audit.py: unreadable branch protection reads as unavailable")

"""Key-free hosted native references, counterexamples and isolation controls."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / ".raw/integration"
OUTPUT = ROOT / "integration-results"


def native(task, name, expected, agent="oracle"):
    result_dir = RAW / "trials" / name
    command = ["harbor", "trial", "start", "-p", str(task), "-a", agent,
               "--trial-name", name, "--trials-dir", str(RAW / "trials")]
    with (RAW / (name + ".log")).open("w") as log:
        process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=600)
    result = json.loads((result_dir / "result.json").read_text())
    verdict_path = result_dir / "verifier/verdict.json"
    if not verdict_path.is_file():
        print((RAW / (name + ".log")).read_text()[-10000:])
        raise AssertionError("native verifier did not run: " + name)
    verdict = json.loads(verdict_path.read_text())
    summary = {"name": name, "expected_complete": expected, "verdict": verdict,
            "agent": agent, "exception_type": (result.get("exception_info") or {}).get("exception_type")}
    (OUTPUT / (name + ".json")).write_text(json.dumps(summary, indent=2) + "\n")
    boundary = verdict.get("isolation", {})
    isolated = all(boundary.get(key) is True for key in ("network_namespace_none", "network_probe_blocked", "no_inference_key", "no_docker_socket"))
    if process.returncode or verdict["complete"] != expected or not isolated:
        print(json.dumps({"name": name, "verdict": verdict, "exception": result.get("exception_info")}))
        raise AssertionError("unexpected native result")
    print(name, "passed")
    return summary


def control(original, name, answer, extra=""):
    target = RAW / "tasks" / name
    shutil.copytree(original, target)
    script = "#!/bin/bash\nset -euo pipefail\n" + extra
    script += "cat > /logs/artifacts/answer.json <<'ANSWER'\n" + json.dumps(answer) + "\nANSWER\n"
    (target / "solution/solve.sh").write_text(script)
    return target


def main():
    if os.environ.get("RUNNER_OS") != "Linux" or os.environ.get("GITHUB_REPOSITORY") != "CaoimhConway/workpaperbench":
        raise SystemExit("Container integration runs only in the dedicated hosted Actions repository")
    if any(k in os.environ for k in ("OPENROUTER_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY")):
        raise SystemExit("No paid key belongs in CI")
    RAW.mkdir(parents=True)
    OUTPUT.mkdir(exist_ok=True)
    results = []
    scope = os.environ.get("WPB_INTEGRATION_SCOPE", "full")
    if scope not in ("full", "smoke", "review"):
        raise ValueError("invalid integration scope")
    network_checks = """test ! -e /tests/gold.json
test ! -e /var/run/docker.sock
test ! -d /workspace/.git
test ! -e /workspace/prior-marker
touch /workspace/prior-marker
python - <<'BOUNDARY'
import os
from urllib.request import urlopen
assert not any(k in os.environ for k in ('GITHUB_TOKEN', 'GH_TOKEN', 'OPENROUTER_API_KEY'))
with urlopen('https://openrouter.ai/api/v1/models', timeout=20) as response:
    assert response.status == 200
for address in ('https://example.com', 'https://github.com'):
    blocked = False
    try:
        with urlopen(address, timeout=3):
            pass
    except Exception:
        blocked = True
    assert blocked, address
BOUNDARY
"""
    for task in sorted((ROOT / "tasks").glob("wp*")):
        ref = json.loads((task / "tests/reference.json").read_text())
        reference = control(task, task.name + "-reference", ref, network_checks)
        results.append(native(reference, task.name + "-reference", True))
        results.append(native(task, task.name + "-empty", False, "nop"))
        if scope in ("smoke", "review"):
            continue
        for index, wrapper in enumerate(("WITH c AS ({sql}) SELECT value FROM c", "SELECT value FROM ({sql})")):
            alternate = copy.deepcopy(ref)
            for claim in alternate["answers"]:
                if claim["sql"]:
                    claim["sql"] = wrapper.format(sql=claim["sql"])
            if task.name == "wp05" and index == 0:
                alternate["answers"][0]["evidence"] = ["export:periods"]
            if task.name == "wp04" and index == 0:
                alternate["conclusion"]["evidence"] = ["policy:window"]
            if task.name == "wp08" and index == 0:
                alternate["conclusion"]["evidence"] = ["policy:scope"]
            name = task.name + "-alternative-" + str(index)
            results.append(native(control(task, name, alternate), name, True))
        for index, mutation in enumerate(("constant", "citations", "abstain")):
            wrong = copy.deepcopy(ref)
            claim = next(a for a in wrong["answers"] if a["status"] == "answered")
            if mutation == "constant":
                claim["sql"] = "SELECT " + str(claim["value"]) + " AS value"
            elif mutation == "citations":
                claim["evidence"] = [e["id"] for e in json.loads((task / "tests/evidence.json").read_text())]
            else:
                claim.update(status="insufficient_evidence", value=None, sql=None, reason_code="missing_required_input")
            name = task.name + "-wrong-" + str(index)
            results.append(native(control(task, name, wrong), name, False))
    if scope == "full":
        original = ROOT / "tasks/wp06"
        wrong = json.loads((original / "tests/reference.json").read_text())
        wrong["answers"][1]["sql"] = "WITH common AS (SELECT network_asset FROM observations GROUP BY network_asset HAVING COUNT(DISTINCT period)=2), totals AS (SELECT period,SUM(amount_units) amount FROM observations JOIN common USING(network_asset) JOIN asset_tags USING(network_asset) GROUP BY period) SELECT 100.0*((SELECT amount FROM totals WHERE period='P2')-(SELECT amount FROM totals WHERE period='P1'))/(SELECT amount FROM totals WHERE period='P1') AS value"
        name = "wp06-matched-tag-join"
        results.append(native(control(original, name, wrong), name, False))
    if scope == "review":
        task = ROOT / "tasks/wp03"
        ref = json.loads((task / "tests/reference.json").read_text())
        for label, condition in (("date", "date(published_on)<=date('2024-07-05')"), ("lower", "published_on<='2024-07-05' AND lower(period)='p2'")):
            alternate = copy.deepcopy(ref)
            alternate["answers"][1]["sql"] = "SELECT transfer_units AS value FROM releases WHERE period='P2' AND " + condition + " ORDER BY published_on DESC LIMIT 1"
            name = "review-valid-" + label
            results.append(native(control(task, name, alternate), name, True))
        for label, sql in (("write-denied", "ATTACH DATABASE '/tmp/escape' AS x"), ("timeout", "WITH RECURSIVE t(n) AS (VALUES(1) UNION ALL SELECT n+1 FROM t) SELECT SUM(n) AS value FROM t")):
            wrong = copy.deepcopy(ref)
            wrong["answers"][0]["sql"] = sql
            name = "review-" + label
            results.append(native(control(task, name, wrong), name, False))
        name = "review-candidate-data-tamper"
        results.append(native(control(task, name, ref, "rm /workspace/data.sqlite\nprintf broken > /workspace/data.sqlite\n"), name, True))
        name = "review-extra-artifact"
        results.append(native(control(task, name, ref, "printf unexpected > /logs/artifacts/extra.txt\n"), name, False))
        extra = copy.deepcopy(ref)
        extra["answers"].append({**extra["answers"][0], "id": "unrequested"})
        name = "review-extra-claim"
        item = native(control(task, name, extra), name, False)
        assert item["verdict"]["checks"]["numerical"] is True
        results.append(item)
    if scope in ("smoke", "review"):
        (OUTPUT / "controls.json").write_text(json.dumps({"scope": scope, "run_id": os.environ["GITHUB_RUN_ID"], "commit": os.environ["GITHUB_SHA"], "controls": results}, indent=2) + "\n")
        return
    task = ROOT / "tasks/wp01"
    ref = json.loads((task / "tests/reference.json").read_text())
    for name, extra, expected in (
        ("candidate-data-tamper", "rm /workspace/data.sqlite\nprintf 'candidate mutation' > /workspace/data.sqlite\n", True),
        ("artifact-db-injection", "printf 'candidate database' > /logs/artifacts/data.sqlite\n", False),
        ("artifact-symlink", "ln -s /tests/reference.json /logs/artifacts/answer.json\n", False),
        ("artifact-oversize", "head -c 65537 /dev/zero > /logs/artifacts/answer.json\n", False),
    ):
        target = control(task, name, ref)
        if name.startswith("artifact-") and name != "artifact-db-injection":
            (target / "solution/solve.sh").write_text("#!/bin/bash\nset -euo pipefail\n" + extra)
        else:
            target = control(task, name + "-run", ref, extra)
        results.append(native(target, name, expected))
    forbidden = copy.deepcopy(ref)
    forbidden["answers"][0]["sql"] = "ATTACH DATABASE '/tmp/escape' AS x"
    results.append(native(control(task, "sql-denied", forbidden), "sql-denied", False))
    forbidden["answers"][0]["sql"] = "WITH RECURSIVE t(n) AS (VALUES(1) UNION ALL SELECT n+1 FROM t) SELECT SUM(n) AS value FROM t"
    results.append(native(control(task, "sql-timeout", forbidden), "sql-timeout", False))
    historical = ROOT / "reports/runs/pilot-wp05-A-2/answer.json"
    if historical.is_file():
        answer = json.loads(historical.read_text())
        name = "pilot-wp05-A-2-citation-regrade"
        results.append(native(control(ROOT / "tasks/wp05", name, answer), name, False))
    (OUTPUT / "controls.json").write_text(json.dumps({"scope": scope, "run_id": os.environ["GITHUB_RUN_ID"], "commit": os.environ["GITHUB_SHA"], "controls": results}, indent=2) + "\n")


if __name__ == "__main__":
    main()

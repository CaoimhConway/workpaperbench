"""Hosted native challenge references, alternatives and hostile outputs."""
import copy
import json
import os

from integration import ROOT, RAW, OUTPUT, control, native


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("RUNNER_OS") != "Linux":
        raise SystemExit("Challenge replay requires hosted Linux Actions")
    if any(key in os.environ for key in ("OPENROUTER_API_KEY", "GH_TOKEN", "GITHUB_TOKEN")):
        raise SystemExit("Key-free controls require an environment without credentials")
    RAW.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(exist_ok=True)
    results = []
    boundaries = """test ! -e /tests/gold.json
test ! -e /var/run/docker.sock
test ! -d /workspace/.git
test ! -e /workspace/prior-marker
touch /workspace/prior-marker
python - <<'CHECK'
from urllib.request import urlopen
with urlopen('https://openrouter.ai/api/v1/models', timeout=20) as response:
    assert response.status == 200
for url in ('https://example.com', 'https://github.com'):
    try:
        urlopen(url, timeout=3)
    except Exception:
        continue
    raise AssertionError('Unexpected candidate network access')
CHECK
"""
    for task in sorted((ROOT / "datasets/challenge-v1/tasks").iterdir()):
        ref = json.loads((task / "tests/reference.json").read_text())
        name = "challenge-" + task.name
        results.append(native(control(task, name + "-reference", ref, boundaries), name + "-reference", True))
        results.append(native(task, name + "-empty", False, "nop"))
        alternative = copy.deepcopy(ref)
        for claim in alternative["answers"]:
            if claim["sql"]:
                claim["sql"] = "WITH computed(result) AS (" + claim["sql"] + ") SELECT result AS analysis FROM computed"
        results.append(native(control(task, name + "-alias", alternative), name + "-alias", True))
        constant = copy.deepcopy(ref)
        for claim in constant["answers"]:
            if claim["sql"]:
                claim["sql"] = "SELECT " + str(claim["value"])
        results.append(native(control(task, name + "-constant", constant), name + "-constant", False))
        gold = json.loads((task / "tests/gold.json").read_text())
        equivalent = copy.deepcopy(ref)
        for claim in equivalent["answers"]:
            claim["evidence"] = gold["answers"][claim["id"]]["evidence"][-1]
        if equivalent["conclusion"]:
            equivalent["conclusion"]["evidence"] = gold["conclusion"]["evidence"][-1]
        results.append(native(control(task, name + "-evidence", equivalent), name + "-evidence", True))
        shared = copy.deepcopy(ref)
        shared["context_evidence"] = gold.get("context_evidence_allowed", [])
        for claim in shared["answers"]:
            claim["evidence"] = [e for e in claim["evidence"] if e not in shared["context_evidence"]]
        if shared["conclusion"]:
            shared["conclusion"]["evidence"] = [e for e in shared["conclusion"]["evidence"] if e not in shared["context_evidence"]]
        results.append(native(control(task, name + "-shared-context", shared), name + "-shared-context", True))
    task = ROOT / "datasets/challenge-v1/tasks/a01"
    ref = json.loads((task / "tests/reference.json").read_text())
    for label, sql in (("attach", "ATTACH DATABASE '/tmp/escape' AS other"),
                       ("write", "DELETE FROM financials"),
                       ("extension", "SELECT load_extension('/tmp/escape')"),
                       ("resource", "WITH RECURSIVE t(n) AS (VALUES(1) UNION ALL SELECT n+1 FROM t) SELECT SUM(n) FROM t")):
        answer = copy.deepcopy(ref)
        answer["answers"][0]["sql"] = sql
        results.append(native(control(task, "challenge-" + label, answer), "challenge-" + label, False))
    rejected = copy.deepcopy(ref)
    rejected["answers"].append(copy.deepcopy(ref["answers"][0]))
    rejected["answers"][0]["sql"] = "DELETE FROM financials"
    item = native(control(task, "challenge-duplicate", rejected), "challenge-duplicate", False)
    assert item["verdict"]["checks"]["robustness"] is None
    results.append(item)
    item = native(control(task, "challenge-pristine", ref, "rm /workspace/data.sqlite\nprintf broken > /workspace/data.sqlite\n"), "challenge-pristine", True)
    results.append(item)
    report = {"dataset_id": "challenge-v1", "run_id": os.environ["GITHUB_RUN_ID"],
              "commit_sha": os.environ["GITHUB_SHA"], "controls": results}
    (OUTPUT / "challenge-controls.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()

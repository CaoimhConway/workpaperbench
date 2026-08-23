"""Focused replay checks for evaluation-task alternatives and false passes."""
import json
from pathlib import Path

from workpaperbench.grading import grade, replay


ROOT = Path(__file__).resolve().parents[1]
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def reference(task_id):
    path = ROOT / "tasks" / task_id / "tests" / "reference.json"
    return json.loads(path.read_text())


def submit(tmp_path, task_id, answer):
    directory = tmp_path / task_id
    directory.mkdir()
    (directory / "answer.json").write_text(json.dumps(answer))
    return grade(directory, ROOT / "tasks" / task_id / "tests")


def test_wp03_accepts_latest_eligible_query_and_preliminary_context(tmp_path):
    answer = reference("wp03")
    answer["answers"][1]["sql"] = (
        "SELECT transfer_units AS value FROM releases "
        "WHERE period='P2' AND published_on<='2024-07-05' "
        "ORDER BY published_on DESC LIMIT 1"
    )
    answer["answers"][1]["evidence"] = [
        "release:20240703",
        "policy:selection",
        "release:20240702",
    ]
    answer["answers"][2]["evidence"].append("release:20240702")
    answer["conclusion"]["evidence"].append("release:20240702")

    result = submit(tmp_path, "wp03", answer)

    assert result["complete"]


def test_wp03_rejects_late_revision_and_zero_for_missing_usd(tmp_path):
    answer = reference("wp03")
    p2 = answer["answers"][1]
    p2["value"] = 90
    p2["evidence"] = ["release:20240710", "policy:selection"]
    p2["sql"] = (
        "SELECT transfer_units AS value FROM releases WHERE period='P2' "
        "ORDER BY published_on DESC LIMIT 1"
    )
    usd = answer["answers"][3]
    usd.update(
        status="answered",
        value=0,
        evidence=["valuation:availability"],
        sql="SELECT 0 AS value",
        reason_code=None,
    )

    result = submit(tmp_path, "wp03", answer)

    assert not result["complete"]
    assert "p2_total:numerical" in result["errors"]
    assert "p2_total:evidence_context" in result["errors"]
    assert "p2_usd_value:availability_or_unit" in result["errors"]


def test_wp03_does_not_accept_not_established_for_supported_growth(tmp_path):
    answer = reference("wp03")
    answer["conclusion"].update(
        verdict="not_established",
        reason_code="missing_required_evidence",
    )

    result = submit(tmp_path, "wp03", answer)

    assert not result["complete"]
    assert result["checks"]["conclusion"] is False


def test_wp04_accepts_exclude_then_group_alternative(tmp_path):
    answer = reference("wp04")
    answer["answers"][1]["sql"] = (
        "WITH non_mint AS ("
        f"SELECT tx_id,amount_base_units FROM events WHERE sender!='{ZERO_ADDRESS}' "
        f"AND recipient!='{ZERO_ADDRESS}'"
        "), per_tx AS (SELECT tx_id,MAX(amount_base_units) AS amount "
        "FROM non_mint GROUP BY tx_id) "
        "SELECT SUM(amount)/1000000.0 AS value FROM per_tx"
    )
    answer["answers"][1]["evidence"].append("policy:window")

    result = submit(tmp_path, "wp04", answer)

    assert result["complete"]


def test_wp04_rejects_max_before_mint_exclusion(tmp_path):
    answer = reference("wp04")
    query = (
        "WITH txmax AS (SELECT tx_id,MAX(amount_base_units) AS amount FROM events GROUP BY tx_id), "
        f"eligible_tx AS (SELECT DISTINCT tx_id FROM events WHERE sender!='{ZERO_ADDRESS}' "
        f"AND recipient!='{ZERO_ADDRESS}') "
        "SELECT SUM(amount)/1000000.0 AS value FROM txmax JOIN eligible_tx USING(tx_id)"
    )
    value = replay(query, ROOT / "tasks/wp04/tests/data.sqlite")
    assert value == 925
    answer["answers"][1].update(value=value, sql=query)

    result = submit(tmp_path, "wp04", answer)

    assert not result["complete"]
    assert "max_per_tx:numerical" in result["errors"]
    assert "max_per_tx:replay" in result["errors"]


def test_wp06_accepts_intersect_for_matched_coverage(tmp_path):
    answer = reference("wp06")
    answer["answers"][1]["sql"] = (
        "WITH common AS ("
        "SELECT network_asset FROM observations WHERE period='P1' "
        "INTERSECT SELECT network_asset FROM observations WHERE period='P2'"
        "), totals AS (SELECT period,SUM(amount_units) AS amount FROM observations "
        "JOIN common USING(network_asset) GROUP BY period) "
        "SELECT 100.0*((SELECT amount FROM totals WHERE period='P2')-"
        "(SELECT amount FROM totals WHERE period='P1'))/"
        "(SELECT amount FROM totals WHERE period='P1') AS value"
    )

    result = submit(tmp_path, "wp06", answer)

    assert result["complete"]


def test_wp06_rejects_blind_one_to_many_tag_join(tmp_path):
    answer = reference("wp06")
    query = (
        "SELECT 100.0*(SUM(CASE WHEN period='P2' THEN amount_units ELSE 0 END)-"
        "SUM(CASE WHEN period='P1' THEN amount_units ELSE 0 END))/"
        "SUM(CASE WHEN period='P1' THEN amount_units ELSE 0 END) AS value "
        "FROM observations JOIN asset_tags USING(network_asset)"
    )
    value = replay(query, ROOT / "tasks/wp06/tests/data.sqlite")
    assert value == 150
    answer["answers"][0].update(value=value, sql=query)

    result = submit(tmp_path, "wp06", answer)

    assert not result["complete"]
    assert "reported_growth:numerical" in result["errors"]
    assert "reported_growth:replay" in result["errors"]


def test_wp07_accepts_scalar_subquery_margin_change(tmp_path):
    answer = reference("wp07")
    answer["answers"][3]["sql"] = (
        "SELECT 100.0*((SELECT gross_profit_million FROM services WHERE entity='Apple' AND fiscal_year=2024 AND period='Q2')*1.0/"
        "(SELECT revenue_million FROM services WHERE entity='Apple' AND fiscal_year=2024 AND period='Q2')-"
        "((SELECT gross_profit_million FROM services WHERE entity='Apple' AND fiscal_year=2024 AND period='H1')-"
        "(SELECT gross_profit_million FROM services WHERE entity='Apple' AND fiscal_year=2024 AND period='Q2'))*1.0/"
        "((SELECT revenue_million FROM services WHERE entity='Apple' AND fiscal_year=2024 AND period='H1')-"
        "(SELECT revenue_million FROM services WHERE entity='Apple' AND fiscal_year=2024 AND period='Q2'))) AS value"
    )

    result = submit(tmp_path, "wp07", answer)

    assert result["complete"]


def test_wp07_distinguishes_percentage_points_and_fy2024_evidence(tmp_path):
    answer = reference("wp07")
    answer["answers"][3]["unit"] = "percent"
    answer["answers"][0]["evidence"] = ["filing:comparative"]

    result = submit(tmp_path, "wp07", answer)

    assert not result["complete"]
    assert "margin_change:availability_or_unit" in result["errors"]
    assert "q1_revenue:evidence_context" in result["errors"]


def test_wp08_rejects_payment_and_human_inference_from_transfer_rows(tmp_path):
    answer = reference("wp08")
    answer["answers"][1].update(
        status="answered",
        value=775,
        evidence=["corpus:events", "policy:scope"],
        sql=(
            f"SELECT SUM(amount_base_units)/1000000.0 AS value FROM events WHERE sender!='{ZERO_ADDRESS}' "
            f"AND recipient!='{ZERO_ADDRESS}'"
        ),
        reason_code=None,
    )
    answer["answers"][2].update(
        status="answered",
        value=4,
        evidence=["corpus:events", "policy:scope"],
        sql="SELECT COUNT(DISTINCT sender) AS value FROM events",
        reason_code=None,
    )
    answer["conclusion"].update(
        verdict="supported",
        reason_code="supported_by_calculation",
        evidence=["corpus:events", "policy:scope", "policy:counting"],
    )

    result = submit(tmp_path, "wp08", answer)

    assert not result["complete"]
    assert "business_payment_volume:availability_or_unit" in result["errors"]
    assert "unique_humans:availability_or_unit" in result["errors"]
    assert result["checks"]["conclusion"] is False

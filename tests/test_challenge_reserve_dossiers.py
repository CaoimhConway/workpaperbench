"""Trusted source and Decimal checks for the three reserve dossiers."""
import hashlib
import json
from decimal import Decimal
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
AUTHORING = ROOT / "datasets/challenge-v1/authoring"
RAW = ROOT / ".raw/challenge-sources"
ZERO = Decimal(0)


def dec(value):
    return Decimal(str(value))


def load_case(key):
    folder = AUTHORING / key
    return folder, json.loads((folder / "definition.json").read_text()), json.loads((folder / "source_capture.json").read_text())


def circle_results(tables):
    assets = {}
    for date in ("2025-03-19", "2025-03-31"):
        assets[date] = sum((dec(row[3]) for row in tables["reserve_components"]["rows"] if row[0] == date), ZERO)
    circulation = {}
    for date in assets:
        rows = [row for row in tables["circulation_inputs"]["rows"] if row[0] == date]
        gross = sum((dec(row[2]) for row in rows if row[1] == "total supply"), ZERO)
        excluded = sum((dec(row[2]) for row in rows if row[1] != "total supply"), ZERO)
        circulation[date] = gross - excluded
    reported = {row[0]: dec(row[1]) for row in tables["reported_reserve_totals"]["rows"]}
    change = Decimal(10000) * (assets["2025-03-31"] / circulation["2025-03-31"] - assets["2025-03-19"] / circulation["2025-03-19"])
    return {
        "march31_reserves_usd": assets["2025-03-31"],
        "march31_circulation_usdc": circulation["2025-03-31"],
        "march31_residual_usd": reported["2025-03-31"] - assets["2025-03-31"],
        "coverage_change_bps": change,
        "conclusion": "supported" if all(assets[date] > circulation[date] for date in assets) else "contradicted",
    }


def tether_results(tables):
    assets = sum((dec(row[2]) for row in tables["reserve_components"]["rows"]), ZERO)
    amounts = {row[1]: dec(row[2]) for row in tables["liability_inputs"]["rows"]}
    token_liability = amounts["gross contractual redemption"] - amounts["company-held tokens not in Treasury wallet"]
    company_excess = assets - amounts["detailed FFR company total liabilities"]
    release_delta = amounts["July release company total liabilities"] - amounts["detailed FFR company total liabilities"]
    return {
        "reserve_assets_usd": assets,
        "net_token_liability_usd": token_liability,
        "company_asset_excess_usd": company_excess,
        "release_liability_delta_usd": release_delta,
        "conclusion": "supported" if release_delta == 0 else "contradicted",
    }


def ripple_results(tables):
    assets = {}
    for date in ("2025-05-22", "2025-05-30", "2025-06-09", "2025-06-30"):
        assets[date] = sum((dec(row[2]) for row in tables["reserve_components"]["rows"] if row[0] == date), ZERO)
    balances = {row[0]: (dec(row[1]), dec(row[2])) for row in tables["reported_balances"]["rows"]}
    change = Decimal(10000) * (assets["2025-06-30"] / balances["2025-06-30"][0] - assets["2025-05-30"] / balances["2025-05-30"][0])
    return {
        "jun30_reserves_usd": assets["2025-06-30"],
        "jun30_reconciliation_usd": balances["2025-06-30"][1] - assets["2025-06-30"],
        "coverage_change_bps": change,
        "conclusion": "supported" if change > 0 else "contradicted",
    }


CALCULATORS = {"b02": circle_results, "b03": tether_results, "b04": ripple_results}


class ReserveDossierTests(unittest.TestCase):
    def assert_result_matches(self, definition, result):
        answers = definition["gold"]["answers"]
        self.assertEqual(set(result) - {"conclusion"}, set(answers))
        for claim_id, expected in answers.items():
            self.assertEqual(expected["status"], "answered")
            self.assertLessEqual(abs(dec(expected["value"]) - result[claim_id]), dec(expected["tolerance"]))
            if claim_id == "coverage_change_bps":
                self.assertEqual(expected["unit"], "basis_points")
                self.assertEqual(dec(expected["tolerance"]), Decimal("0.005"))
            else:
                self.assertIn(expected["unit"], ("usd", "usdc"))
                self.assertEqual(dec(expected["tolerance"]), Decimal("0.5"))
        self.assertEqual(definition["gold"]["conclusion"]["verdict"], result["conclusion"])

    def test_source_captures_and_evidence_hashes_are_bound(self):
        for key in ("b02", "b03", "b04"):
            folder, definition, capture = load_case(key)
            extract = folder / capture["retained_extract"]
            extract_hash = hashlib.sha256(extract.read_bytes()).hexdigest()
            self.assertEqual(capture["retained_extract_sha256"], extract_hash)
            self.assertTrue(all(item["capture_sha256"] == extract_hash for item in definition["evidence"]))
            for raw in capture["raw_files_retained"]:
                source = RAW / raw["raw_file"]
                self.assertGreater(raw["bytes"], 0)
                self.assertEqual(len(raw["sha256"]), 64)
                if source.exists():
                    self.assertEqual(raw["bytes"], source.stat().st_size)
                    self.assertEqual(raw["sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
            metadata_name = capture.get("release_metadata_file")
            if metadata_name:
                metadata = RAW / metadata_name
                self.assertEqual(len(capture["release_metadata_sha256"]), 64)
                if metadata.exists():
                    self.assertEqual(capture["release_metadata_sha256"], hashlib.sha256(metadata.read_bytes()).hexdigest())
            evidence_ids = {item["id"] for item in definition["evidence"]}
            self.assertTrue(all(identifier in definition["context"] for identifier in evidence_ids))
            for table in definition["tables"].values():
                self.assertTrue(all(row[-1] in evidence_ids for row in table["rows"]))
            for answer in definition["gold"]["answers"].values():
                for path in answer["evidence"]:
                    self.assertTrue(set(path) <= evidence_ids)
            for source in capture["sources"]:
                if source["raw_file"].endswith(".pdf"):
                    self.assertEqual(source["publication"], "unknown")
                    self.assertIsNotNone(source["report_signed_date"])
            if key == "b03":
                release = next(source for source in capture["sources"] if source["raw_file"].endswith(".html"))
                self.assertEqual(release["publication_date"], "2025-07-31")
                self.assertEqual(release["publication_time"], "unknown")
            for table in definition["tables"].values():
                columns = table["schema"].split("(", 1)[1].rsplit(")", 1)[0].split(",")
                self.assertTrue(all(len(row) == len(columns) for row in table["rows"]))
            for control in definition["controls"]:
                self.assertEqual(set(control["tables"]), set(definition["tables"]))
                for table_name, table in control["tables"].items():
                    self.assertEqual(table["schema"], definition["tables"][table_name]["schema"])
                    columns = table["schema"].split("(", 1)[1].rsplit(")", 1)[0].split(",")
                    self.assertTrue(all(len(row) == len(columns) for row in table["rows"]))

    def test_circle_displayed_precision_and_calculation(self):
        _, definition, _ = load_case("b02")
        result = circle_results(definition["tables"])
        self.assertEqual(result["march31_reserves_usd"], Decimal("60040707041"))
        self.assertEqual(result["march31_circulation_usdc"], Decimal("59975771715"))
        self.assertEqual(result["march31_residual_usd"], Decimal("-1"))
        self.assertEqual(result["conclusion"], "supported")
        self.assertEqual(sum(1 for row in definition["tables"]["reserve_components"]["rows"] if row[0] == "2025-03-19" and row[1] == "U.S. Treasury security fair value"), 13)
        self.assertEqual(sum(1 for row in definition["tables"]["reserve_components"]["rows"] if row[0] == "2025-03-31" and row[1] == "U.S. Treasury security fair value"), 16)
        self.assertEqual(len([row for row in definition["tables"]["circulation_inputs"]["rows"] if row[0] == "2025-03-31"]), 3)
        self.assert_result_matches(definition, result)

    def test_tether_scopes_and_calculation(self):
        _, definition, _ = load_case("b03")
        result = tether_results(definition["tables"])
        self.assertEqual(result["reserve_assets_usd"], Decimal("162574933798"))
        self.assertEqual(result["net_token_liability_usd"], Decimal("157100255857"))
        self.assertEqual(result["company_asset_excess_usd"], Decimal("5466933324"))
        self.assertEqual(result["release_liability_delta_usd"], Decimal("9000"))
        self.assertEqual(len(definition["tables"]["reserve_components"]["rows"]), 11)
        self.assert_result_matches(definition, result)

    def test_ripple_month_end_comparison_and_calculation(self):
        _, definition, _ = load_case("b04")
        result = ripple_results(definition["tables"])
        self.assertEqual(result["jun30_reserves_usd"], Decimal("471227699"))
        self.assertEqual(result["jun30_reconciliation_usd"], Decimal(0))
        self.assertLess(result["coverage_change_bps"], Decimal(0))
        for date in ("2025-05-22", "2025-05-30", "2025-06-09", "2025-06-30"):
            component_sum = sum((dec(row[2]) for row in definition["tables"]["reserve_components"]["rows"] if row[0] == date), ZERO)
            reported = next(dec(row[2]) for row in definition["tables"]["reported_balances"]["rows"] if row[0] == date)
            self.assertEqual(component_sum, reported)
        self.assert_result_matches(definition, result)

    def test_synthetic_controls_recompute_and_change_every_claim(self):
        for key, calculate in CALCULATORS.items():
            _, definition, _ = load_case(key)
            baseline = calculate(definition["tables"])
            self.assert_result_matches(definition, baseline)
            changed = {claim_id: False for claim_id in definition["gold"]["answers"]}
            for control in definition["controls"]:
                actual = calculate(control["tables"])
                expected = control["expected"]
                self.assertEqual(set(expected), set(definition["gold"]["answers"]) | {"conclusion"})
                for claim_id, claim_definition in definition["gold"]["answers"].items():
                    difference = abs(dec(expected[claim_id]) - actual[claim_id])
                    self.assertLessEqual(difference, dec(claim_definition["tolerance"]))
                    if abs(actual[claim_id] - baseline[claim_id]) > dec(claim_definition["tolerance"]):
                        changed[claim_id] = True
                self.assertEqual(expected["conclusion"], actual["conclusion"])
            self.assertTrue(all(changed.values()), (key, changed))

    def test_evaluation_dossier_shape_and_version(self):
        for key in ("b02", "b03", "b04"):
            _, definition, capture = load_case(key)
            self.assertEqual(definition["split"], "evaluation")
            self.assertEqual(definition["family"], "B")
            self.assertEqual(definition["scorer_version"], "challenge-1.1.0")
            self.assertFalse(definition["previously_exposed"])
            self.assertGreaterEqual(len(definition["evidence"]), 4)
            self.assertLessEqual(len(definition["evidence"]), 10)
            self.assertGreaterEqual(len(definition["controls"]), 2)
            self.assertLessEqual(len(definition["controls"]), 4)
            self.assertEqual(capture["capture_timestamp_basis"], "local source-file modification time in UTC, not an original server retrieval timestamp")
            reference = {answer["id"]: answer for answer in definition["reference"]["answers"]}
            self.assertEqual(set(reference), set(definition["gold"]["answers"]))
            for claim_id, gold in definition["gold"]["answers"].items():
                self.assertEqual(reference[claim_id]["unit"], gold["unit"])
                self.assertTrue(reference[claim_id]["sql"])
                self.assertEqual(reference[claim_id]["status"], gold["status"])


if __name__ == "__main__":
    unittest.main()

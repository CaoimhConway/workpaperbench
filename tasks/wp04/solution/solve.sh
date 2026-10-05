#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "wp04",
  "answers": [
    {
      "id": "all_events",
      "status": "answered",
      "value": 775,
      "unit": "token_units",
      "evidence": [
        "corpus:events",
        "policy:counting",
        "metadata:token"
      ],
      "sql": "SELECT SUM(amount_base_units)/1000000.0 AS value FROM events WHERE sender!='0x0000000000000000000000000000000000000000' AND recipient!='0x0000000000000000000000000000000000000000'",
      "reason_code": null
    },
    {
      "id": "max_per_tx",
      "status": "answered",
      "value": 675,
      "unit": "token_units",
      "evidence": [
        "corpus:events",
        "policy:counting",
        "metadata:token"
      ],
      "sql": "SELECT SUM(amount)/1000000.0 AS value FROM (SELECT tx_id,MAX(amount_base_units) amount FROM events WHERE sender!='0x0000000000000000000000000000000000000000' AND recipient!='0x0000000000000000000000000000000000000000' GROUP BY tx_id)",
      "reason_code": null
    },
    {
      "id": "difference",
      "status": "answered",
      "value": 100,
      "unit": "token_units",
      "evidence": [
        "corpus:events",
        "policy:counting",
        "metadata:token"
      ],
      "sql": "WITH eligible AS (SELECT tx_id,amount_base_units FROM events WHERE sender!='0x0000000000000000000000000000000000000000' AND recipient!='0x0000000000000000000000000000000000000000'), by_tx AS (SELECT tx_id,MAX(amount_base_units) amount FROM eligible GROUP BY tx_id) SELECT ((SELECT SUM(amount_base_units) FROM eligible)-(SELECT SUM(amount) FROM by_tx))/1000000.0 AS value",
      "reason_code": null
    }
  ],
  "conclusion": {
    "verdict": "not_established",
    "reason_code": "missing_required_evidence",
    "evidence": [
      "corpus:events",
      "policy:window",
      "policy:counting"
    ]
  }
}
ANSWER

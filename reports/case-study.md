# A correct growth figure can hide an incorrect formula

## The observation

In the first frozen campaign, Hermes Agent using `qwen/qwen3.6-35b-a3b` returned the correct period totals and growth figure for task `wp03`. Its submitted growth calculation was nevertheless wrong.

This is an actual saved model submission on an **explicitly synthetic dated-release fixture**. It is not evidence of a defect in a financial product or an observed on-chain series. It is one inspectable failure, not an estimate of how often the model fails.

| Input | P1 | P2 | Correct growth | Submitted expression |
|---|---:|---:|---:|---:|
| Original fixture | 100 | 120 | 20% | 20 |
| Declared changed-input control | 120 | 150 | 25% | 50 |

The submitted expression, with its two source selections abbreviated, is:

```sql
P2 - P1 * 100.0 / P1
```

The required calculation is:

```sql
100.0 * (P2 - P1) / P1
```

Multiplication and division occur before subtraction. In the original fixture, the submitted expression accidentally agrees with percentage growth because P1 is 100. When P1 changes to 120, that agreement disappears.

## What the original grader actually reported

The original saved verdict has `numerical: true` and `replay: false`. It also reports failed evidence and conclusion checks. The submission omits the required `AS value` column alias from its numerical queries and does not supply every required evidence identifier.

Consequently, **the changed-input formula error was not isolated as the sole cause of the original replay failure**. The original worker can reject the query at its column-name check before assessing the changed result. The table above is a separate arithmetic inspection of the submitted expression, not a repaired submission or replacement score.

The conclusion's proposition was `supported`, as required. Its aggregate conclusion check also includes reason-code and citation requirements. A failed aggregate flag must not automatically be described as a wrong financial verdict.

## Reproduce the arithmetic without credentials or containers

This short example evaluates only the two authored expressions shown above against literal fixture values. It does not execute an arbitrary downloaded model program.

```python
import sqlite3

with sqlite3.connect(":memory:") as connection:
    for p1, p2 in [(100, 120), (120, 150)]:
        submitted, correct = connection.execute(
            "SELECT ? - ? * 100.0 / ?, 100.0 * (? - ?) / ?",
            (p2, p1, p1, p2, p1, p1),
        ).fetchone()
        print(p1, p2, submitted, correct)
```

Expected output:

```text
100 120 20.0 20.0
120 150 50.0 25.0
```

## Evidence and identity

- Slot: `final-wp03-A-1`, baseline, first repetition.
- Campaign: `wpb-v1-92baa4a72f0e`.
- Executed commit: `b4e256dc8976223a8a3fdad157a6b212f49bb8e1`.
- [Original Actions run](https://github.com/CaoimhConway/workpaperbench/actions/runs/37280454673).
- Artifact ID: `11334520085`, uploaded 2026-10-05 at 08:45:01 UTC.
- Artifact ZIP SHA-256: `56ebdd836fc3bfadacbfdb4b554c72a24db2288fdf0a10c6dd9ba851518da646`.
- [Frozen task and reference values](https://github.com/CaoimhConway/workpaperbench/blob/b4e256dc8976223a8a3fdad157a6b212f49bb8e1/sources/wp03.json).

The historical collector retained normalized `answer.json`, not the original raw answer bytes. Its recorded `answer_sha256` describes the missing raw serialization. It must not be represented as the hash of the normalized file. The artifact ZIP digest identifies the downloaded evidence bundle, and the distinction remains part of the provenance record.

## Why this matters

Checking a reported number asks whether one output matches one reference. Replaying the calculation on changed inputs asks an additional question: does the submitted method actually recompute the requested quantity?

This example supports the second check. It does not prove that two fixtures establish general SQL correctness, that a prompt intervention improves performance, or that this small suite measures production financial-research reliability.

The next requirement is a complete, consistently graded campaign with original and corrected verdicts kept separate. No favorable trial is substituted for a failed one, and no model call is needed merely to inspect this example.

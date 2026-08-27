# A correct 20% answer with an incorrect growth formula

In recorded trial **`final-wp03-A-1`**, Hermes Agent using the configured Qwen model returned the correct period totals and growth. Its submitted SQL did not implement the growth formula. The original data happened to conceal that error.

[Unchanged retained answer](runs/final-wp03-A-1/answer.json) · [Original verdict](runs/final-wp03-A-1/verdict.json) · [Execution record](runs/final-wp03-A-1/record.json) · [Task and reference data](../sources/wp03.json)

## The work request

Select releases eligible at the July 5, 2024 cutoff, calculate P1-to-P2 transfer growth on the same supplied token/network coverage, and identify whether a USD value is supported. This is an explicitly synthetic dated-release case, not observed USDC activity.

The eligible totals are 100 and 120 token units. The agent reported both and reported 20% growth. It also correctly declined a USD value without a supplied valuation input.

## The submitted calculation

The growth expression below preserves the submitted SQL with line breaks added for readability:

```sql
SELECT (SELECT transfer_units FROM releases WHERE release_id='r-p2-20240703')
     - (SELECT transfer_units FROM releases WHERE release_id='r-p1-20240701')
     * 100.0
     / (SELECT transfer_units FROM releases WHERE release_id='r-p1-20240701')
```

Multiplication and division apply before subtraction. The expression computes `P2 - P1 * 100 / P1`, not `(P2 - P1) * 100 / P1`.

| Input | P1 | P2 | Submitted expression | Correct growth |
|---|---:|---:|---:|---:|
| Original task | 100 | 120 | 20 | 20% |
| Declared changed-input control | 120 | 150 | 50 | 25% |

With P1 equal to 100, the wrong expression and the correct formula coincide. Changing the operands reveals the error without another model call.

## What the verdict does and does not establish

The original saved verdict has `numerical: true`, `replay: false` and `complete: false`. It also reports failed evidence and conclusion checks. The submitted SQL lacks the required `AS value` alias, so the strict original replay fails before it can isolate the changed-input error. Its citations also omit the selection-rule identifier.

**This case is not proof that the original grader rejected the answer solely because it detected the formula error.** The formula diagnosis follows from inspecting the recorded expression and independently calculating it on both fixtures. Neither the submission nor its original score has been repaired. The supported conclusion verdict is correct even though its full citation contract fails.

The takeaway is narrower and useful: checking the final scalar alone would miss a wrong calculation that happens to work on one input. Replay, controlled input changes and separate diagnostics make that difference inspectable.

## Reproduce the arithmetic without containers

This checks only the two authored expressions shown above against literal fixture values. It does not execute an arbitrary downloaded model program or change an official score.

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

Expected output: `100 120 20.0 20.0` and `120 150 50.0 25.0`.

The test `test_authored_formula_control_exposes_accidentally_correct_number` separately confirms that the reviewed grader detects this mechanism when the authored control satisfies the other output requirements. This is a grader test, not a repaired model submission.

## Evidence identity

The original campaign is `wpb-v1-92baa4a72f0e`, executed at `b4e256dc8976223a8a3fdad157a6b212f49bb8e1` in [run 37280454673](https://github.com/CaoimhConway/workpaperbench/actions/runs/37280454673). Artifact `11334520085` was uploaded on 2026-10-05 at 08:45:01 UTC. Its ZIP SHA-256 is `56ebdd836fc3bfadacbfdb4b554c72a24db2288fdf0a10c6dd9ba851518da646`.

The legacy runner retained normalized JSON, not the raw serialization described by its `answer_sha256`. The collected artifact audit identifies the retained-file hash separately. Missing original bytes are not reconstructed from a digest. The [previously preserved evidence copy](evidence/final-wp03-A-1/answer.json) is also retained.

## Why this case leads

This was the first inspected evaluation artifact with a correct scalar and a demonstrably wrong submitted calculation. It was not selected because a treatment improved it. The full results retain all collected attempts, including successes, infrastructure failures and regressions. One failure does not establish an error rate, a general model ranking or treatment effectiveness.

[Results and completeness status](results.md) · [Scoring and correction policy](../docs/METHODOLOGY.md)

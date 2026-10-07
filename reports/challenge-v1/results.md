# Research Challenge results

Full dossiers, neutral shared instructions. Model comparisons are separate from the historical prompt-arm experiments.

## pilot - challenge-v1-development-7e8903385beb

| Scope | Model | Financial / assessed | Evidence / assessed | Robustness / assessed | Verified / scheduled | Delivery / assessed | Strict / scheduled | Verdict coverage |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | inexpensive | 5 / 9 | 4 / 9 | 3 / 9 | 1 / 9 | 9 / 9 | 1 / 9 | 9 / 9 |
| a01 | inexpensive | 3 / 3 | 1 / 3 | 1 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 |
| b01 | inexpensive | 0 / 3 | 2 / 3 | 0 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 |
| c01 | inexpensive | 2 / 3 | 1 / 3 | 2 / 3 | 1 / 3 | 3 / 3 | 1 / 3 | 3 / 3 |
| family-A | inexpensive | 3 / 3 | 1 / 3 | 1 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 |
| family-B | inexpensive | 0 / 3 | 2 / 3 | 0 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 |
| family-C | inexpensive | 2 / 3 | 1 / 3 | 2 / 3 | 1 / 3 | 3 / 3 | 1 / 3 | 3 / 3 |
| all | reference | 2 / 9 | 7 / 9 | 6 / 9 | 2 / 9 | 9 / 9 | 2 / 9 | 9 / 9 |
| a01 | reference | 2 / 3 | 3 / 3 | 3 / 3 | 2 / 3 | 3 / 3 | 2 / 3 | 3 / 3 |
| b01 | reference | 0 / 3 | 2 / 3 | 0 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 |
| c01 | reference | 0 / 3 | 2 / 3 | 3 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 |
| family-A | reference | 2 / 3 | 3 / 3 | 3 / 3 | 2 / 3 | 3 / 3 | 2 / 3 | 3 / 3 |
| family-B | reference | 0 / 3 | 2 / 3 | 0 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 |
| family-C | reference | 0 / 3 | 2 / 3 | 3 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 |

Balanced repetitions give equal weight to each task in the scheduled completion proportions. Component denominators count assessed verdicts. Missing or infrastructure-failed slots remain in scheduled denominators and are not fabricated model answers.

Latency, actual order, per-model cost deltas, unknown counts and nonexclusive failed components are retained in scores.json. Provider metadata can lag, so slot cost deltas are not exact model allocations. Native zero token fields do not establish zero usage.

Selected example: [pilot-a01-inexpensive-1](workpapers/challenge-v1-development-7e8903385beb/pilot-a01-inexpensive-1.md). Selection: `financial_or_robustness_failure`.

Passing contrast: [pilot-a01-reference-1](workpapers/challenge-v1-development-7e8903385beb/pilot-a01-reference-1.md).

## final - challenge-v1-evaluation-d9a2fe13f6f2

| Scope | Model | Financial / assessed | Evidence / assessed | Robustness / assessed | Verified / scheduled | Delivery / assessed | Strict / scheduled | Verdict coverage |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | inexpensive | 17 / 27 | 4 / 27 | 19 / 27 | 2 / 27 | 27 / 27 | 2 / 27 | 27 / 27 |
| a02 | inexpensive | 3 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 |
| a03 | inexpensive | 2 / 3 | 2 / 3 | 1 / 3 | 1 / 3 | 3 / 3 | 1 / 3 | 3 / 3 |
| a04 | inexpensive | 3 / 3 | 0 / 3 | 0 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 |
| b02 | inexpensive | 3 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 |
| b03 | inexpensive | 3 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 |
| b04 | inexpensive | 3 / 3 | 1 / 3 | 3 / 3 | 1 / 3 | 3 / 3 | 1 / 3 | 3 / 3 |
| c02 | inexpensive | 0 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 |
| c03 | inexpensive | 0 / 3 | 1 / 3 | 0 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 |
| c04 | inexpensive | 0 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 |
| family-A | inexpensive | 8 / 9 | 2 / 9 | 4 / 9 | 1 / 9 | 9 / 9 | 1 / 9 | 9 / 9 |
| family-B | inexpensive | 9 / 9 | 1 / 9 | 9 / 9 | 1 / 9 | 9 / 9 | 1 / 9 | 9 / 9 |
| family-C | inexpensive | 0 / 9 | 1 / 9 | 6 / 9 | 0 / 9 | 9 / 9 | 0 / 9 | 9 / 9 |
| all | reference | 25 / 27 | 19 / 27 | 25 / 27 | 17 / 27 | 27 / 27 | 17 / 27 | 27 / 27 |
| a02 | reference | 3 / 3 | 2 / 3 | 3 / 3 | 2 / 3 | 3 / 3 | 2 / 3 | 3 / 3 |
| a03 | reference | 3 / 3 | 3 / 3 | 3 / 3 | 3 / 3 | 3 / 3 | 3 / 3 | 3 / 3 |
| a04 | reference | 3 / 3 | 3 / 3 | 3 / 3 | 3 / 3 | 3 / 3 | 3 / 3 | 3 / 3 |
| b02 | reference | 3 / 3 | 3 / 3 | 3 / 3 | 3 / 3 | 3 / 3 | 3 / 3 | 3 / 3 |
| b03 | reference | 3 / 3 | 3 / 3 | 3 / 3 | 3 / 3 | 3 / 3 | 3 / 3 | 3 / 3 |
| b04 | reference | 3 / 3 | 2 / 3 | 3 / 3 | 2 / 3 | 3 / 3 | 2 / 3 | 3 / 3 |
| c02 | reference | 3 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 |
| c03 | reference | 1 / 3 | 3 / 3 | 1 / 3 | 1 / 3 | 3 / 3 | 1 / 3 | 3 / 3 |
| c04 | reference | 3 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 | 0 / 3 | 3 / 3 |
| family-A | reference | 9 / 9 | 8 / 9 | 9 / 9 | 8 / 9 | 9 / 9 | 8 / 9 | 9 / 9 |
| family-B | reference | 9 / 9 | 8 / 9 | 9 / 9 | 8 / 9 | 9 / 9 | 8 / 9 | 9 / 9 |
| family-C | reference | 7 / 9 | 3 / 9 | 7 / 9 | 1 / 9 | 9 / 9 | 1 / 9 | 9 / 9 |

Balanced repetitions give equal weight to each task in the scheduled completion proportions. Component denominators count assessed verdicts. Missing or infrastructure-failed slots remain in scheduled denominators and are not fabricated model answers.

Latency, actual order, per-model cost deltas, unknown counts and nonexclusive failed components are retained in scores.json. Provider metadata can lag, so slot cost deltas are not exact model allocations. Native zero token fields do not establish zero usage.

Selected example: [final-a03-inexpensive-1](workpapers/challenge-v1-evaluation-d9a2fe13f6f2/final-a03-inexpensive-1.md). Selection: `financial_or_robustness_failure`.

Passing contrast: [final-a03-reference-1](workpapers/challenge-v1-evaluation-d9a2fe13f6f2/final-a03-reference-1.md).

No assisted-condition trials are recorded. These small source groups and repeated attempts do not establish population reliability or a universal model ranking. Synthetic controls test a few declared mechanisms, not universal generalization.

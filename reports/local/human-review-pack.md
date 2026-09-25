# Blinded workflow source review

Status: prepared, human review pending. No reviewer has been contacted.
These three development dossiers use previously published source groups.
No model names, submissions, scores or reference SQL are included in this pack.

For each case, independently check the question against the source, identify
the defensible outcomes and any ambiguity, and assess whether the declared
columns and controls reward valid alternative methods. Record the review date
and relevant financial experience only if a review actually takes place.

## Case A - comparable quarterly model

[Candidate request](../../datasets/workflow-v1/tasks/a01/instruction.md),
[source dossier](../../datasets/workflow-v1/tasks/a01/environment/sources.md),
[output contract](../../datasets/workflow-v1/tasks/a01/environment/output_contract.json).

Primary source: [Microsoft FY2025 Q2 release](https://www.microsoft.com/en-us/Investor/earnings/FY-2025-Q2/press-release-webcast).

Check the three-month/six-month reconstruction, the fiscal-year convention and
the preserved comparable prior-year amounts. Is the earlier Azure guidance on
the same currency basis as the actual? Does the evidence permit attributing
Intelligent Cloud operating income specifically to Azure? Are the segment recast
footnotes sufficient to avoid implying an unchanged historical segment perimeter?

## Case B - stablecoin reserve-metric audit

[Candidate request](../../datasets/workflow-v1/tasks/b01/instruction.md),
[source dossier](../../datasets/workflow-v1/tasks/b01/environment/sources.md),
[output contract](../../datasets/workflow-v1/tasks/b01/environment/output_contract.json).

Primary sources: [May SBC report](https://brale.xyz/assets/reports/SBC-Stable-Coin-Reserve-Attestation-Report-05-2025.pdf)
and [June SBC report](https://brale.xyz/assets/reports/SBC-Stable-Coin-Reserve-Attestation-Report-06-2025.pdf).

Check which date identifies the reserve stock, which date is the signature, and
which starting SQL calculation is already valid. Are the coverage denominator
and asset valuation scope justified? Does a change in issued supply identify
payments volume? Do identical exports and equal-valued different observations
have the correct distinct treatment? Assess the difference in examiner scope
without treating missing first-publication times as known.

## Case C - growth and gross-profit attribution

[Candidate request](../../datasets/workflow-v1/tasks/c01/instruction.md),
[source dossier](../../datasets/workflow-v1/tasks/c01/environment/sources.md),
[output contract](../../datasets/workflow-v1/tasks/c01/environment/output_contract.json).

Primary source: [Block FY2024 filing](https://www.sec.gov/Archives/edgar/data/1512673/000162828025007376/sq-20241231.htm).

Check consolidated contribution versus annual revenue-share change, the percent
scale, and the treatment of acquired-technology amortization in the gross-profit
bridge. Are Cash App percentages clearly separated from consolidated amounts?
Do the related revenue/cost disclosures identify a separate Bitcoin price effect,
or only a combined observed change? Assess whether a nonzero component residual
should be quantified rather than forced to zero.

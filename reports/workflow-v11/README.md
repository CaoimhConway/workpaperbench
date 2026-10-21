# Workflow-v11 prepared release

Prepared unpublished release: `v0.6.3-rc.1`.
Catalog: `workflow-v11-canonical-99f9af5fc8cb`.
Scorer: `workflow-1.2.1`, unchanged from workflow-v10.
No model inference, external-service spend, push or publication occurred.

This revision adds four independent-operand controls. c01 changes subscription
costs and the matching reported total with revenue fixed. b06 changes trips with
consumers fixed. The bounded audit also reproduced frozen spot-volume ratios in
b03 and frozen operating margins in c04, each addressed by a focused control.
The builder pins SQLite 3.45.1 for deterministic database header bytes.
Original observations, original-input answers, reference SQL, source-group splits,
published packages and historical results remain unchanged.

## Software qualification

All listed expectations passed against this exact catalog and scorer. Negative
cases deliberately receive financial or delivery rejection as specified, rather
than being counted as successful workpapers. These are authored software checks,
not model-performance results or independent human review.

| Check | Outcome | Record |
| --- | --- | --- |
| Software suite on Mac Pro | 582 passed, 13 platform skips | [Software validation](software-validation.json) |
| New submission-to-verdict tests on Linux | 16 passed, including all 12 tests skipped on macOS | [Linux regression log](dependency-pytest.txt) |
| Deterministic reconstruction | Exact reconstruction using Ubuntu 24.04 system Python 3.12 / SQLite 3.45.1 | [Validation summary](validation.json) |
| Whole-catalog native oracles | 150/150, five per task, zero errors, retries or cancellations, all original and control outputs pass | [Native records](direct-harbor-validation.json) |
| Fresh-environment quickstart | One c01 oracle passes through native Harbor and separate verification | [Quickstart record](direct-harbor-validation.json) |
| Dependency counterexamples | 28 expected outcomes, including prior-catalog false acceptance and current numerical rejection | [Dependency validation](dependency-validation.json) |
| Whole-catalog authored quality cases | 147 expected outcomes | [Quality validation](quality-validation.json) |
| Calculation, evidence and transport regression | Nine workpapers and three worker probes pass their expectations | [Contract validation](contract-validation.json) |
| Native scripted delivery | Correct delivery accepted and malformed delivery rejected, comparison settings forwarded | [Transport validation](comparison-recipe-validation.json) |
| Saved artifact grade and report | Reference passes, frozen-cost-ratio fixture fails only intended robustness requirement | [Saved-workpaper validation](saved-workpaper-validation.json) |

The [environment record](environment.json) retains actual controller, Docker,
Python and dependency versions. The catalog sweep and transport checks used the
existing pinned Harbor runtime. The quickstart and saved-workpaper commands also
passed in a newly installed project virtual environment. Each native trial uses
fresh candidate and separate verifier state. Raw originals remain local with
identity-bound hashes in the retained records. The verifier checks no network,
no inference credential and no Docker socket. Its resource and SQL bounds retain
the existing documented limits.

The [validation summary](validation.json) binds the manifest, scorer, worker and
retained record hashes. The [dependency audit](dependency-audit.md) records the
eight inspected calculations, four reproduced gaps and coverage limits. It does
not establish coverage of every row, operand or possible future financial change.

## Review and pilot materials

- [Source and independent arithmetic checks](source-review.json)
- [Current blinded source-review pack](human-review-pack.md)
- [Valid integration example](../../examples/block-workpaper-v11/answer.json)
- [Frozen-ratio negative example](../../examples/block-frozen-ratio-v11/answer.json)
- [Preliminary difficulty pilot and unexecuted commands](../../docs/PILOT.md)
- [Hosted configuration template](../../config/preliminary-hosted-model.example.json)
- [Local reference template](../../config/preliminary-local-reference.example.json)
- [Pilot schedule and outcome ledger](../../config/preliminary-pilot-manifest.example.json)

No unresolved scoped software defect or blocked software check is known. Human
financial-domain review remains pending. Provider/model selection, effective
settings, funding and configuration freeze are still required before any pilot
launch. Compatibility, usage, latency, pricing and model performance are
unobserved. The full comparison remains three attempts per evaluation task,
separate from the pilot's one attempt per evaluation task.

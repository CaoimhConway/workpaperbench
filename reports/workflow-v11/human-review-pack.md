# Current-release blinded source review

Status: prepared, human review pending. No completed human review or approval is
claimed. Catalog `workflow-v11-canonical-99f9af5fc8cb`, scorer `workflow-1.2.1`,
prepared unpublished release `v0.6.3-rc.1`.
The historical [review pack](../local/human-review-pack.md) is preserved separately.

First read only the request, permitted inputs and primary sources linked in the
dossier. Record your own calculations, interpretations and sufficient evidence
before inspecting solutions, gold, validation reports or submissions. Initial
judgments and subsequent adjudication must remain separate. The package hashes
in the [catalog manifest](../../datasets/workflow-v11/manifest.json) identify the
precise release under review.

| Task | Request and source inputs | Review focus |
| --- | --- | --- |
| workflow-v11-c01 | [Request](../../datasets/workflow-v11/tasks/c01/instruction.md), [dossier](../../datasets/workflow-v11/tasks/c01/environment/sources.md), [contract](../../datasets/workflow-v11/tasks/c01/environment/output_contract.json), [evidence locators](../../datasets/workflow-v11/tasks/c01/environment/evidence.json) | Annual cost matching, gross-profit attribution, amortization and consolidated residuals |
| workflow-v11-b06 | [Request](../../datasets/workflow-v11/tasks/b06/instruction.md), [dossier](../../datasets/workflow-v11/tasks/b06/environment/sources.md), [contract](../../datasets/workflow-v11/tasks/b06/environment/output_contract.json), [evidence locators](../../datasets/workflow-v11/tasks/b06/environment/evidence.json) | Quarterly flow versus monthly average consumers, months, segment denominator and corporate reconciliation |
| workflow-v11-b03 | [Request](../../datasets/workflow-v11/tasks/b03/instruction.md), [dossier](../../datasets/workflow-v11/tasks/b03/environment/sources.md), [contract](../../datasets/workflow-v11/tasks/b03/environment/output_contract.json), [evidence locators](../../datasets/workflow-v11/tasks/b03/environment/evidence.json) | Revenue versus spot-volume scope, USD million versus billion, booked stablecoin revenue and average balances |
| workflow-v11-c04 | [Request](../../datasets/workflow-v11/tasks/c04/instruction.md), [dossier](../../datasets/workflow-v11/tasks/c04/environment/sources.md), [contract](../../datasets/workflow-v11/tasks/c04/environment/output_contract.json), [evidence locators](../../datasets/workflow-v11/tasks/c04/environment/evidence.json) | Reported adjusted expense versus reconstructed adjustments, rounded residuals and branded-volume scope |
| workflow-v11-b02 | [Request](../../datasets/workflow-v11/tasks/b02/instruction.md), [dossier](../../datasets/workflow-v11/tasks/b02/environment/sources.md), [contract](../../datasets/workflow-v11/tasks/b02/environment/output_contract.json), [evidence locators](../../datasets/workflow-v11/tasks/b02/environment/evidence.json) | Reported versus reconstructed stocks, conflicting year labels, signatures versus economic dates, missing payment flows |
| workflow-v11-c07 | [Request](../../datasets/workflow-v11/tasks/c07/instruction.md), [dossier](../../datasets/workflow-v11/tasks/c07/environment/sources.md), [contract](../../datasets/workflow-v11/tasks/c07/environment/output_contract.json), [evidence locators](../../datasets/workflow-v11/tasks/c07/environment/evidence.json) | Release versus superseding annual report, settlement recognition, tax effects and unchanged operating cash |
| workflow-v11-c09 | [Request](../../datasets/workflow-v11/tasks/c09/instruction.md), [dossier](../../datasets/workflow-v11/tasks/c09/environment/sources.md), [contract](../../datasets/workflow-v11/tasks/c09/environment/output_contract.json), [evidence locators](../../datasets/workflow-v11/tasks/c09/environment/evidence.json) | Managed versus reported basis, pretax/after-tax exclusions, rounded inputs and unavailable pricing evidence |

For each case, identify ambiguous or inconsistent definitions, incorrect source
transcription or interpretation, valid calculations/evidence combinations the
grader rejects, and plausible financially coherent input changes the controls
fail to test. Distinguish a coherent counterfactual from a deliberate discrepancy
between separately reported observations. Missing disclosures are not zero.

After recording the initial derivation, compare references and submit alternative
artifacts through the [existing grader](../../docs/RUNNING.md#evaluate-your-own-agent).
Record any disagreement without altering the original review or historical files.

Every feedback item must include:

- Task ID, catalog ID and scorer version, plus review date and relevant experience.
- Submitted `answer.json` and SQL files, hashes and attempt ID where applicable.
- The observed verifier result and specific output/control/error, if grading was run.
- The expected result, independent derivation, source URL, page/section and date basis.
- Ambiguity, alternative sufficient evidence, counterexample or required correction.
- Initial judgment versus any later reference-informed adjudication, and unresolved questions.

Automated source/arithmetic checks are retained separately in `source-review.json`.
They do not establish independent human review or agreement. This selected pack
covers four changed cases and three higher-risk interpretations, not all 30 tasks.
A person's completed review remains pending until actually received.

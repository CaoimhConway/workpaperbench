# Workflow v15 software validation

Catalog: `workflow-v15-canonical-400f60b5b3b6`.
Scorer: `workflow-1.2.1`.
Native harness: Harbor `0.23.0` on Ubuntu 24.04 x86_64 with separate Docker verification.

The README quickstart passes on task `c01`. The maintained regression checks
five authored oracles (`a01`, `b01`, `b02`, `b06`, `c01`) and two scripted
Terminus-2 deliveries. The correct delivery passes and the malformed delivery
is rejected. Each invocation binds its task and manifest through the checked
runtime. Separate verification confirms network isolation, absence of an
inference credential and absence of the Docker socket.

These are software checks using authored references and scripted responses.
They do not measure model performance. The quickstart and maintained regression
cover selected tasks. The full 30-task, five-attempt oracle command is documented
in the [execution guide](../../docs/RUNNING.md#direct-harbor-execution).

| Check | Coverage and outcome | Record |
| --- | --- | --- |
| Linux test suite | 741 passed, no skips | [Test log](unit-tests.txt) |
| README quickstart | One c01 oracle passes with five input-integrity proofs | [Software validation](software-validation.json) |
| Maintained regression | Five oracles pass, correct scripted delivery accepted, malformed delivery rejected | [Native regression](native-regression.json) |
| Saved workpapers | Authored reference passes, frozen-cost-ratio example fails its independent-operand control | [Software validation](software-validation.json) |
| c01 quality controls | Five expected positive and negative outcomes | [Quality validation](quality-validation.json) |

Independent financial-domain review and external replication remain pending.
Tasks measure analysis within a fixed dossier, with normalized observations and
bounded claims. They do not establish open-ended financial research ability or
fine-grained model rankings.

The [publication bindings](../../config/workflow-publication.json) distinguish
original execution metadata from the published metadata. Every task file and
scorer byte is identical across that projection. Earlier catalogs and their
validation reports retain their own identities. See the
[preserved v11 qualification](../workflow-v11/README.md) for its separate scope.

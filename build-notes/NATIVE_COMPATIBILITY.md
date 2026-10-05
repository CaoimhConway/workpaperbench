# Native compatibility findings

Harbor 0.23.0 and Hermes `8b66a51036c1e20920a17cdd049fdf55c968d683` require three small corrections in the existing installed adapter. The project applies them on Actions only, after verifying the original module hash, and verifies the corrected hash before importing Harbor. No replacement adapter is introduced.

1. Native setup calls `hermes version`. The current CLI accepts `hermes --version`. Installation completed but this final command failed in run [37268358386](https://github.com/CaoimhConway/workpaperbench/actions/runs/37268358386). After correction and a consistent native `HERMES_HOME`, installation passed in [37269174132](https://github.com/CaoimhConway/workpaperbench/actions/runs/37269174132).
2. Native OpenRouter routing supplies `openrouter/qwen/qwen3.6-35b-a3b` as the CLI model without an explicit provider. The pinned resolver retains that prefix under this configuration. Set the existing provider flag to `openrouter` so the existing command builder passes the canonical model ID and explicit provider. Run 37269765974 exited without an answer or charged inference. That observation establishes runtime failure, while the specific routing diagnosis comes from source inspection.
3. Finite-query Hermes sessions use source `oneshot`. The native export filter uses `cli`. Update the existing filter to `oneshot` so native session export can supply its trajectory and token metrics.

Primary code: [Harbor adapter](https://github.com/laude-institute/harbor/blob/1e5c5c6db929a10a140d05e606882c671ae20729/src/harbor/agents/installed/hermes.py), [Hermes routing](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/oneshot.py), [session labels](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/run_agent.py).

The moving bootstrap also expects the PM package absent from the September stable tag. A timestamped canary tag was selected and its actual checkout is checked before solving. Native installation and execution must share `/tmp/hermes` as their data root. Managed Node needs Debian `libatomic1`. These installation constraints are recorded separately from financial task outcomes. The bootstrap URL and dependency retrieval remain moving parts.

This note is ready for upstream triage. No upstream report or contact is a release dependency. Model/tool behavior and final controls are recorded in BUILD_STATUS.md and the saved slot records.

Corrected routing and native terminal/file events were observed in run
37271209030. Treatment delivery and full task completion were observed in
37274770675, with the exact runtime revision checked before solving. Native
session-export token fields remained zero placeholders, so usage is treated as
unreported and provider lifetime accounting supplies the cost authority.

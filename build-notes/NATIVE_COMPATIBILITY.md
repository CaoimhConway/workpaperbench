# Native runtime compatibility

Harbor 0.23.0 and Hermes revision
`8b66a51036c1e20920a17cdd049fdf55c968d683` require three corrections in the
installed Harbor adapter. The patch verifies the original module hash and the
corrected hash before import.

1. Use `hermes --version` for the CLI version check.
2. Pass the explicit `openrouter` provider and canonical model ID for that route.
3. Select `oneshot` sessions when exporting finite-query trajectories.

The [pinned Harbor adapter](https://github.com/laude-institute/harbor/blob/1e5c5c6db929a10a140d05e606882c671ae20729/src/harbor/agents/installed/hermes.py),
[Hermes routing source](https://api.github.com/repositories/1024554267/contents/hermes_cli/oneshot.py?ref=8b66a51036c1e20920a17cdd049fdf55c968d683)
and [session implementation](https://api.github.com/repositories/1024554267/contents/run_agent.py?ref=8b66a51036c1e20920a17cdd049fdf55c968d683)
define these interfaces. The Apache-2.0 notice for retained patch fragments is in
[`third-party/NOTICE.md`](../third-party/NOTICE.md).

The bootstrap is pinned by revision and SHA-256. Installation and execution share
`/tmp/hermes` as their data root. Managed Node requires Debian `libatomic1`.
Bootstrap dependencies are not fully locked, so setup failures remain
infrastructure outcomes. Historical native export token fields were placeholders,
and provider lifetime accounting remains the historical cost authority.

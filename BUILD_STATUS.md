# Build status

Correction release 0.2.0 is in progress on existing PR [1](https://github.com/CaoimhConway/workpaperbench/pull/1). Specification v3.1 and the original experiment remain unchanged. The dedicated repository is public. No Docker, Harbor, inference or downloaded-submission SQL ran on this device.

## Verified state

- Original campaign [37280454673](https://github.com/CaoimhConway/workpaperbench/actions/runs/37280454673) completed all 48 scheduled slots at `b4e256dc8976223a8a3fdad157a6b212f49bb8e1`. All 48 original verdicts and 47 normalized answers are retained. `final-wp05-B-3` has no retained answer. Original raw serialization and tool observations were not retained and remain unavailable.
- Original strict completion: evaluation A 3/15, B 1/15. Final development A 4/9, B 3/9. Twelve exploratory attempts are separate, including setup/runtime failures and uncertain exposure.
- Freeze `wpb-v1-92baa4a72f0e` has 234 original hashes. Freeze file SHA256 `8cc3e40ed42898a7ead9fce7a7bfd5c9dc955f02cdd86a1c7bf352c9f667f95b`. Candidate data, instructions/schema, model, treatment, schedule, original answers and original verdicts remain unchanged.
- Existing correction run `37295210415` passed 156 lightweight tests and 23 native review controls. Its later workflow-edit push failed due to job-token permissions. Inspected recovery artifact `11339264449` matched ZIP SHA256 `4d3eb058c944abd2980575c00c26ca524f6d3183c44833f6a1688aa4a4304283`. Historical scorer 1.1.0 sidecars remain evidence, not final correction coverage.
- Commits `554e67e` and `c661f59` preserve authenticated campaign evidence, correct replay boundaries and expose coverage-aware reporting. Current checkout passes 190 lightweight tests. Hosted full native controls and consistent scorer 1.2.0 regrading are running in [37373492428](https://github.com/CaoimhConway/workpaperbench/actions/runs/37373492428). Its unit gate passed. Clean Python 3.12 checkout `8324b84` passed install, demo, all 186 tests at that checkpoint, report and full-history/freeze audit. Empirical merge/release waits for actual native results.

## Correction decisions

Scorer 1.2.0 accepts deterministic explicit-date, text and window alternatives while keeping read-only authorization, isolated imports, finite scalar output, 256 MiB Linux address-space, two-second CPU/subprocess and 1.5-second progress limits. Structurally rejected answers never execute SQL. Unambiguous numerical diagnostics can remain assessed while other checks are null. Conclusion verdict, reason and evidence have separate diagnostics.

Original versus normalized answer hashes are distinct. New retention screens bounded original bytes and tool calls/observations without retaining hidden reasoning. Authenticated imports verify archive/member bounds, schedule and artifact-declared slot identity, Actions run/attempt/commit and retained hashes, including the original record before replay. Legacy paths stay stable while new receipts/imports use experiment/slot directories. History is rechecked immediately before inference. Same-run reruns are rejected by new workflow definitions. Old Actions runs keep their original definition and must not be rerun.

The correction registry permits reviewed publication changes, never paid execution under the old freeze. The launcher checks every original frozen hash without consulting the registry. Regression controls demonstrate that model/runtime/source/candidate changes cannot be blessed by the publication registry and that this corrected checkout cannot launch the original paid freeze. All eight trusted grader copies match, without rebuilding candidate databases/assets.

Fresh read-only review found and checked structural SQL gating, encoded-secret screening, archive provenance and attempt namespacing. Independent Decimal calculations matched every original and changed fixture. Tesla and Apple filing headers/figures were rechecked. The saved wp03 A1 formula is accidentally correct at 100 to 120, but independently yields 50 instead of 25 at 120 to 150. Its official submission also fails aliases/evidence, and was never repaired for scoring.

Runtime/operations comprised 2,115 physical Python lines before final provenance fixes, excluding native control generation/tests/assets/config. Necessary bounded evidence code was reviewed. No parser, scheduler service, provider adapter, extra model or extra scored task was added.

## Versions, sources and boundaries

Harbor 0.23.0, commit `1e5c5c6db929a10a140d05e606882c671ae20729`. Hermes `v0.21.4+canary.20261004T084456Z`, commit `8b66a51036c1e20920a17cdd049fdf55c968d683`. Native compatibility changes have guarded module hashes in `config/runtime.json` and [upstream-ready notes](build-notes/NATIVE_COMPATIBILITY.md). Model `qwen/qwen3.6-35b-a3b` uses OpenRouter default routing. The only intervention is the original 230-word contract-check skill. Provider routing and moving bootstrap dependencies retain disclosed variability.

Two tasks use filing facts. Six are synthetic. wp04/wp08 share one fallback corpus after bounded RPC acquisition [37273047665](https://github.com/CaoimhConway/workpaperbench/actions/runs/37273047665) failed. Public methodology references motivate tasks and establish no product defect or observed adoption. [Source review](reports/source-review.md), [data sources](DATA_SOURCES.md) and [methodology](docs/METHODOLOGY.md) preserve details.

The candidate can read its dedicated capped inference key. Native TCP allowlisting retains DNS/ICMP channels. The separate verifier has network-none, no inference key and no Docker socket. Gold, checkout/Git history, GitHub credentials and host sockets do not enter the candidate. No paid secrets reach push/PR CI. Raw traces remain ephemeral and secret screening is not an absolute guarantee.

## Resource and publication accounting

Final provider receipt `reports/provider/37280454673.json`, as of 2026-10-05 11:15:27 UTC: lifetime USD 0.769789131, cap USD 20, reset null, remaining USD 19.230210869, BYOK zero. Lifetime includes exploration and failed calls. No inference was added for corrections. The lower existing cap stays below the USD 50 authorization and is never reset or raised. Lagging slot deltas are not exact per-arm costs and native zero token fields do not establish zero usage.

Refreshed actual Actions metadata confirms 182 rounded Linux job minutes for jobs started before publication at 07:55:02 UTC, conservatively USD 1.092 before included quota at USD 0.006/minute. Standard public hosted Linux compute after publication is free. Account quota, invoice and storage charges remain unknown after the existing billing API returned 404. The USD 10 incremental Actions ceiling remains in force. No account safeguards, scopes or subscriptions changed.

Historical software publication audit and prerelease [v0.1.0-software](https://github.com/CaoimhConway/workpaperbench/releases/tag/v0.1.0-software) are preserved. The corrected measured release requires final source/history/log/artifact/COPY-context audit, clean-checkout usage checks and passing native controls/regrades before merge.

## Supplied package availability

The named workpaperbench-corrections package was absent from supplied project/attachment locations. Existing PR/source artifacts were inspected and completed directly. This does not establish validation or applicator preflight of an unavailable package. It blocks no independent release work.

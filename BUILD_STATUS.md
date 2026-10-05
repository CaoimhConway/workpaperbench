# Build status

Specification v3.1. Dedicated repository: https://github.com/CaoimhConway/workpaperbench.
Confirmed owner `CaoimhConway` (ID 55163829), default branch `main`, now public after the completed software audit.
No genuine external blocker. No Docker, Harbor or inference ran on this device.

- Stage 1 complete: three development tasks, native controls, all 12 exploratory
  slots preserved, one selected skill and actual hosted delivery verified.
- Stage 2: all eight sources/packages, direct reference review, balanced controls,
  candidate-instructions/schema-only review and freeze complete. Corrected full
  native gate `37276298546` on `77f1fd8` passed all 64 controls: 25 expected
  passes, 39 expected failures, every recorded isolation check passed.
- Stage 3: fresh read-only source-first audit complete and fixes verified locally.
  Software prerelease published. Frozen final 48-slot campaign is running as
  `37280454673` on `b4e256d`. Empirical release remains pending actual completion.
- Clean checkout `3031a86` installed and passed all 128 tests, demo, validate,
  report and full-history scanner. Frozen push CI `37277179243` also passed.
- Current freeze `wpb-v1-92baa4a72f0e`, 234 file hashes. Content digest
  `92baa4a72f0e` is the manifest ID suffix, full digest is in `config/freeze.json`.
  Freeze file SHA256 `8cc3e40ed42898a7ead9fce7a7bfd5c9dc955f02cdd86a1c7bf352c9f667f95b`.
  Sources, tasks, grader, scripts, tests, runtime/skill, schedule and workflows
  are frozen before any evaluation model exposure. Status/results/README remain
  editable. Model, treatment and task inputs cannot change silently after exposure.

## Configuration and boundaries

Harbor 0.23.0 at `1e5c5c6db929a10a140d05e606882c671ae20729`.
Hermes `v0.21.4+canary.20261004T084456Z` resolves to
`8b66a51036c1e20920a17cdd049fdf55c968d683`, checked before every solve.
The native installer uses a moving upstream bootstrap. Three genuine native
compatibility corrections have exact original/corrected module SHA256 guards in
`config/runtime.json` and an upstream-ready note. No custom adapter or proxy.

Hosted model `qwen/qwen3.6-35b-a3b` uses OpenRouter default routing, with residual
provider variation. Actual terminal/file events and completed workpapers confirm
compatibility. Toolsets file/terminal/skills, turn cap 90, memory/profile/checkpoints
false, compression 0.85, terminal 180 seconds. Setup 1200, solve 600, verifier 180
seconds, candidate 2 CPUs/4096MiB. Base Python3.12 manifest/amd64 digests are pinned.
One slot per Ubuntu 24.04 full-VM job, max-parallel 1, no outer score-based retries.
Native transport retries remain in-slot and their individual counts are unknown.

The candidate can read its dedicated capped inference key. Native TCP allowlisting
has DNS/ICMP residual channels. The separate verifier uses network-none and checks
loopback-only interfaces, blocked external TLS, absent key and Docker socket.
Candidate inputs exclude gold, project checkout/Git history, GitHub credentials and host
sockets. SQL alone runs in a constrained, bounded, key-free trusted subprocess.
Raw live traces are ephemeral. Only scanned/allowlisted small evidence is retained.
Runtime growth reviewed at 1534 hand-written lines, three runtime modules and thin
scripts, excluding tests/assets/config. No minification or framework was added.

## Sources and development findings

[DATA_SOURCES.md](DATA_SOURCES.md) and [source review](reports/source-review.md)
record factual extracts, original synthetic fixtures, independent direct
calculations and valid/invalid alternatives. wp04/wp08 share one synthetic corpus.
Capture `37273047665` used the fixed window through PublicNode and documented
Cloudflare, one request each. HTTPError/RPC error prevented acquisition. The
explicit fallback preserves failure evidence and makes no observed-chain claim.
Artemis methodology motivates a question, without proving a product defect.

Pilot 12 statuses: preserved under `reports/runs`, including installation/runtime
failures and unknown costs. wp01 A3/A4 and wp05 B1 completed. wp02 A3/A4 had correct
transfer arithmetic but violated requested fields/evidence/SQL output contracts.
wp05 A2 guessed an omitted task identifier and omitted SQL aliases. That unfair
prompt and a valid naive-growth citation alternative were fixed. wp05 A3 had
correct 65% naive/10% comparable values but hardcoded naive SQL and prose citations.
No substantive financial miscalculation is inferred from those contract failures.

Selected one 230-word contract-check skill, without task IDs/formulas/answers or
new evidence. B delivery run `37274770675` proved exact appended text and staged
skill hash `651820768f6a80222f92256abd9ac58474a480fcfbdf212bda8b22fff1863bb0`,
plus runtime pin and complete verification. Pilot corrections preceded this check,
so it establishes delivery, not causal uplift. All 12 slots are exhausted.

Fresh audit corrected synthetic-origin labeling, attached Circle metadata
locators, accepted genuine scope-only citations, and caught wrong matched joins
whose equal tag weights canceled. The wp06 changed metadata observation exposes
22% from the bad query against 25% correct growth, with local/native controls.
The candidate-only review found no direct answers but noted scope-cued limits in
wp04/wp08. No external human validation or contamination-proof claim.

## Actual execution evidence

| Runs | Actual result |
|---|---|
| 37261618709 | Docker plumbing preflight passed, not native proof |
| 37263846465 | Full3-development native controls passed 27 cases |
| 37265511360 | Bare TCP probe failed to prove egress blocking, corrected to TLS |
| 37266025062 / 37266518124 | Corrected native smoke passed 6 each, then verifier namespace-none proof |
| 37266930239 | Three A1 setup failures, retained |
| 37267321820 / 37267758153 / 37268139696 / 37268358386 / 37268809048 | Key-free installation diagnostics failed, motivating actual compatibility/library/data-root fixes |
| 37269174132 / 37270674684 | Key-free installation and CLI gates passed |
| 37269765974 | wp01 A2 runtime failure, wp02 A2 started/canceled with unknown cost, wp05 A2 genuinely unstarted and later resumed |
| 37271209030 | Actual tools and submissions, wp01 A3 complete, wp02 A3/wp05 A2 failed contract |
| 37272511333 / 37274770675 | Remaining baselines and single B check completed, canonical evidence retained |
| 37272514161 | Development smoke passed 6 |
| 37275297547 | Canceled as superseded after audit finding,8 partial controls retained, gate not passed |
| 37276298546 | Corrected all-eight full native gate passed64 controls |

Tested commands: editable lightweight install, `python -m pytest -q`,
`workpaperbench demo`, structural `validate`, report generation, native CI dispatch,
pilot dispatch/watch/download, and exact final 48 resume selection against actual
Actions history. The final selector found 48 truly unstarted,0 previously started.
Remote commands use `--repo CaoimhConway/workpaperbench --ref main`.

## Resource and publication accounting

The dedicated key was supplied explicitly and transferred to the repository secret
through stdin. Provider reconciliation `37274770675` as of 2026-10-05 06:59:02 UTC:
lifetime usage $0.0867218, cap $20, reset null, remaining/funded $19.9132782, BYOK 0.
This actual cap is below the authorized $50 ceiling and is never reset or raised.
Per-slot snapshots lag, so their sum is not total spend. Native zero token fields
are unreported usage. Full 48 reserve $9.60 fits current funds.

Actions snapshot as of 07:52 UTC: 182 rounded Linux job minutes, conservative compute
$1.092 before included quota at $0.006/minute. It includes the then-running job and
will be refreshed after gates. Invoice, included account quota and storage charges
are unknown because the existing billing API returned 404 without user scope.
No scope, subscription, cap or account safeguards changed. Authorization ceiling
is $10 incremental project Actions charges.

Tracked files, Git blobs, candidate COPY contexts and freeze hashes passed the
publication scanner. Dependency license/notice retained. Actual logs/artifacts,
staged history/source audit and completed software gate are required before
visibility change. Software prerelease v0.1.0-software published after the gate. Existing SSH setup reused. With explicit
owner permission, the work include became case-insensitive and was ordered after
the fallback. Effective existing work identity verified. Bootstrap `da28f4a` used
the old fallback identity before the fix, history preserved without rewriting.

Software publication audit complete: 19 started live-job logs, full native and frozen-unit logs, saved sanitized JSON, full Git blobs, source/license notices and candidate COPY contexts reviewed. No credential/encoded-fragment hits. The full native control report is permanently retained. Software is complete. Final evaluation started only after this audit and the software prerelease.

Exact final dispatch: `gh workflow run benchmark.yml --repo CaoimhConway/workpaperbench --ref main -f mode=final -f batch=all -f manifest_id=wpb-v1-92baa4a72f0e`. Run37280454673. No scored reruns or changed frozen inputs. Standard public Linux compute applies after the software publication timestamp recorded in the audit, while storage/invoice charges remain unknown.


## Review correction validation

156 Python tests and the native review controls passed on Actions run 37295210415. Existing answers were regraded without inference. Original task inputs, model, treatment, freeze and verdicts remain unchanged. The README results block is derived from the retained evidence. See reports/results.md for completeness, reviewed coverage and current counts.


## Correction recovery - 2026-10-05

Reused PR 1 and its existing branch. Original campaign 37280454673 completed all 48 slots. Authenticated artifact 11339264449 from 37295210415 matched ZIP SHA256 4d3eb058c944abd2980575c00c26ca524f6d3183c44833f6a1688aa4a4304283. The previous run passed its tests/native checks but could not push workflow changes with its job token. Recovered code and historical regrades were inspected in an isolated directory, with a fresh read-only security review.

Scorer 1.2.0 stops SQL on structural rejection while retaining unambiguous numerical diagnostics. Full schedule/run/archive/hash checks protect collection and task lookup. Experiment-scoped receipts and a final history check prevent repeated inference. CI now validates committed source and emits artifacts with read-only permissions. Original candidate assets/freeze/model/treatment remain unchanged. 179 lightweight tests passed. Final key-free hosted validation is pending. No inference was added. Final provider receipt records lifetime USD 0.769789131 and remaining USD 19.230210869 under the unchanged USD 20 cap. One original slot has no retained answer and cannot be regraded.

The named workpaperbench-corrections package was not present in supplied local locations. Existing PR/source artifacts were inspected and completed directly. This does not establish validation of an unavailable package.


Release usage/reporting checkpoint: package version 0.2.0, scorer 1.2.0. The package audit permits only its version field to differ from the frozen dependency manifest. README commands, local evidence-backed demo and relative links have smoke coverage. Reports now expose numerical/strict denominators, split conclusion diagnostics, task origins, latency, lagging cost deltas, actual order and scorer/input identities. Direct Decimal calculations matched all eight original and changed fixtures. Tesla and Apple primary filing headers and amounts were rechecked. Runtime/operations comprise 2,115 physical Python lines excluding native integration tests and build generation, reviewed as necessary bounded evaluation/evidence code. No scheduler service, parser, provider adapter or model was added. Hosted full controls/regrade 37373492428 are in progress on 554e67e.

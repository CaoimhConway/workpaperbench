# Third-party notices

WorkpaperBench original code and fixtures use the root MIT license.

`scripts/fix_native_version.py` includes small match/replacement fragments of the
Harbor 0.23.0 native Hermes adapter. The upstream file is Apache-2.0 licensed.
The script applies the three changes described in
[Native compatibility findings](../build-notes/NATIVE_COMPATIBILITY.md) to the
installed package and does not redistribute a complete adapter. Retain the
[Apache-2.0 license](Harbor-Apache-2.0.txt).
[Source at the pinned revision](https://github.com/laude-institute/harbor/blob/1e5c5c6db929a10a140d05e606882c671ae20729/src/harbor/agents/installed/hermes.py).

Hermes Agent is installed from its own repository on hosted runners. Its
[MIT license](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/LICENSE)
remains in the installed checkout. This repository does not bundle its source.
Issuer filings, Circle metadata and Artemis methodology remain their owners'
material. Only concise factual extracts and original annotations are included.

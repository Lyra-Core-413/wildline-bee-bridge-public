# MIT license scope and external dependencies

This public Wildline Bee Bridge release adopts the complete [MIT License](LICENSE) under Eric's authorization:

**Copyright (c) 2026 Eric Staiger**

The grant covers the authorized project-owned source, tests, fictional fixtures, launchers and documentation in this release, including the inherited project-owned H5 derivative and bounded transport Eric has authorized for release. It does not claim ownership of independently owned material or relicense external runtimes, executables or services. The separately published [Wildline Continuity Reader](https://github.com/Lyra-Core-413/wildline-continuity-reader) is a distinct MIT-licensed artifact; its license was not an automatic license grant for this Bridge.

No specific conflicting license, copied third-party implementation or bundled third-party notice obligation was identified in this release inventory. MIT adoption follows Eric's authorization and the available provenance records; it is not an independent certification of copyright ownership. Preserve any applicable third-party notices if a specific independently owned component is later identified and resolve its distribution rights before including it.

## Dependency and notice inventory

| Component | Distribution and rights |
| --- | --- |
| Project-owned Bridge/H5 source, probes, tests, fictional fixtures, launchers and documentation | Included. Authorized project-owned materials are covered by LICENSE. Existing source provenance remains in `bee_runtime.py` and `CHANGE-RECORD.md`. |
| CPython 3.14 and the standard library | Separately installed; no runtime or standard-library implementation is bundled. The external runtime retains its PSF and incorporated-component licenses. See [Python's license documentation](https://docs.python.org/3.14/license.html). |
| Windows APIs | Called dynamically through standard-library `ctypes`. No Windows binary or SDK implementation is bundled. |
| Third-party pip packages, vendored source, binary dependencies and nested source archives | None included in this package. |
| Native `@beeai/cli` 0.7.3 `bee.exe` | Optional, separately installed and authenticated. No Bee executable or SDK is included or relicensed. Its terms and account/service rules remain external; no redistribution rights or current availability claim is made. The exact accepted executable hash remains in the setup guide and runtime. |
| Real Bee records, private operation receipts, personal Lyra Core state and preserved private packages | Excluded. The source license does not grant access to accounts or rights to anyone's personal records. |

The offline demonstration and test suite require no Bee account, Bee executable, credentials, Core files or pip packages. Optional live use retains the existing one-operation, explicit-consent runtime and requires the operator's own authorized account and source record. These operational boundaries do not add conditions to the standard MIT source license.

MIT's copyright and permission notices must accompany copies or substantial portions of the licensed materials. The complete grant and warranty/liability clauses are in LICENSE.

This public derivative adds licensing and public setup documentation, substitutes a fictional refusal-policy fingerprint for the inherited private one, and refreshes the affected H5 engine pin and package seal. Tests, fictional fixtures, launchers and dependency bytes are preserved. The separate release record identifies and verifies the bounded source changes. The earlier sealed packages retain their historical versions and seals. Development-PC verification does not establish compatibility on a second physical computer.

# Bee Bridge v1.1-public.1 — judge demonstration

## Exact v1.1-public.1 setup and commands

Use normal Windows 10/11 x64, a fixed local drive with Windows ACL support, Python 3.14 (tested 3.14.7 x64) and the `py` launcher. No pip dependencies, Core files or Bee account are needed offline.

Use a clean source ZIP extraction of the 37-file **v1.1-public.1** package:

1. Open the [Bee Bridge public-release repository](https://github.com/Lyra-Core-413/wildline-bee-bridge-public) at the exact revision identified in the release verification record. Select **Code → Download ZIP → Extract All**. The separate release record supplies the reviewed commit/download link and records public-access verification; this source document does not certify current repository visibility.
2. Extract all files to a fixed local Windows drive with no linked or reparse-point parent directories. Use a normal local folder outside OneDrive or other synchronized folders. Open PowerShell in the extracted folder containing `RUN-JUDGE.cmd` and `RUN-TESTS.cmd`. Confirm `PACKAGE-MANIFEST.json` identifies `derivative_version: v1.1-public.1`.
3. Use a clean extracted source ZIP. A Git clone includes `.git` metadata, which triggers `PACKAGE_INTEGRITY_FAILED`. Any added, missing or changed file also fails integrity. Keep archives, verification reports, redirected logs and generated output outside the package. Preserve the package files exactly as extracted.
4. Confirm Python with `py -3.14 --version`. Then run the commands below: `RUN-JUDGE.cmd` is the **fictional demonstration**; `RUN-TESTS.cmd` runs the **107-test fictional/mock offline suite**. No Bee account, Bee executable, credentials or Lyra Core files are required offline.

```powershell
.\RUN-JUDGE.cmd
.\RUN-TESTS.cmd
```

The judge command always selects fictional single-observation mode and does not forward live flags. Direct equivalents:

```powershell
py -3.14 -X utf8 -I -B .\single_bridge.py --offline-demo
py -3.14 -X utf8 -I -B .\run_tests.py
```

The existing runner uses disposable copies and runs 6 Windows process/ACL, 24 bridge, 36 adapter and 41 H5 tests, 107 total. It never launches installed Bee.

### New live operation — separate authorization required

Installation/login are external prerequisites, not setup actions performed here. Only the exact native user-installed `@beeai/cli` 0.7.3 `bee.exe` is accepted, SHA-256:

`865e421f94af9a4aab1426af5b062d91236b7d08e9098de0758fba1d1b0dc5e6`

Shims, relative/UNC/mapped/non-fixed paths, links, hardlinks, changed pins and other executables fail closed. Do not weaken the pin. Current availability, other versions/accounts and second-PC behavior are unverified. No auth preflight runs.

For a new read from your own authorized Bee account, choose only a Fact you are entitled to access. In a normal interactive terminal:

```powershell
$factId = Read-Host 'Your authorized numeric Bee Fact ID'
$beeExe = Read-Host 'Absolute local path to the pinned native bee.exe'
py -3.14 -X utf8 -I -B .\single_bridge.py --live-read --fact-id $factId --bee-exe $beeExe
```

`Read-Host` supplies parameters only, not consent. The user must type the runtime's exact ID-specific phrase personally:

```text
READ CAPTURE AND RECOVER FACT <YOUR_AUTHORIZED_FACT_ID> FIELDS id,text,confirmed,created_at
```

This covers one read, selected-field private capture, display and one fresh-process recovery. No default live ID, `--yes`, unattended or redirected consent exists.

The actual path is:

```text
single_bridge.py --live-read
  -> pinned bee.exe facts get <chosen-ID> --json
  -> one private H5_CAPTURE_V1 stage A
  -> H5_SINGLE_OBSERVATION_V1 seal
  -> separate single_reader.py
  -> actual recovered view.answer, provenance, uncertainty, authority NONE
```

One native CLI launch, shell/stdin disabled, bounded response/diagnostics, no automatic retry. The full response transiently passes through bounded memory; only selected fields influence the capture, and raw output/diagnostics are not saved. CLI internal HTTP/logging behavior is not independently audited.

### Private output and STOP behavior

Default output is `%LOCALAPPDATA%\WildlineBeeContinuity\<random-operation>`, owner/SYSTEM-only, outside the repository and package. Existing mismatched permissions are refused. Optional `--private-root` needs a new absolute fixed-local location with an existing parent, outside/away from Git and the package. Avoid cloud-sync/shared folders. Windows app packaging may redirect logical paths; inspect the recorded resolved operation path.

Successful selected text, ID and answer remain private plaintext as consented. Do not distribute the operation folder or record/share the live terminal without separate permission.

Eight files establish the operation: `attempt.json`, `capture.json`, `receipt.json`, `SINGLE.json`, `STATE.json`, `READER-CLAIM.json`, `RECOVERED.json`, `COMPLETE.json`. Pending acquisition/state records are intentionally not rewritten; the separate valid COMPLETE record establishes completion. Do not run the reader again on a claimed/completed operation.

Refusal performs no read. Auth/CLI failure, interruption, reader mismatch or cleanup refusal means STOP without retry or fictional substitution. Caught failures attempt scoped cleanup and keep only a private attempt plus sanitized failure. Forced termination or filesystem/permission failure can leave protected remnants. Retention/deletion is not secure erasure; memory, backups, scrollback, administrators and same-user tampering are outside these guarantees.

### Integrity

This public derivative is v1.1-public.1: 37 files, with 35 payload files bound by PACKAGE-MANIFEST.json and the manifest bound by PACKAGE-ANCHOR.sha256. It has a new seal; the original private packages and earlier seals remain preserved separately. Any later documentation or other packaged-file change requires a new version, refreshed manifest/anchor and verification; never reuse an old seal. The retained `WILDLINE_PRIVATE_SINGLE_BRIDGE_V1` manifest format is an internal compatibility identifier, not a repository-visibility statement. Runtime refuses missing, extra or changed files, including Git metadata.

## VERIFIED — October 11 live evidence update

One founder-authorized native CLI invocation returned exit 0, followed by a distinct acquisition/reader process pair and a recovered answer exactly matching the H5 single-observation projection. All eight private evidence files and the 28 original package files were verified; authority was NONE.

The immutable formatter prints the actual recovered answer and flushes it before completion is recorded. Terminal completion was founder-reported; no independent character-by-character screen capture was retained. Independently checked means local evidence verification, not a second physical machine or external source attestation.

The result remains source-qualified `CLAIMED_UNVERIFIED`, with device origin unverified and source-reported confirmation. Creation time is not update time. `NOT_ASSESSED_SINGLE_OBSERVATION` establishes neither change nor no-change, correction, withdrawal, writeback or synchronization. The successful one-account operation is not a general service/compatibility guarantee.

No private operation receipt, identifying Fact content/ID or captured answer is included here.

**Live v1.1 single-Fact recovery ≠ historical change replay ≠ full sync.**

## VERIFIED / EXPERIMENTAL / FUTURE VISION

VERIFIED means a bounded behavior supported by an attributed retained report or local operation check. EXPERIMENTAL identifies separate Lab work. FUTURE VISION identifies capabilities not delivered here. None means production readiness or independent physical-machine verification.

Saved real H5 A/B no-change evidence and the historical correction/withdrawal/H4 narrative are excluded. Fictional A/B regression fixtures are not a second genuine observation.

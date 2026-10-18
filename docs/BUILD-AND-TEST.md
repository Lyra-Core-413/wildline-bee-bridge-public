# Build and test guidance

This is the **documentation-facing summary** for the public Bee Bridge derivative and distinct project artifacts. The exact package-local manifest, test runner and setup guide take precedence when executing software. Do not treat the private development snapshot as a complete installation.

## Distinct artifacts and their evidence

| Artifact | Distribution | Default input | Environment tested | Evidence |
| --- | --- | --- | --- | --- |
| Public MIT Continuity Reader | Published separately; MIT-licensed | Fictional fixtures | Retained RC3 clean-extraction verification on the development Windows PC | 48 passing tests |
| Public Bee Bridge v1.1-public.1 | Owner-authorized MIT source derivative; new public-repository route | Fictional default; separately authorized live mode | Its own verification is recorded separately | Existing 107 fictional/mock tests retained; consult the public-release record for its actual results |
| Earlier private Bee Bridge v1.1-docs.2 | Preserved private source and history | Fictional default; separately authorized live mode | Retained development-PC verification | 107 fictional/mock tests; historical results belong to that package |
| Preserved historical demonstration | Private and frozen | Authorized historical lifecycle data | Isolated Windows demonstration | Reports documented corrections, partial reconfirmation, withdrawal and fresh-process recovery |

The **separately authorized real Bee v1.1 operation** was verified after mock testing. One actual CLI read succeeded with exit 0 and no retry, and a distinct process recovered the selected information. Its private receipt is **not** a file in the public-source archive.

## Installation and execution boundaries

- Offline public Bridge and separate Continuity Reader: Windows x64 and separately installed CPython 3.14 (tested 3.14.7 x64).
- Optional live Bridge mode: the exact pinned native Bee CLI must be installed and authenticated separately. The operator supplies a Fact from their own authorized account and types the runtime's fresh consent phrase; the judge launcher remains fictional-only.
- Run `RUN-JUDGE.cmd` only from an approved extracted package where the file exists.
- Do not run original Lyra Store/server entry points from the screened development snapshot as smoke tests. Those have omitted configurations and may mutate local state.
- No bundle has been verified on a second physical Windows machine. Document that limitation.

## Verify before distribution

1. Check the release ZIP hash against its retained manifest and verification receipt.
2. Inspect the exact file inventory, including data, binaries and nested archives, and compare it with the intended release scope.
3. Verify synthetic-only examples contain no identifying Bee account IDs or personal text.
4. Check package-local test commands actually exist and don't read or write private data.
5. Run offline tests in a clean extraction. Record their actual outputs and environment.
6. Inspect setup docs for security assumptions, special Windows permissions and missing prerequisites.
7. Preserve the adopted MIT notice for authorized project-owned materials and the separate terms of external components; review rights before adding new components.
8. Record the exact owner-authorized public-release commit/ZIP, anonymous access and verification results. Publication of source does not authorize new live operations or submission changes.

## Provenance and authority checks

An honest result should show what was retrieved or projected, what source it refers to, what remains uncertain, whether information was superseded, and whether the system has any authority to act. The current judge reader keeps authority at **NONE** for the demonstrated observation. Avoid claiming stronger inference than the available sample supports.

## Public release status and evidence limits

- MIT adoption: **AUTHORIZED** for the project-owned materials described in [LICENSE-REVIEW.md](../LICENSE-REVIEW.md), with the complete grant in [LICENSE](../LICENSE). No specific conflicting bundled license was identified; this is not an independent certification of copyright title.
- Public source distribution: **OWNER-AUTHORIZED** for this distinct derivative in the new [Bee Bridge public-release repository](https://github.com/Lyra-Core-413/wildline-bee-bridge-public). The separate release record establishes actual publication, exact commit/ZIP and anonymous access. The earlier private repository and history are preserved separately.
- The public MIT Continuity Reader is a distinct, fictional-only published artifact. This Bridge's offline default is fictional; optional live mode requires its external prerequisites and operator consent.
- Different-machine compatibility: **NOT TESTED**.
- Broad source-device attestation: **UNVERIFIED**.
- Live synchronization and automated actions: **NOT CLAIMED**.

**Preserve the line. Keep it wild.**

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

## Public derivative and integrity

This public derivative is v1.1-public.1: 37 files, with 35 payload files bound by PACKAGE-MANIFEST.json and the manifest bound by PACKAGE-ANCHOR.sha256. It has a new seal; the original private packages and earlier seals remain preserved separately. Any later documentation or other packaged-file change requires a new version, refreshed manifest/anchor and verification; never reuse an old seal. The retained `WILDLINE_PRIVATE_SINGLE_BRIDGE_V1` manifest format is an internal compatibility identifier, not a repository-visibility statement.

The earlier private versions have retained offline development-PC test results. This public derivative changes licensing/setup documentation and replaces private refusal-policy metadata with a fictional policy fingerprint, with the corresponding H5 engine pin and package seal refreshed. Test, launcher, fixture and dependency bytes remain unchanged. Candidate tests and final public GitHub ZIP/access checks are recorded separately; prior live-operation evidence and earlier test results retain their historical attribution. No new live operation or second-computer test follows from this release work.

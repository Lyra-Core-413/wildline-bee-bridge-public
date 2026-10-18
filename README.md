# Wildline | Bee Bridge public release

**CONTINUITY WITHOUT CAPTIVITY**

*The past matters. But it doesn't get exclusive ownership of the future.*

Wildline began with a Daily Command Center: Amazon Bee captured real-world context, ChatGPT helped interpret it, and a bespoke Lyra Core evolved to preserve corrections and changing understanding across sessions. Wildline is the effort to extract **portable continuity mechanics** from that private working experience.

> Know me well enough to recognize me. Stay curious enough to let me change.

## What this Bee Bridge is designed to show

**A. Offline, fictional demonstration:** The v1.1-public.1 default validates one fictional source observation and recovers an actual source-qualified answer in a separate process. It makes uncertainty and `authority: NONE` visible. This path requires no Bee account. The retained fictional A/B pair is a separate regression interface.

**B. Consent-gated real Bee bridge:** Optional live mode lets an operator specify a Fact ID from their own authorized account and explicitly approve one read, selected-field private capture and fresh-process recovery. The successful founder-supervised October 11 test of the earlier private v1.1 package recorded **one genuine CLI call (exit 0, no retries)** and a distinct reader process. That historical result is not a new live test of this public derivative. Selected personal data and its receipt remain outside distributable archives.

**C. Historical lifecycle evidence:** A separately preserved judge package replays an authorized historical Bee Fact's change, partial reconfirmation, deletion and fresh-process recovery. The lifecycle was not observed during the single October 11 read; do not present it as such.


## Exact setup and demonstration

Use normal Windows 10/11 x64, a fixed local drive with ACL support, Python 3.14 (tested 3.14.7 x64) and the Windows `py` launcher. No pip packages, Core files or Bee account are required offline.

Use a clean source ZIP extraction of the 37-file **v1.1-public.1** package:

1. Open the [Bee Bridge public-release repository](https://github.com/Lyra-Core-413/wildline-bee-bridge-public) at the exact revision identified in the release verification record. Select **Code → Download ZIP → Extract All**. The separate release record supplies the reviewed commit/download link and records public-access verification; this source document does not certify current repository visibility.
2. Extract all files to a fixed local Windows drive with no linked or reparse-point parent directories. Use a normal local folder outside OneDrive or other synchronized folders. Open PowerShell in the extracted folder containing `RUN-JUDGE.cmd` and `RUN-TESTS.cmd`. Confirm `PACKAGE-MANIFEST.json` identifies `derivative_version: v1.1-public.1`.
3. Use a clean extracted source ZIP. A Git clone includes `.git` metadata, which triggers `PACKAGE_INTEGRITY_FAILED`. Any added, missing or changed file also fails integrity. Keep archives, verification reports, redirected logs and generated output outside the package. Preserve the package files exactly as extracted.
4. Confirm Python with `py -3.14 --version`. Then run the commands below: `RUN-JUDGE.cmd` is the **fictional demonstration**; `RUN-TESTS.cmd` runs the **107-test fictional/mock offline suite**. No Bee account, Bee executable, credentials or Lyra Core files are required offline.

```powershell
.\RUN-JUDGE.cmd
.\RUN-TESTS.cmd
```

The judge launcher always selects the fictional single-observation mode and does not forward live flags. The existing test runner uses disposable copies and mock/fictional inputs, never installed Bee.

For an operator's new, separately authorized genuine read from their own account, the supported entry is:

```powershell
$factId = Read-Host 'Your authorized numeric Bee Fact ID'
$beeExe = Read-Host 'Absolute local path to the pinned native bee.exe'
py -3.14 -X utf8 -I -B .\single_bridge.py --live-read --fact-id $factId --bee-exe $beeExe
```

This does not automate consent: type the runtime's exact ID-specific phrase yourself. The [live guide](docs/DEMO-AND-VERIFICATION.md) gives the phrase, actual CLI/reader path and STOP behavior. [Build and tests](docs/BUILD-AND-TEST.md) gives the exact external CLI pin and storage prerequisites. No personal Fact ID, credentials or source text is supplied.

## What the evidence says

| Claim | Existing evidence | Limitation |
| --- | --- | --- |
| Fresh-process answer recovery | Offline clean-extraction tests; separate reader PID | Does not establish language-model retraining |
| Real Bee→recovery in one bounded operation | Oct 11 founder-run v1.1 receipt independently checked | One selected Fact, no automatic synchronization |
| Historical corrections and withdrawal | Separate authorized history replay | Does not describe a live source modification |
| Privacy preservation | Staged archive screening and ACL checks | Does not establish defense against all local attacks |
| Portability to another Windows PC | Clean extraction on development PC | Different physical PC not tested |

The core distinction is **evidence ≠ interpretation ≠ authority**.

## MIT license and distribution boundaries

Eric has authorized this distinct public derivative under the complete [MIT License](LICENSE), **Copyright (c) 2026 Eric Staiger**, for authorized project-owned source and documentation. [License scope and external dependencies](LICENSE-REVIEW.md) distinguishes those materials from separately installed Python, Windows and Bee components. The [Wildline Continuity Reader](https://github.com/Lyra-Core-413/wildline-continuity-reader) remains a separate MIT-licensed, fictional-only artifact; this Bridge also contains the optional consent-gated adapter.

Source publication grants no account access or rights to anyone's personal records. Real observations, private receipts, personal Core state, credentials and protected Lab artifacts remain excluded. This release is prepared for a new public repository without the private repository's history. Its publication/access status and final commit/ZIP verification are recorded separately. No Bee executable is bundled or relicensed.

**Preserve the line. Keep it wild.**

The v1.1-public.1 derivative contains 37 files and retains the existing 107 fictional/mock tests. It replaces inherited private refusal-policy metadata with a fictional public policy fingerprint, with the corresponding H5 engine pin refreshed. This is a disclosed source difference from the private package. The earlier 28-file v1.1 package, historical replay and saved genuine evidence remain preserved separately.

**Live v1.1 single-Fact recovery ≠ historical change replay ≠ full sync.**

**Bee is an evidence source, not automatic truth or permission.**

**Lyra Core: personal reference; Wildline: portable architecture; Wildline Lab: isolated testing.**

**Portable constitution. Non-portable biography.**

**411 Recover → 413 Challenge → 412 Reconstruct**

## VERIFIED / EXPERIMENTAL / FUTURE VISION

VERIFIED means a bounded behavior supported by an attributed retained report or local operation check. EXPERIMENTAL identifies separate Lab work. FUTURE VISION identifies capabilities not delivered here. None means production readiness or independent physical-machine verification.

## Public derivative and integrity

This public derivative is v1.1-public.1: 37 files, with 35 payload files bound by PACKAGE-MANIFEST.json and the manifest bound by PACKAGE-ANCHOR.sha256. It has a new seal; the original private packages and earlier seals remain preserved separately. Any later documentation or other packaged-file change requires a new version, refreshed manifest/anchor and verification; never reuse an old seal. The retained `WILDLINE_PRIVATE_SINGLE_BRIDGE_V1` manifest format is an internal compatibility identifier, not a repository-visibility statement.

The earlier private v1.1 releases have retained 107-test fictional/mock verification on the development Windows PC. This public derivative adds MIT licensing and public setup documentation, replaces the private refusal-policy fingerprint with a fictional one, and refreshes the affected H5 engine pin and package seal. Tests, launchers, fixtures and dependency bytes are preserved. Its own offline test results and final GitHub ZIP/access checks must be attributed to the separate public-release verification record. This revision performs no new live Bee operation or second-computer test.

[Dated implementation note](docs/IMPLEMENTATION-RECORD-NOTE.md) explains preparation-era statements.

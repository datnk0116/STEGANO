# LOGBOOK — UET.CN3124 Steganography CTF
**Project:** Blue 3 (image) and Sleepy Alarm (audio)  
**Repository:** `datnk0116/STEGANO`  
**Purpose:** chronological record of the work actually performed, commands executed, observed outputs, and limitations.

Work-duration figures marked as estimates are self-reported and were not timed; timestamps in screenshots and saved logs anchor particular events, not total time worked.

> This logbook is an evidence record, not a plan. Entries describe completed actions only. A result is marked successful only when the corresponding execution output was observed.

**Retrospective note on the reproduction records:** Some early project work was committed before its corresponding logbook entry was recorded because the logbook update was missed at the time. The later runs marked “Re-executed” and the records under `results/reproduction-*` were added to supplement those documentation gaps by rerunning commands and preserving their outputs. Their timestamps refer to the later reruns, not to the original work or commits; they should not be read as contemporaneous records.


---

<a id="entry-00"></a>
## Entry 00 — Environment setup

**Appendix/report:** [Appendix A.2](report/APPENDIX.md#app-a2-environment-setup) · [Report §3](report/REPORT.md#report-environment)

**Date:** 16 November 2026  
**Platform:** macOS, MacBook Air<br>
**Python recorded for 16 November:** 3.14.10 (unverified; no retained terminal transcript)<br>
**Environment used:** `.venv` (its interpreter at the 16 November run could not be independently verified)<br>
**pip:** upgraded from 26.2.2 to 26.3

**Hypothesis tested:** the declared dependencies install successfully and the required modules import under the chosen Python environment.

I created and activated the virtual environment, upgraded pip, installed the dependencies from `requirements.txt`, and generated a dependency freeze with `python -m pip freeze`.

Packages installed:

- NumPy 2.5.5
- Pillow 13.0.0
- SciPy 1.18.1
- SoundFile 0.14.0
- cffi 2.1.1
- pycparser 3.12
- typing-extensions 4.16.0

Direct imports of NumPy, Pillow, SciPy, and SoundFile succeeded.

**Observed outcome:** dependency installation and direct import checks completed without error.

**Scope:** this confirms the environment setup and imports; it does not, by itself, validate either challenge decoder.

**Source limitation:** complete original terminal transcripts for Entries 00–05 were not retained. The bare `python` commands shown there do not identify the executable or version. Interpreter details recorded for later replays apply only to those replays.

**Supplemental environment verification — 18 November 2026:** the existing `.venv` was found to use Python 3.9.6, below the README's Python 3.10 minimum. A separate `.venv/repro314` was created with Python 3.14.10. This later check does not establish which interpreter `.venv` used on 16 November; the original 16 November Python 3.14.10 value remains unverified (consistent with Report §3). The recorded setup interval was 15:06:20–15:07:36 (+07); virtual-environment creation occurred immediately before the start marker.

Commands:

```text
python3.14 -m venv .venv/repro314
.venv/repro314/bin/python -m pip install --upgrade pip
.venv/repro314/bin/python -m pip install -r requirements.txt
.venv/repro314/bin/python -m pip check
```

The pip self-upgrade attempt could not resolve `pypi.org`; pip remained at 26.2.2. Dependency installation then completed, and `pip check` reported no broken requirements. Pip also warned that its user cache directory was not writable and disabled caching. The environment record is in [`setup-time.txt`](results/reproduction-2026-11-18/setup-time.txt), [`setup-end.txt`](results/reproduction-2026-11-18/setup-end.txt), [`environment-check.log`](results/reproduction-2026-11-18/environment-check.log), [`environment-freeze.txt`](results/reproduction-2026-11-18/environment-freeze.txt), [`pip-install.log`](results/reproduction-2026-11-18/pip-install.log), and [`pip-check.log`](results/reproduction-2026-11-18/pip-check.log).

**Terminal screenshot — 18 November 2026, 16:12:56 (+07):** the environment was checked again in the live Terminal. The screen shows Python 3.14.10, `pip install -r requirements.txt` reporting the dependencies already satisfied, and `pip check` reporting no broken requirements: [setup/configuration capture](evidence/terminal/2026-11-18-setup-terminal.png).

---

<a id="entry-01"></a>
## Entry 01 — Blue 3 image extraction

**Appendix/report:** [Appendix A.3](report/APPENDIX.md#app-a3-blue-3-extraction) · [Report §4.1](report/REPORT.md#report-methods) · [§5](report/REPORT.md#report-results)

**Date:** 16 November 2026  
**Input:** `data/blue3/blue.png`

**Hypothesis tested:** the image's diagonal RGB differences yield a candidate accepted by the challenge flag-format check.

**Command executed:**

```bash
PYTHONPATH=src python -m stegano blue3 data/blue3/blue.png
```

**Observed output:**

- Decoded flag: `byuctf{more_blue_steganography_da_ba_dee_nkiY9CyP}`
- Candidate length accepted: 50 characters
- `format_valid`: `true`
- Exit code: `0`

**Outcome:** extraction succeeded.

**Interpretation:** the implemented Blue 3 extraction routine recovered a candidate accepted by the challenge flag-format check. The command output, rather than the flag text alone, is the relevant execution evidence.

**Re-executed — 18 November 2026, 15:08:05–15:08:53 (+07):** `env PYTHONPATH=src .venv/repro314/bin/python -m stegano blue3 data/blue3/blue.png` returned the same valid 50-character flag with exit code 0. Output: [`blue3.log`](results/reproduction-2026-11-18/blue3.log).

**Terminal screenshot — 18 November 2026, 16:13:32 (+07):** the command was run again in Terminal; the capture shows the command and accepted 50-character candidate: [Blue 3 run](evidence/terminal/2026-11-18-blue3-terminal.png).

---

<a id="entry-02"></a>
## Entry 02 — Sleepy Alarm, reference-assisted extraction

**Appendix/report:** [Appendix A.4](report/APPENDIX.md#app-a4-sleepy-alarm-reference-assisted) · [Report §4.2](report/REPORT.md#report-methods) · [§5](report/REPORT.md#report-results)

**Date:** 16 November 2026  
**Target audio:** `data/sleepy_alarm/morning_n_breakfast.mp3`  
**Reference audio:** `data/sleepy_alarm/morning_n_breakfast_original.mp3`

**Hypothesis tested:** aligning and subtracting the original recording reveals a valid payload in the target.

**Command executed:**

```bash
PYTHONPATH=src python -m stegano sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3 --reference data/sleepy_alarm/morning_n_breakfast_original.mp3
```

**Observed output:**

- Decoded flag: `ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}`
- `format_valid`: `true`
- Symbol count: 350
- Separator count: 38
- Alignment lag: 1,729 samples
- Normalized correlation: 0.9998734358246231
- Target start sample: 1,729
- Amplitude cluster centers:
  - 0.00010346536568754544
  - 0.0019974891068537835
  - 0.00497272470857525
- Byte errors: none
- Exit code: `0`

**Outcome:** reference-assisted extraction succeeded.

**Interpretation and limitation:** this run explicitly used the original recording as a reference for alignment/subtraction. It is therefore a reference-assisted result, not proof that the payload can be extracted blindly from the distributed audio alone.

**Re-executed — 18 November 2026, 15:08:05–15:08:53 (+07):** `env PYTHONPATH=src .venv/repro314/bin/python -m stegano sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3 --reference data/sleepy_alarm/morning_n_breakfast_original.mp3` returned the same valid flag, 350 symbols, 38 separators, and exit code 0. Output: [`sleepy-alarm-reference-assisted.log`](results/reproduction-2026-11-18/sleepy-alarm-reference-assisted.log).

**Terminal screenshot — 18 November 2026, 16:14:39 (+07):** a subsequent run shows the decoded flag, `format_valid: true`, 350 symbols, 38 separators, and no errors: [reference-assisted run](evidence/terminal/2026-11-18-audio-assisted-terminal.png).

---

<a id="entry-03"></a>
## Entry 03 — Sleepy Alarm, reference-free extraction

**Appendix/report:** [Appendix A.5](report/APPENDIX.md#app-a5-sleepy-alarm-reference-free) · [Report §5](report/REPORT.md#report-results) · [§8](report/REPORT.md#report-limitations)

**Date:** 16 November 2026  
**Target audio:** `data/sleepy_alarm/morning_n_breakfast.mp3`  
**Reference audio:** none

**Hypothesis tested:** the target recording alone can yield a valid payload.

**Command executed:**

```bash
PYTHONPATH=src python -m stegano sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3
```

**Observed output:**

- Decoded fragment: `ictsl33p_Nauk_arm_224dcb2}`
- `format_valid`: `false`
- Symbol count: 350
- Separator count: 49
- Malformed byte groups: 20
- Alignment: not performed
- Exit code: `2`

**Outcome:** unsuccessful extraction.

**Interpretation:** without the reference recording, the current implementation did not recover a valid flag. This failure is retained as a separate experimental result and must not be described as a successful blind extraction.

**Re-executed — 18 November 2026, 15:08:05–15:08:53 (+07):** `env PYTHONPATH=src .venv/repro314/bin/python -m stegano sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3` again returned an invalid fragment, 20 malformed byte groups, and exit code 2. Output: [`sleepy-alarm-reference-free.log`](results/reproduction-2026-11-18/sleepy-alarm-reference-free.log).

**Terminal screenshot — 18 November 2026, 16:15:19 (+07):** the target-only command was run again and displays `format_valid: false`; the failure is retained as the result: [reference-free run](evidence/terminal/2026-11-18-audio-reference-free-terminal.png). The detailed earlier rerun log records 20 malformed groups and exit code 2.

---

<a id="entry-04"></a>
## Entry 04 — Automated tests

**Appendix/report:** [Appendix A.6](report/APPENDIX.md#app-a6-initial-automated-tests) · [Report §5](report/REPORT.md#report-results)

**Date:** 16 November 2026

**Hypothesis tested:** the Blue 3 and reference-assisted Sleepy Alarm integration paths pass on the supplied artifacts.

**Command executed:**

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

**Observed output:**

- Tests run: 2
- Blue 3 integration test: passed
- Sleepy Alarm reference-assisted integration test: passed
- Runtime: 0.294 seconds
- Summary: `Ran 2 tests in 0.294s — OK`
- Exit code: `0`

**Outcome:** both tests in the current test suite passed.

**Scope:** the audio integration test covers reference-assisted extraction. The two passing tests do not contradict or erase the separate reference-free failure recorded in Entry 03. This is the initial two-test run; later totals refer to different test sets and snapshots, not cumulative counts. Entry 06's nine tests were the visualizer-focused verification set. Entry 07's five were the repository-wide suite at the alignment snapshot: the two existing challenge tests plus three new tests in `tests/test_audio_alignment.py`. Git history confirms that this five-test suite followed the alignment-test addition; the visualization test module was committed separately later on 17 November. Subsequent test additions match the 17 tests in Entry 08 and 19 in Entry 10. The separate `STEGO` redo has no visualization suite; its historical six-test log covers alignment, Blue 3 CLI/solver, and audio solver tests. Entry 06 has no retained raw test transcript or exact test-file snapshot; its screenshots show visualizer pages rather than test output.

**Re-executed — 18 November 2026, 15:08:05–15:08:53 (+07):** `env PYTHONPATH=src .venv/repro314/bin/python -m unittest discover -s tests -v` passed all 19 tests in 7.864 seconds; exit code 0. Full output: [`unittest.log`](results/reproduction-2026-11-18/unittest.log). AppTest printed a missing-`ScriptRunContext` warning in bare mode; the page test passed. The session interval and command statuses are in [`exit-status.txt`](results/reproduction-2026-11-18/exit-status.txt).

**Terminal screenshot — 18 November 2026, 16:15:58 (+07):** another run passed all 19 tests in 2.285 seconds; the capture shows the final test output and `OK`: [unittest run](evidence/terminal/2026-11-18-unittest-terminal.png).

The combined setup, decoder, and test replay interval was 15:06:20–15:08:53 (+07), or 2 minutes 33 seconds between the saved markers.

---

<a id="entry-05"></a>
## Entry 05 — Input integrity recorded during the experiment

**Appendix/report:** [Appendix A.7](report/APPENDIX.md#app-a7-input-artifact-integrity) · [Report §3](report/REPORT.md#report-artifacts)

**Date:** 16 November 2026

**Hypothesis tested:** the three SHA-256 values identify the exact challenge input bytes used in the runs.

Recorded SHA-256 values for the three challenge inputs:

| Input artifact | SHA-256 |
|---|---|
| `data/blue3/blue.png` | `009dab85bf6ccc5b42b8efa5f959ab6efa0c556b37eb6b4a77a21ec3356b721e` |
| `data/sleepy_alarm/morning_n_breakfast.mp3` | `bd181876c2d28152b9c3982fd88945d4e681fd93d49477622ea5841a3ff25ae2` |
| `data/sleepy_alarm/morning_n_breakfast_original.mp3` | `d0c283834955e54d68b0bba723ccd194142a428d2de74722e5f1dff3ccbd94ad` |

**Interpretation:** the three hashes identify the challenge input files used in the recorded experiments.

**Recheck — 18 November 2026:** `shasum -a 256 data/blue3/blue.png data/sleepy_alarm/morning_n_breakfast.mp3 data/sleepy_alarm/morning_n_breakfast_original.mp3` produced the same three hashes. Output: [`input-sha256.txt`](results/reproduction-2026-11-18/input-sha256.txt).

---

<a id="entry-06"></a>
## Entry 06 — Decoder-backed visualization implementation and verification

**Appendix/report:** [Appendix A.8](report/APPENDIX.md#app-a8-first-visualizer-verification) · [Report Appendix B](report/REPORT.md#report-visualization)

**Date:** 16 November 2026

**Estimated effort:** approximately 5 hours for the 16 November work session covering Entries 00–06 (self-reported estimate; no timer record was preserved). Evidence anchors: visualization screenshots 21:40:24–21:41:45 and related commits 23:07:59, 23:16:09, and 23:22:18 (+07).

**Hypothesis tested:** the visualization pages display results and signal/image diagnostics from the decoder and challenge artifacts.

Added a Streamlit overview and Blue 3 and Sleepy Alarm pages with shared decoder/data helpers and Plotly charts. During this visualization work, the decoder implementation and challenge artifacts were not changed. Audio waveform points are sampled in bounded blocks for display; decoder calls use the original files.

Verification recorded for this work:

- Nine unit tests passed; no raw terminal transcript or exact test-file snapshot was preserved for this run.
- Streamlit `AppTest` reported no exceptions for the overview and both challenge pages.
- The live app health endpoint returned `ok`.
- Blue 3 and reference-assisted Sleepy Alarm returned format-valid results. Reference-free Sleepy Alarm remained invalid with 20 byte errors.

Five screenshots are stored in `evidence/visualization/`.

**Re-executed visualization check — 18 November 2026, 15:46:46–15:47:40 (+07):**

```text
env PYTHONPATH=src .venv/repro314/bin/streamlit run visualization/app.py --server.headless true --server.port 8765
```

The first launch was blocked while binding localhost (`PermissionError: [Errno 1] Operation not permitted`). Retried with the required local-server permission, Streamlit started and the `/_stcore/health` endpoint returned `ok`. The server was stopped after the health check. Logs: [`streamlit.log`](results/reproduction-2026-11-18/streamlit.log) (initial failure), [`streamlit-retry.log`](results/reproduction-2026-11-18/streamlit-retry.log), [`streamlit-health.log`](results/reproduction-2026-11-18/streamlit-health.log), and [`visualizer-time.txt`](results/reproduction-2026-11-18/visualizer-time.txt).

**Terminal screenshot — 18 November 2026, 16:18:28–16:18:49 (+07):** Streamlit was launched with `--server.address 127.0.0.1`; the `/_stcore/health` request returned `ok`, and the process was stopped afterward. The capture shows the localhost-only URL and startup output: [visualizer launch](evidence/terminal/2026-11-18-streamlit-terminal.png).

---

<a id="entry-07"></a>
## Entry 07 — Audio resampling and alignment regression test

**Appendix/report:** [Appendix A.9](report/APPENDIX.md#app-a9-audio-alignment-regression) · [Report §5](report/REPORT.md#report-results)

**Date:** 17 November 2026

**Estimated effort:** 2–3 hours (self-reported; no timer record was preserved). Evidence anchor: alignment-helper commit at 08:22:57 (+07), covering 134 insertions across five files.

**Hypothesis tested:** the alignment helper resamples mismatched sample rates, finds the known delay, and returns only the shared overlap.

Added an independent audio alignment helper that resamples the reference signal to the target sample rate and estimates the time offset with cross-correlation. The returned aligned signals are limited to their shared overlap. Regression tests use generated synthetic signals to cover differing sample rates, a time offset, and differing signal lengths; no MP3 files are needed by these tests.

**Command executed:**

```bash
python -m unittest discover -s tests -v
```

**Observed output:** all 5 tests passed, including the existing image and reference-assisted audio tests and 3 audio alignment tests. Summary: `Ran 5 tests in 0.311s — OK`. No raw terminal transcript is preserved for this run.

**Outcome:** the full test run passed. No additional measurements were recorded.

---

<a id="entry-08"></a>
## Entry 08 — Resampling and correlation diagnostics in the visualizer

**Appendix/report:** [Appendix A.10](report/APPENDIX.md#app-a10-correlation-diagnostics) · [Report §4.2](report/REPORT.md#report-methods)

**Date:** 17 November 2026

**Estimated effort:** approximately 2.5 hours for Entries 08–09 together (self-reported; no timer record was preserved). Evidence anchors: commits 21:55:17–22:24:50 and the alignment screenshot at 22:18:35 (+07).

**Hypothesis tested:** the plotted normalized-correlation peak matches the lag selected by the alignment routine.

Refactored the shared resampling and correlation path in `src/audio_alignment.py` and added `alignment_diagnostics` for visualization data. The Sleepy Alarm page now displays reference waveforms before and after resampling, the normalized correlation profile with the selected lag marked, and the existing aligned overlap and residual. Plot downsampling is limited to display; the alignment uses full-resolution signals.

**Verification:**

- `python -m unittest discover -s tests -v` passed 17 tests (no raw terminal transcript is linked for this run).
- Streamlit `AppTest` loaded the overview and both challenge pages without exceptions.
- Synthetic signals with different sample rates, delay, and lengths confirmed that the correlation-profile peak matches the selected alignment lag.

**Outcome:** the visualizer diagnostics and regression coverage passed. No changes were made to the decoder or challenge MP3 files.

---

<a id="entry-09"></a>
## Entry 09 — Audio alignment visualizer and evidence

**Appendix/report:** [Appendix A.11](report/APPENDIX.md#app-a11-alignment-visual-evidence) · [Report Appendix B](report/REPORT.md#report-visualization)

**Date:** 17 November 2026

**Session estimate:** included in the 2.5-hour self-reported estimate recorded in Entry 08; no independent time measurement is preserved.

**Hypothesis tested:** the displayed waveforms, lag and overlap describe the signals used by the current alignment run.

Expanded the Sleepy Alarm visualizer to show the input sample rates and frame counts; reference waveforms before and after resampling to the target rate; the normalized cross-correlation profile in milliseconds with the selected lag marked; and the aligned target/reference overlap and residual. The charts use bounded samples for display while alignment diagnostics use full-resolution signals. The page also reports target sample rate, selected lag, correlation, and overlap length.

Added `evidence/visualization/Screenshot 2026-11-17 at 22.18.35.png`, which captures these views. In the shown run, both files were at 44,100 Hz; the target had 441,840 frames and reference had 438,912 frames. The selected lag was 1,729 samples, correlation was 0.999873436, and overlap was 438,912 samples.

**Outcome:** the screenshot records the expanded visualizer output and its observed alignment values; it is visual evidence, not a separate test run.

---

<a id="entry-10"></a>
## Entry 10 — ASK and Blue 3 diagnostic visualizations

**Appendix/report:** [Appendix A.12](report/APPENDIX.md#app-a12-ask-and-blue-3-diagnostics) · [Report §4](report/REPORT.md#report-methods) · [§6.1](report/REPORT.md#report-methods)

**Date:** 18 November 2026

**Estimated effort:** approximately 3 hours (self-reported; no timer record was preserved). Evidence anchors: screenshots 06:31:35–06:47:19 and the diagnostics commit at 06:49:47 (+07); the commit covered 308 insertions and 30 deletions across 14 files.

**Hypothesis tested:** the displayed ASK values and Blue 3 block diagnostics expose the intermediate measurements used by the decoders.

### Implementation

- Added Sleepy Alarm diagnostics for the exact channel-0 measurements used by the decoder: per-symbol ASK levels and labels, the three cluster centers, and decoded byte groups. Extraction results and visualization diagnostics are reported separately.
- Added Blue 3 diagnostics for the inferred RGB baseline and selected diagonal blocks, including pixel bounds, per-channel deltas, summed character codes, and decoded characters.
- Updated the Sleepy Alarm and Blue 3 Streamlit pages and the README, including audio resampling and cross-correlation views.

### Verification

**Command:**

```text
env PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

**Observed result:** all 19 tests passed, including AppTest for the overview and both challenge pages. `git diff --check` completed without errors.

I recall `.venv/bin/python` running Python 3.14.10 for this 06:49 run, though the command transcript did not retain a `--version` output so that interpreter remains unverified. A later verified replay under isolated `.venv/repro314/bin/python` recorded Python 3.14.10, whereas the supplemental check at 15:06 found the pre-existing `.venv` running Python 3.9.6. The reference-assisted run reported 350 symbols and 38 separators in the 7-second window, with no NUL characters in the decoded byte groups. Blue 3 diagnostics reconstructed the selected valid candidate from its diagonal blocks.

### Evidence

- `evidence/visualization/Screenshot 2026-11-18 at 06.31.35.png` — Blue 3 image with the selected diagonal blocks highlighted.
- `evidence/visualization/Screenshot 2026-11-18 at 06.31.58.png` — Blue 3 candidate, RGB baseline, and per-block character/code table.
- `evidence/visualization/Screenshot 2026-11-18 at 06.47.19.png` — current Sleepy Alarm ASK metrics, per-symbol clusters, and decoder parameters.
- `evidence/visualization/Screenshot 2026-11-18 at 06.34.48.png` — decoded byte groups, bits, characters, code points, and error indicators.

---

<a id="entry-11"></a>
## Entry 11 — Artifact integrity and full-flag verification

**Appendix/report:** [Appendix A.14](report/APPENDIX.md#app-a14-artifact-integrity-and-exact-match) · [Report §3](report/REPORT.md#report-artifacts) · [§5](report/REPORT.md#report-results)

**Date/time:** 18 November 2026; timestamp sample 20:08:39 (+07)

**Execution duration:** the unittest command reported 2.691 seconds. Total documentation and evidence-preparation time was not timed.

**Technical hypothesis:** the three challenge files match their pinned manifest size and SHA-256 values, and both decoders return the complete expected flag strings rather than only matching a prefix.

### Commands and observed results

1. `python scripts/verify_artifacts.py` — exit code 0; all three artifacts passed size and SHA-256 checks. The recorded output is [`artifact-verification-2026-11-18.log`](results/reproduction-2026-11-18/artifact-verification-2026-11-18.log).
2. `env PYTHONPATH=src .venv/repro314/bin/python -m unittest discover -s tests -v` — exit code 0; all 21 tests passed, including both full-string exact-match tests. Runtime was 2.691 seconds. The AppTest emitted three `missing ScriptRunContext` warnings in bare mode; the page test still passed. Full output: [`unittest-exact-match-2026-11-18.log`](results/reproduction-2026-11-18/unittest-exact-match-2026-11-18.log).

The exact-match tests verified Blue 3 at 50 characters and reference-assisted Sleepy Alarm at 39 characters. The audio decoder reported 350 symbols, 38 separators, and no byte errors. The dashboard showed a 1,729-sample alignment lag measured by cross-correlation at run time; this is an observed alignment offset and is not attributed solely to MP3 encoder delay.

**Errors/corrections:** no command or test failed. The Streamlit bare-mode warnings are preserved in the test log; they did not affect the passing result.

**Screenshot evidence:** [verification dashboard capture](evidence/visualization/2026-11-18-verification-dashboard.png), showing the 3/3 integrity status, both exact-match statuses, and artifact table.

**Terminal log screenshot:** [verification run log](evidence/terminal/2026-11-18-verification-log-terminal.png). The capture shows the artifact-verification output, both exact-match test lines, exit code 0, and the 21-test summary. The complete command output remains in the linked `.log` files above.

---

<a id="entry-12"></a>
## Entry 12 — ASK prefix preservation and output regression

**Appendix/report:** [Appendix A.15](report/APPENDIX.md#app-a15-ask-prefix-preservation-and-output-regression) · [Report §4.2 and §5](report/REPORT.md#report-methods)

**Date:** 19 November 2026

**Technical hypothesis:** projecting each symbol from its original target samples with carrier phase anchored to global sample indices will preserve leading ASK symbols when reference alignment begins inside a symbol.

### Implementation and regression case

The ASK decoder now retains the target prefix before the aligned overlap and decodes from sample zero. Per-symbol I/Q projection uses the original samples in each symbol window and the global sample index for carrier phase, so each measurement uses the intended target-sample window. The decoder result includes the number of decoded complete-byte characters.

The earlier reference-assisted path decoded only the aligned target/reference overlap (`x-y`), omitting target samples before the overlap. The change prepends that target prefix and keeps symbol timing and carrier phase anchored at target sample zero. The synthetic regression places the overlap start one and a half symbol periods into the target; it checks the first 16 labels, initial ASK level, and full 39-character flag. The preserved records do not identify a separate failure on the official file that first triggered the change. The official file returns the same 39-character flag before and after the change. Its 350-symbol count is the 7-second window at 50 baud (`7 × 50`), so that count does not distinguish the two decoder versions.

### Commands and observed results

```text
env PYTHONPATH=src .venv/repro314/bin/python -m unittest discover -s tests -v
env PYTHONPATH=src .venv/repro314/bin/python -m stegano sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3 --reference data/sleepy_alarm/morning_n_breakfast_original.mp3
```

The full unittest run passed all 22 tests in 2.966 seconds with exit code 0. The first attempt using the system Python could not import Streamlit; rerunning with the project's Python 3.14 environment succeeded. A review rerun on 19 November passed all 22 tests in 2.826 seconds with exit code 0. AppTest printed three `missing ScriptRunContext` warnings in bare mode; the page test still passed.

The reference-assisted decoder run returned `format_valid: true`, `reference_assisted: true`, 350 symbols, 38 separators, 39 characters, and no byte errors. The decoded flag was `ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}`. Alignment reported a 1,729-sample lag and target start, with normalized correlation 0.9998734358246231.

The separate run manifest records the mode, 8,000 Hz carrier, 50 baud, 7-second window, input hashes, counts, and SHA-256 values for the JSON output and log. The original [`artifact_manifest.json`](results/artifact_manifest.json) remains the input-integrity record.

**Chronology and parameter provenance:** this ASK decoder change followed the earlier results in Entries 02 and 06–08. Those entries describe the earlier implementation; the 19 November run verifies the updated implementation against the same known challenge flag. The manifest confirms the settings used in that run, but no preserved record establishes how they were selected before the expected flag was known. The report therefore treats them as fixed decoder settings and the exact-match check as post-decode validation, not as evidence of blind parameter selection.

**Run artifacts:** [decoded output](results/reproduction-2026-11-19/sleepy-alarm-reference-assisted-output.json) · [run log](results/reproduction-2026-11-19/sleepy-alarm-reference-assisted.log) · [run manifest](results/reproduction-2026-11-19/sleepy-alarm-reference-assisted-manifest.json)

**Screenshots:** [Streamlit ASK diagnostics](evidence/visualization/2026-11-19-sleepy-alarm-streamlit.png) · [rendered run log](evidence/visualization/2026-11-19-sleepy-alarm-run-log.png)

The Streamlit screenshot shows the 350/38/39 metrics, the first 32 symbol projections, symbol boundaries, and the red alignment-overlap marker. The log screenshot shows the saved `.log` contents rendered in a browser; it is not a terminal capture.

---

<a id="entry-13"></a>
## Entry 13 — Sleepy Alarm asymmetric robustness

**Appendix/report:** [Appendix A.16](report/APPENDIX.md#app-a16-asymmetric-audio-robustness) · [Report §5 and Appendix B](report/REPORT.md#report-results)

**Date:** 19 November 2026

**Technical hypothesis:** reference-assisted decoding may tolerate one-sided resampling while failing when only one member of the target/reference pair is gain-scaled.

**Command:**

```text
env PYTHONPATH=src .venv/repro314/bin/python scripts/run_audio_asymmetric.py
```

**Observed result:** baseline PASS, reported separately from six variants. Baseline metrics were 350 symbols, 38 separators, 39 characters, 0 byte errors, and a measured alignment lag of 1,729 samples. Of the six one-sided variants, both 44,100→48,000→44,100 Hz round trips passed; gain ×0.5 and ×1.5 failed on both target-only and reference-only runs. The aggregate is **2/6 variants PASS**, with baseline excluded from the denominator.

| Changed file | Gain ×0.5 | Gain ×1.5 | Resample round trip |
|---|---|---|---|
| Target only | FAIL · 28 characters · 14 byte errors | FAIL · 34 characters · 4 byte errors | PASS · 39 characters · 0 byte errors |
| Reference only | FAIL · 36 characters · 5 byte errors | FAIL · 33 characters · 4 byte errors | PASS · 39 characters · 0 byte errors |

**Pass criterion:** `format_valid` is true, decoded text exactly matches the ground truth, and the decoder reports no byte errors. All transformations operated on temporary copies; the two original audio hashes still match the input manifest.

**Run artifacts:** [JSON](results/asymmetric/asymmetric_robustness.json) · [CSV](results/asymmetric/asymmetric_robustness.csv) · [run log](results/asymmetric/asymmetric_robustness.log).

**Regression verification:** `env PYTHONPATH=src .venv/repro314/bin/python -m unittest discover -s tests -v` passed all 22 tests in 2.713 seconds; exit code 0. The three Streamlit `missing ScriptRunContext` warnings appeared in bare mode; AppTest passed. Full output: [unittest.log](results/asymmetric/unittest.log).

**Evidence:** [Streamlit dashboard capture](evidence/visualization/2026-11-19-asymmetric-dashboard.png), showing the baseline, 2/6 and 4/6 metrics, heatmap, all six table rows, and the scope note. [Terminal run capture](evidence/terminal/2026-11-19-asymmetric-run-terminal.png) shows the script command, baseline, six result rows, and final 2/6 summary.

**Scope limitation:** results characterize this exact target/reference pair and these six transformations only; they do not establish general audio robustness.

---

<a id="entry-14"></a>
## Entry 14 — Steganalysis benchmark and extended robustness

**Appendix/report:** [Appendix A.17](report/APPENDIX.md#app-a17-steganalysis-benchmark-and-extended-robustness) · [Report §5 and §7.1](report/REPORT.md#report-benchmark)

**Date:** 20 November 2026; run output generated at 18:15:20 (+07)

**Technical hypothesis:** fixed image/audio triage heuristics can be measured against deterministic controls, and controlled transformations can expose recovery limits without changing the original challenge artifacts.

**Environment:** Python 3.14.10, `.venv/repro314`, existing project dependencies.

**Commands:**

```text
.venv/repro314/bin/python scripts/run_steganalysis_benchmark.py > results/steganalysis/benchmark-run.log 2>&1
.venv/repro314/bin/python scripts/run_extended_robustness.py > results/robustness/extended-robustness-run.log 2>&1
```

Both scripts completed with exit code 0.

**Benchmark result:**

| Medium | TP | TN | FP | FN | Recall | Samples |
|---|---:|---:|---:|---:|---:|---:|
| Image | 5 | 12 | 0 | 0 | 1.00 | 17 |
| Audio | 0 | 8 | 0 | 5 | 0.00 | 13 |

The image baseline identified all five positive samples and rejected all 12 synthetic benign controls. The audio baseline missed all five positive samples. Positive sets include official challenge files and deterministic derived variants; benign sets are synthetic and do not represent a real-world media corpus.

**Reference comparison:** reference-free decoding remains **FAIL**, with 350 symbols, 49 separators, 26 characters, and 20 malformed byte groups. Reference-assisted decoding returned the exact 39-character flag, 38 separators, and no byte errors. Expected text was used for post-decode validation only.

**Extended robustness:** Blue 3 passed 1/9 image variants (Gaussian blur radius 0.3); the other eight failed. Sleepy Alarm passed 7/23 trials, including its baseline. The six non-baseline passes were gain ×0.75, AWGN SNR 30 dB, and resampling round trip for both target-only and reference-only inputs. PASS requires valid format, exact ground-truth match, and zero byte errors.

**Open-source comparison:** Aperi'Solve, The-A-Files, and WavSteg are recorded as scope/method comparators only; no external tool was executed.

**Artifacts:** [benchmark JSON](results/steganalysis/benchmark.json) · [benchmark run log](results/steganalysis/benchmark-run.log) · [Blue 3 matrix JSON/CSV](results/robustness/blue3_extended_robustness.json) · [Sleepy Alarm matrix JSON/CSV](results/robustness/sleepy_alarm_robustness_matrix.json) · [robustness run log](results/robustness/extended-robustness-run.log).

**Evidence screenshots captured later the same day (19:23–19:30 +07):** [reference-assisted result excerpt](evidence/terminal/2026-11-20-reference-assisted-result-terminal.png) · [detector TP/TN/FP/FN metrics](evidence/terminal/2026-11-20-steganalysis-benchmark-metrics-terminal.png) · [reference-free audio FAIL details](evidence/terminal/2026-11-20-reference-free-audio-failure-terminal.png) · [extended robustness summary](evidence/terminal/2026-11-20-extended-robustness-summary-terminal.png) · [Sleepy Alarm result comparison](evidence/visualization/2026-11-20-sleepy-alarm-decoder-results.png) · [Sleepy Alarm ASK diagnostics](evidence/visualization/2026-11-20-sleepy-alarm-ask-diagnostics.png) · [Blue 3 RGB channel histogram and diagonal trace](evidence/visualization/2026-11-20-blue3-rgb-channel-histogram-and-diagonal-trace.png).

**Scope limitation:** fixed heuristics and single-artifact robustness matrices characterize only these generated controls, challenge files, and tested transformations. They do not establish detector performance or robustness on a broader media population.

---

<a id="entry-15"></a>
## Entry 15 — Automated quality gate and provenance

**Appendix/report:** [Appendix A.18](report/APPENDIX.md#app-a18-quality-gate-and-provenance) · [Report Appendix A](report/REPORT.md#report-quality-gate-provenance)

**Date:** 22 November 2026

**Objective:** run the artifact-integrity check, execute the project's discovered unittest suite, and generate provenance and quality-gate records from the observed results.

**Environment:** Python 3.14.10 in `.venv/repro314`.

**Command:**

```text
.venv/repro314/bin/python scripts/verify_reproducibility.py
```

**Historical result:** exit code 0. The unittest suite passed 22/22 tests, all three artifacts passed size/SHA-256 checks, and provenance status is `verified`. At that run, `submission_package` was `not_verified` because the archive had not been checked. The current archive and latest recheck are documented in Entry 16.

**Generated records:** [quality-gate.json](results/verification/quality-gate.json) · [provenance.json](results/verification/provenance.json) · [complete run log](results/verification/reproducibility.log).

**Terminal evidence:** [quality gate run](evidence/terminal/2026-11-22-quality-gate-run-with-initial-path-errors-terminal.png) (shows setup/path errors before the successful run) · [22-test summary](evidence/terminal/2026-11-22-unittest-22-tests-passed-terminal.png) · [artifact integrity 3/3](evidence/terminal/2026-11-22-unittest-and-artifact-integrity-terminal.png) · [artifact and provenance checks](evidence/terminal/2026-11-22-artifact-and-provenance-terminal.png). The unittest capture includes non-fatal Streamlit `missing ScriptRunContext` warnings; the suite ends with `Ran 22 tests` and `OK`.

<a id="entry-16"></a>
## Entry 16 — Visualization evidence review and capture

**Appendix/report:** [Appendix A.19](report/APPENDIX.md#app-a19-visualization-evidence-review) · [Report Appendix A and B](report/REPORT.md#report-quality-gate-provenance)

**Date:** 22 November 2026

**Objective:** index the dashboard evidence, identify redundant captures, and link the saved recheck records and generated report figures.

**Evidence captured:**

- Overview: [corrected status capture](evidence/visualization/2026-11-22-overview-corrected-status.png) shows artifact integrity and the two separate decoder outcomes; the reference-free result is visibly FAIL. The earlier [pre-fix capture](evidence/visualization/2026-11-22-overview-before-status-copy-fix.png) is retained as historical evidence; its green banner was misleading.
- Blue 3: [input/baseline](evidence/visualization/2026-11-22-blue3-input-baseline-overview.png) · [RGB histogram and diagonal trace](evidence/visualization/2026-11-22-blue3-rgb-histogram-diagonal-trace.png) · [selected candidate and block table](evidence/visualization/2026-11-22-blue3-selected-candidate-block-table.png).
- Sleepy Alarm: [audio metadata](evidence/visualization/2026-11-22-sleepy-audio-file-metadata.png) · [target/reference waveforms](evidence/visualization/2026-11-22-sleepy-target-reference-waveforms.png) · [reference resampling](evidence/visualization/2026-11-22-sleepy-reference-resampling.png) · [alignment correlation and residual](evidence/visualization/2026-11-22-sleepy-alignment-correlation-residual.png) · [ASK symbol clusters](evidence/visualization/2026-11-22-sleepy-ask-symbol-clusters.png) · [first 32 symbols and byte groups](evidence/visualization/2026-11-22-sleepy-first-32-symbols-byte-groups.png) · [assisted versus reference-free results](evidence/visualization/2026-11-22-sleepy-assisted-vs-free-results.png).
- Robustness: [asymmetric 2/6 result](evidence/visualization/2026-11-22-sleepy-asymmetric-robustness-2-of-6.png). This view documents the six one-sided variants, not the separate 23-trial matrix.

**Redundant evidence:** [the second alignment/residual capture](evidence/visualization/2026-11-22-sleepy-alignment-correlation-residual-repeat.png) substantially repeats the first; either one is sufficient for the final evidence set.

**Visualization evidence status:** the corrected Overview and current dashboard captures are indexed in [Appendix A.19](report/APPENDIX.md#app-a19-visualization-evidence-review). The repeated alignment/residual view is redundant. The four report figures are generated from the recheck JSON files and embedded in [Report §7.1 and Appendix A](report/REPORT.md#report-extended-robustness). The latest saved recheck passed 22/22 tests, verified 3/3 artifacts and provenance, and verified `submission_package_current.zip`; its [quality-gate JSON](results/recheck/quality-gate.json), [provenance JSON](results/recheck/provenance.json), and [complete run log](results/recheck/reproducibility.log) are linked in Appendix A.19.


---

<a id="entry-17"></a>
## Entry 17 — Independent ASK measurement, writeup comparison, and final verification

**Appendix/report:** [Report §4.3](report/REPORT.md#report-methods) · [§7.2](report/REPORT.md) · [Appendix A](report/REPORT.md#report-quality-gate-provenance) · [Appendix D](report/REPORT.md)

**Date:** 27 November 2026, 15:50 (+07)

**Hypothesis tested:** Independent spectral and envelope-transition measurement on the aligned Sleepy Alarm residual verifies the 8,000 Hz carrier, 50 baud (20 ms/symbol) rate, and 7.0 s framing window without reading challenge constants during estimation, and the full test, provenance, and archive checks pass on the finalized documentation.

**Work performed:**

- Implemented and ran `scripts/measure_ask_params.py` (`--self-check` and full challenge run) into `results/independent-measurement/`, with local terminal capture saved at `evidence/terminal/2026-11-27-independent-ask-measurement-terminal.png` (Figure D.7).
- Verified public CTF references accessed on 27 November 2026 (Cook1e's ImaginaryCTF 2024 writeup and official BYU-CSA / ImaginaryCTF 2024 challenge READMEs) and documented the comparison in `REPORT.md` §7.2 and IEEE Reference `[13]`.
- Updated `REPORT.md` (§4.3, §7.2, Appendix A–D, cover dates `27/11/2026` / `13/12/2026`), `README.md`, `.gitignore`, and `report/APPENDIX.md`, exported `report/24021404_UETCN3124_CTF_Report.pdf`, and ran the final packaging and quality gate into `results/final-2026-11-27/`.

**Commands and observed outputs:**

```bash
.venv/repro314/bin/python scripts/measure_ask_params.py --self-check
.venv/repro314/bin/python scripts/measure_ask_params.py
.venv/repro314/bin/python scripts/create_submission_zip.py
.venv/repro314/bin/python scripts/verify_reproducibility.py \
  --output results/final-2026-11-27/quality-gate.json \
  --provenance-output results/final-2026-11-27/provenance.json \
  --log-output results/final-2026-11-27/reproducibility.log
```

- `measure_ask_params.py --self-check`: `Self-check PASS: synthetic ASK parameters recovered within tolerance.` (exit code `0`).
- `measure_ask_params.py` (exit code `0`, `results/independent-measurement/ask_params.json`):
  - Alignment: `lag=1729` samples, `target_start_sample=1729`, `corr=0.999873`.
  - Carrier peak: `7999.9774 Hz` (`-0.0226 Hz` vs. 8,000 Hz); $\pm 100\text{ Hz}$ energy ratio `0.474145` (`47.41%`).
  - Envelope (~5 ms window = `220` samples / `4.9887 ms`): `222` transitions (`221` intervals; raw mean `31.3920 ms`, std `17.9522 ms`, median `20.4535 ms`).
  - Single-step intervals ($k=1$, $n=135$): mean `20.0702 ms`, std `1.5939 ms`, error vs. 20 ms `+0.0702 ms` (`0.35%`, `49.83 baud`).
  - Run-length normalized ($n=221$, $\max k=5$): mean `20.0206 ms`, std `1.2523 ms`, error vs. 20 ms `+0.0206 ms` (`0.10%`, `49.95 baud`).
  - Carrier drop-off: `7.0020 s` (sample `308,786`, `+0.0020 s` vs. 7.0 s); tail noise mean `0.000094`, max `0.000732`.
- `create_submission_zip.py` + `verify_reproducibility.py` (exit code `0`): `quality_gate: passed`, `22/22` tests PASS, `3/3` artifacts verified, `provenance: verified`, `submission_package: verified`.
- Saved records: [`ask_params.json`](results/independent-measurement/ask_params.json), [`ask_params.log`](results/independent-measurement/ask_params.log), [`quality-gate.json`](results/final-2026-11-27/quality-gate.json), [`provenance.json`](results/final-2026-11-27/provenance.json), [`reproducibility.log`](results/final-2026-11-27/reproducibility.log), and `submission_package_current.zip`.

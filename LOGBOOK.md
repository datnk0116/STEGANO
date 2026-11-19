# LOGBOOK — UET.CN3124 Steganography CTF
**Project:** Blue 3 (image) and Sleepy Alarm (audio)  
**Repository:** `datnk0116/STEGANO`  
**Purpose:** chronological record of the work actually performed, commands reported as executed, observed outputs, and limitations.

Estimated work duration is recorded within the corresponding entries, alongside their evidence timestamps and commands.

> This logbook is an evidence record, not a plan. Entries describe completed actions only. A result is marked successful only when the corresponding execution output was reported.

---

<a id="entry-00"></a>
## Entry 00 — Environment setup

**Appendix/report:** [Appendix A.2](report/APPENDIX.md#app-a2-environment-setup) · [Report §3](report/REPORT.md#report-environment)

**Date:** 16 November 2026  
**Platform:** macOS, MacBook Air  
**Python:** 3.14.10  
**Environment:** `.venv`  
**pip:** upgraded from 26.2.2 to 26.3

**Hypothesis tested:** the declared dependencies install successfully and the required modules import under the chosen Python environment.

The operator reported creating and activating the virtual environment, upgrading pip, installing the dependencies from `requirements.txt`, and generating a dependency freeze with `python -m pip freeze`.

Packages reported installed:

- NumPy 2.5.5
- Pillow 13.0.0
- SciPy 1.18.1
- SoundFile 0.14.0
- cffi 2.1.1
- pycparser 3.12
- typing-extensions 4.16.0

The operator also reported that imports of NumPy, Pillow, SciPy, and SoundFile succeeded.

**Observed outcome:** dependency installation and direct import checks completed without a reported error.

**Scope:** this confirms the reported environment setup and imports; it does not, by itself, validate either challenge decoder.

**Supplemental environment verification — 18 November 2026:** the existing `.venv` used Python 3.9.6, below the README's Python 3.10 minimum. A separate `.venv/repro314` was created with Python 3.14.10. The recorded setup interval was 15:06:20–15:07:36 (+07); virtual-environment creation occurred immediately before the start marker.

Commands:

```text
rtk python3.14 -m venv .venv/repro314
rtk proxy .venv/repro314/bin/python -m pip install --upgrade pip
rtk proxy .venv/repro314/bin/python -m pip install -r requirements.txt
rtk proxy .venv/repro314/bin/python -m pip check
```

The pip self-upgrade attempt could not resolve `pypi.org`; pip remained at 26.2.2. Dependency installation then completed, and `pip check` reported no broken requirements. Pip also warned that its user cache directory was not writable and disabled caching. The environment record is in [`setup-time.txt`](results/reproduction-2026-11-18/setup-time.txt), [`setup-end.txt`](results/reproduction-2026-11-18/setup-end.txt), [`environment-check.log`](results/reproduction-2026-11-18/environment-check.log), [`environment-freeze.txt`](results/reproduction-2026-11-18/environment-freeze.txt), [`pip-install.log`](results/reproduction-2026-11-18/pip-install.log), and [`pip-check.log`](results/reproduction-2026-11-18/pip-check.log).

**Terminal screenshot — 18 November 2026, 16:12:56 (+07):** the environment was checked again in the live Terminal. The screen shows Python 3.14.10, `pip install -r requirements.txt` reporting the dependencies already satisfied, and `pip check` reporting no broken requirements: [setup/configuration capture](evidence/terminal/2026-11-18-setup-terminal.png).

---

<a id="entry-01"></a>
## Entry 01 — Blue 3 image extraction

**Appendix/report:** [Appendix A.3](report/APPENDIX.md#app-a3-blue-3-extraction) · [Report §4.1](report/REPORT.md#report-method-image) · [§6.1](report/REPORT.md#report-blue3)

**Date:** 16 November 2026  
**Input:** `data/blue3/blue.png`

**Hypothesis tested:** the image's diagonal RGB differences yield a candidate accepted by the challenge flag-format check.

**Command reported as executed:**

```bash
PYTHONPATH=src python -m stegano blue3 data/blue3/blue.png
```

**Reported output:**

- Decoded flag: `byuctf{more_blue_steganography_da_ba_dee_nkiY9CyP}`
- Candidate length accepted: 50 characters
- `format_valid`: `true`
- Exit code: `0`

**Outcome:** successful extraction was reported.

**Interpretation:** the implemented Blue 3 extraction routine recovered a candidate accepted by the challenge flag-format check. The command output, rather than the flag text alone, is the relevant execution evidence.

**Re-executed — 18 November 2026, 15:08:05–15:08:53 (+07):** `rtk proxy env PYTHONPATH=src .venv/repro314/bin/python -m stegano blue3 data/blue3/blue.png` returned the same valid 50-character flag with exit code 0. Output: [`blue3.log`](results/reproduction-2026-11-18/blue3.log).

**Terminal screenshot — 18 November 2026, 16:13:32 (+07):** the command was run again in Terminal; the capture shows the command and accepted 50-character candidate: [Blue 3 run](evidence/terminal/2026-11-18-blue3-terminal.png).

---

<a id="entry-02"></a>
## Entry 02 — Sleepy Alarm, reference-assisted extraction

**Appendix/report:** [Appendix A.4](report/APPENDIX.md#app-a4-sleepy-alarm-reference-assisted) · [Report §4.2](report/REPORT.md#report-method-audio) · [§6.2](report/REPORT.md#report-audio-assisted)

**Date:** 16 November 2026  
**Target audio:** `data/sleepy_alarm/morning_n_breakfast.mp3`  
**Reference audio:** `data/sleepy_alarm/morning_n_breakfast_original.mp3`

**Hypothesis tested:** aligning and subtracting the original recording reveals a valid payload in the target.

**Command reported as executed:**

```bash
PYTHONPATH=src python -m stegano sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3 --reference data/sleepy_alarm/morning_n_breakfast_original.mp3
```

**Reported output:**

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

**Outcome:** successful reference-assisted extraction was reported.

**Interpretation and limitation:** this run explicitly used the original recording as a reference for alignment/subtraction. It is therefore a reference-assisted result, not proof that the payload can be extracted blindly from the distributed audio alone.

**Re-executed — 18 November 2026, 15:08:05–15:08:53 (+07):** `rtk proxy env PYTHONPATH=src .venv/repro314/bin/python -m stegano sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3 --reference data/sleepy_alarm/morning_n_breakfast_original.mp3` returned the same valid flag, 350 symbols, 38 separators, and exit code 0. Output: [`sleepy-alarm-reference-assisted.log`](results/reproduction-2026-11-18/sleepy-alarm-reference-assisted.log).

**Terminal screenshot — 18 November 2026, 16:14:39 (+07):** a subsequent run shows the decoded flag, `format_valid: true`, 350 symbols, 38 separators, and no errors: [reference-assisted run](evidence/terminal/2026-11-18-audio-assisted-terminal.png).

---

<a id="entry-03"></a>
## Entry 03 — Sleepy Alarm, reference-free extraction

**Appendix/report:** [Appendix A.5](report/APPENDIX.md#app-a5-sleepy-alarm-reference-free) · [Report §6.3](report/REPORT.md#report-audio-free) · [§8](report/REPORT.md#report-limitations)

**Date:** 16 November 2026  
**Target audio:** `data/sleepy_alarm/morning_n_breakfast.mp3`  
**Reference audio:** none

**Hypothesis tested:** the target recording alone can yield a valid payload.

**Command reported as executed:**

```bash
PYTHONPATH=src python -m stegano sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3
```

**Reported output:**

- Decoded fragment: `ictsl33p_Nauk_arm_224dcb2}`
- `format_valid`: `false`
- Symbol count: 350
- Separator count: 49
- Malformed byte groups: 20
- Alignment: not performed
- Exit code: `2`

**Outcome:** unsuccessful extraction.

**Interpretation:** without the reference recording, the current implementation did not recover a valid flag. This failure is retained as a separate experimental result and must not be described as a successful blind extraction.

**Re-executed — 18 November 2026, 15:08:05–15:08:53 (+07):** `rtk proxy env PYTHONPATH=src .venv/repro314/bin/python -m stegano sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3` again returned an invalid fragment, 20 malformed byte groups, and exit code 2. Output: [`sleepy-alarm-reference-free.log`](results/reproduction-2026-11-18/sleepy-alarm-reference-free.log).

**Terminal screenshot — 18 November 2026, 16:15:19 (+07):** the target-only command was run again and displays `format_valid: false`; the failure is retained as the result: [reference-free run](evidence/terminal/2026-11-18-audio-reference-free-terminal.png). The detailed earlier rerun log records 20 malformed groups and exit code 2.

---

<a id="entry-04"></a>
## Entry 04 — Automated tests

**Appendix/report:** [Appendix A.6](report/APPENDIX.md#app-a6-initial-automated-tests) · [Report §6.4](report/REPORT.md#report-tests)

**Date:** 16 November 2026

**Hypothesis tested:** the Blue 3 and reference-assisted Sleepy Alarm integration paths pass on the supplied artifacts.

**Command reported as executed:**

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

**Reported output:**

- Tests run: 2
- Blue 3 integration test: passed
- Sleepy Alarm reference-assisted integration test: passed
- Runtime: 0.294 seconds
- Summary: `Ran 2 tests in 0.294s — OK`
- Exit code: `0`

**Outcome:** both tests in the current test suite passed.

**Scope:** the audio integration test covers reference-assisted extraction. The two passing tests do not contradict or erase the separate reference-free failure recorded in Entry 03.

**Re-executed — 18 November 2026, 15:08:05–15:08:53 (+07):** `rtk proxy env PYTHONPATH=src .venv/repro314/bin/python -m unittest discover -s tests -v` passed all 19 tests in 7.864 seconds; exit code 0. Full output: [`unittest.log`](results/reproduction-2026-11-18/unittest.log). AppTest printed a missing-`ScriptRunContext` warning in bare mode; the page test passed. The session interval and command statuses are in [`exit-status.txt`](results/reproduction-2026-11-18/exit-status.txt).

**Terminal screenshot — 18 November 2026, 16:15:58 (+07):** another run passed all 19 tests in 2.285 seconds; the capture shows the final test output and `OK`: [unittest run](evidence/terminal/2026-11-18-unittest-terminal.png).

The combined setup, decoder, and test replay interval was 15:06:20–15:08:53 (+07), or 2 minutes 33 seconds between the saved markers.

---

<a id="entry-05"></a>
## Entry 05 — Input integrity recorded during the experiment

**Appendix/report:** [Appendix A.7](report/APPENDIX.md#app-a7-input-artifact-integrity) · [Report §6.5](report/REPORT.md#report-integrity)

**Date:** 16 November 2026

**Hypothesis tested:** the three SHA-256 values identify the exact challenge input bytes used in the runs.

The operator also supplied these SHA-256 values:

| Input artifact | SHA-256 |
|---|---|
| `data/blue3/blue.png` | `009dab85bf6ccc5b42b8efa5f959ab6efa0c556b37eb6b4a77a21ec3356b721e` |
| `data/sleepy_alarm/morning_n_breakfast.mp3` | `bd181876c2d28152b9c3982fd88945d4e681fd93d49477622ea5841a3ff25ae2` |
| `data/sleepy_alarm/morning_n_breakfast_original.mp3` | `d0c283834955e54d68b0bba723ccd194142a428d2de74722e5f1dff3ccbd94ad` |

**Interpretation:** the three hashes identify the challenge input files used in the reported experiments.

**Recheck — 18 November 2026:** `rtk proxy shasum -a 256 data/blue3/blue.png data/sleepy_alarm/morning_n_breakfast.mp3 data/sleepy_alarm/morning_n_breakfast_original.mp3` produced the same three hashes. Output: [`input-sha256.txt`](results/reproduction-2026-11-18/input-sha256.txt).

---

<a id="entry-06"></a>
## Entry 06 — Decoder-backed visualization implementation and verification

**Appendix/report:** [Appendix A.8](report/APPENDIX.md#app-a8-first-visualizer-verification) · [Report §5](report/REPORT.md#report-workflow)

**Date:** 16 November 2026

**Estimated effort:** 5 hours for the 16 November work session covering Entries 00–06. Evidence anchors: visualization screenshots 21:40:24–21:41:45 and related commits 23:07:59, 23:16:09, and 23:22:18 (+07).

**Hypothesis tested:** the visualization pages display results and signal/image diagnostics from the decoder and challenge artifacts.

Added a Streamlit overview and Blue 3 and Sleepy Alarm pages with shared decoder/data helpers and Plotly charts. The decoder implementation and challenge artifacts were not changed. Audio waveform points are sampled in bounded blocks for display; decoder calls use the original files.

Verification recorded for this work:

- Nine unit tests passed.
- Streamlit `AppTest` reported no exceptions for the overview and both challenge pages.
- The live app health endpoint returned `ok`.
- Blue 3 and reference-assisted Sleepy Alarm returned format-valid results. Reference-free Sleepy Alarm remained invalid with 20 byte errors.

Five screenshots are stored in `evidence/visualization/`.

**Re-executed visualization check — 18 November 2026, 15:46:46–15:47:40 (+07):**

```text
rtk proxy env PYTHONPATH=src .venv/repro314/bin/streamlit run visualization/app.py --server.headless true --server.port 8765
```

The first launch was blocked while binding localhost (`PermissionError: [Errno 1] Operation not permitted`). Retried with the required local-server permission, Streamlit started and the `/_stcore/health` endpoint returned `ok`. The server was stopped after the health check. Logs: [`streamlit.log`](results/reproduction-2026-11-18/streamlit.log) (initial failure), [`streamlit-retry.log`](results/reproduction-2026-11-18/streamlit-retry.log), [`streamlit-health.log`](results/reproduction-2026-11-18/streamlit-health.log), and [`visualizer-time.txt`](results/reproduction-2026-11-18/visualizer-time.txt).

**Terminal screenshot — 18 November 2026, 16:18:28–16:18:49 (+07):** Streamlit was launched with `--server.address 127.0.0.1`; the `/_stcore/health` request returned `ok`, and the process was stopped afterward. The capture shows the localhost-only URL and startup output: [visualizer launch](evidence/terminal/2026-11-18-streamlit-terminal.png).

---

<a id="entry-07"></a>
## Entry 07 — Audio resampling and alignment regression test

**Appendix/report:** [Appendix A.9](report/APPENDIX.md#app-a9-audio-alignment-regression) · [Report §6.4](report/REPORT.md#report-tests)

**Date:** 17 November 2026

**Estimated effort:** 2–3 hours. Evidence anchor: alignment-helper commit at 08:22:57 (+07), covering 134 insertions across five files.

**Hypothesis tested:** the alignment helper resamples mismatched sample rates, finds the known delay, and returns only the shared overlap.

Added an independent audio alignment helper that resamples the reference signal to the target sample rate and estimates the time offset with cross-correlation. The returned aligned signals are limited to their shared overlap. Regression tests use generated synthetic signals to cover differing sample rates, a time offset, and differing signal lengths; no MP3 files are needed by these tests.

**Command reported as executed:**

```bash
python -m unittest discover -s tests -v
```

**Reported output:** all 5 tests passed, including the existing image and reference-assisted audio tests and 3 audio alignment tests. Summary: `Ran 5 tests in 0.311s — OK`.

**Outcome:** the reported full test run passed. No additional measurements were recorded.

---

<a id="entry-08"></a>
## Entry 08 — Resampling and correlation diagnostics in the visualizer

**Appendix/report:** [Appendix A.10](report/APPENDIX.md#app-a10-correlation-diagnostics) · [Report §4.2](report/REPORT.md#report-method-audio)

**Date:** 17 November 2026

**Estimated effort:** 2.5 hours for Entries 08–09 together. Evidence anchors: commits 21:55:17–22:24:50 and the alignment screenshot at 22:18:35 (+07).

**Hypothesis tested:** the plotted normalized-correlation peak matches the lag selected by the alignment routine.

Refactored the shared resampling and correlation path in `src/audio_alignment.py` and added `alignment_diagnostics` for visualization data. The Sleepy Alarm page now displays reference waveforms before and after resampling, the normalized correlation profile with the selected lag marked, and the existing aligned overlap and residual. Plot downsampling is limited to display; the alignment uses full-resolution signals.

**Verification:**

- `python -m unittest discover -s tests -v` passed all 17 tests.
- Streamlit `AppTest` loaded the overview and both challenge pages without exceptions.
- Synthetic signals with different sample rates, delay, and lengths confirmed that the correlation-profile peak matches the selected alignment lag.

**Outcome:** the visualizer diagnostics and regression coverage passed. No changes were made to the decoder or challenge MP3 files.

---

<a id="entry-09"></a>
## Entry 09 — Audio alignment visualizer and evidence

**Appendix/report:** [Appendix A.11](report/APPENDIX.md#app-a11-alignment-visual-evidence) · [Report §5](report/REPORT.md#report-workflow)

**Date:** 17 November 2026

**Session estimate:** included in the 2.5-hour estimate recorded in Entry 08.

**Hypothesis tested:** the displayed waveforms, lag and overlap describe the signals used by the current alignment run.

Expanded the Sleepy Alarm visualizer to show the input sample rates and frame counts; reference waveforms before and after resampling to the target rate; the normalized cross-correlation profile in milliseconds with the selected lag marked; and the aligned target/reference overlap and residual. The charts use bounded samples for display while alignment diagnostics use full-resolution signals. The page also reports target sample rate, selected lag, correlation, and overlap length.

Added `evidence/visualization/Screenshot 2026-11-17 at 22.18.35.png`, which captures these views. In the shown run, both files were at 44,100 Hz; the target had 441,840 frames and reference had 438,912 frames. The selected lag was 1,729 samples, correlation was 0.999873436, and overlap was 438,912 samples.

**Outcome:** the screenshot records the expanded visualizer output and its observed alignment values; it is visual evidence, not a separate test run.

---

<a id="entry-10"></a>
## Entry 10 — ASK and Blue 3 diagnostic visualizations

**Appendix/report:** [Appendix A.12](report/APPENDIX.md#app-a12-ask-and-blue-3-diagnostics) · [Report §4.1](report/REPORT.md#report-method-image) · [§4.2](report/REPORT.md#report-method-audio)

**Date:** 18 November 2026

**Estimated effort:** 3 hours. Evidence anchors: screenshots 06:31:35–06:47:19 and the diagnostics commit at 06:49:47 (+07); the commit covered 308 insertions and 30 deletions across 14 files.

**Hypothesis tested:** the displayed ASK values and Blue 3 block diagnostics expose the intermediate measurements used by the decoders.

### Implementation

- Added Sleepy Alarm diagnostics for the exact channel-0 measurements used by the decoder: per-symbol ASK levels and labels, the three cluster centers, and decoded byte groups. Extraction results and visualization diagnostics are reported separately.
- Added Blue 3 diagnostics for the inferred RGB baseline and selected diagonal blocks, including pixel bounds, per-channel deltas, summed character codes, and decoded characters.
- Updated the Sleepy Alarm and Blue 3 Streamlit pages and the README, including audio resampling and cross-correlation views.

### Verification

**Command:**

```text
rtk env PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

**Observed result:** all 19 tests passed, including AppTest for the overview and both challenge pages. `rtk git diff --check` completed without errors.

The current reference-assisted run reported 350 symbols and 38 separators in the 7-second window, with no NUL characters in the decoded byte groups. Blue 3 diagnostics reconstructed the selected valid candidate from its diagonal blocks.

### Evidence

- `evidence/visualization/Screenshot 2026-11-18 at 06.31.35.png` — Blue 3 image with the selected diagonal blocks highlighted.
- `evidence/visualization/Screenshot 2026-11-18 at 06.31.58.png` — Blue 3 candidate, RGB baseline, and per-block character/code table.
- `evidence/visualization/Screenshot 2026-11-18 at 06.47.19.png` — current Sleepy Alarm ASK metrics, per-symbol clusters, and decoder parameters.
- `evidence/visualization/Screenshot 2026-11-18 at 06.34.48.png` — decoded byte groups, bits, characters, code points, and error indicators.

---

<a id="entry-11"></a>
## Entry 11 — Artifact integrity and full-flag verification

**Appendix/report:** [Appendix A.14](report/APPENDIX.md#app-a14-artifact-integrity-and-exact-match) · [Report §3](report/REPORT.md)

**Date/time:** 18 November 2026; timestamp sample 20:08:39 (+07)

**Execution duration:** the unittest command reported 2.691 seconds. Total documentation and evidence-preparation time was not timed.

**Technical hypothesis:** the three challenge files match their pinned manifest size and SHA-256 values, and both decoders return the complete expected flag strings rather than only matching a prefix.

### Commands and observed results

1. `rtk proxy python scripts/verify_artifacts.py` — exit code 0; all three artifacts passed size and SHA-256 checks. The recorded output is [`artifact-verification-2026-11-18.log`](results/reproduction-2026-11-18/artifact-verification-2026-11-18.log).
2. `rtk proxy env PYTHONPATH=src .venv/repro314/bin/python -m unittest discover -s tests -v` — exit code 0; all 21 tests passed, including both full-string exact-match tests. Runtime was 2.691 seconds. The AppTest emitted three `missing ScriptRunContext` warnings in bare mode; the page test still passed. Full output: [`unittest-exact-match-2026-11-18.log`](results/reproduction-2026-11-18/unittest-exact-match-2026-11-18.log).

The exact-match tests verified Blue 3 at 50 characters and reference-assisted Sleepy Alarm at 39 characters. The audio decoder reported 350 symbols, 38 separators, and no byte errors. The dashboard showed a 1,729-sample alignment lag measured by cross-correlation at run time; this is an observed alignment offset and is not attributed solely to MP3 encoder delay.

**Errors/corrections:** no command or test failed. The Streamlit bare-mode warnings are preserved in the test log; they did not affect the passing result.

**Screenshot evidence:** [verification dashboard capture](evidence/visualization/2026-11-18-verification-dashboard.png), showing the 3/3 integrity status, both exact-match statuses, and artifact table.

**Terminal log screenshot:** [verification run log](evidence/terminal/2026-11-18-verification-log-terminal.png). The capture shows the artifact-verification output, both exact-match test lines, exit code 0, and the 21-test summary. The complete command output remains in the linked `.log` files above.

---

<a id="entry-12"></a>
## Entry 12 — ASK prefix preservation and reference-assisted reproduction

**Appendix/report:** [Appendix A.15](report/APPENDIX.md#app-a15-ask-prefix-preservation-and-reproduction) · [Report §2.2 and §3](report/REPORT.md)

**Date:** 19 November 2026

**Technical hypothesis:** projecting each symbol from its original target samples with carrier phase anchored to global sample indices will preserve leading ASK symbols when reference alignment begins inside a symbol.

### Implementation and regression case

The ASK decoder now retains the target prefix before the aligned overlap and decodes from sample zero. Per-symbol I/Q projection uses the original samples in each symbol window and the global sample index for carrier phase, so each measurement uses the intended target-sample window. The decoder result includes the number of decoded complete-byte characters.

The synthetic regression signal places the alignment start one and a half symbol periods into the target. It checks the first 16 labels against the generated bit stream, verifies the initial ASK level, and confirms the full 39-character flag remains intact.

### Commands and observed results

```text
rtk proxy env PYTHONPATH=src .venv/repro314/bin/python -m unittest discover -s tests -v
rtk proxy env PYTHONPATH=src .venv/repro314/bin/python -m stegano sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3 --reference data/sleepy_alarm/morning_n_breakfast_original.mp3
```

The full unittest run passed all 22 tests in 2.966 seconds with exit code 0. The first attempt using the system Python could not import Streamlit; rerunning with the project's Python 3.14 environment succeeded. A review rerun on 19 November passed all 22 tests in 2.826 seconds with exit code 0. AppTest printed three `missing ScriptRunContext` warnings in bare mode; the page test still passed.

The reference-assisted decoder run returned `format_valid: true`, `reference_assisted: true`, 350 symbols, 38 separators, 39 characters, and no byte errors. The decoded flag was `ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}`. Alignment reported a 1,729-sample lag and target start, with normalized correlation 0.9998734358246231.

The separate run manifest records the mode, 8,000 Hz carrier, 50 baud, 7-second window, input hashes, counts, and SHA-256 values for the JSON output and log. The original [`artifact_manifest.json`](results/artifact_manifest.json) remains the input-integrity record.

**Run artifacts:** [decoded output](results/reproduction-2026-11-19/sleepy-alarm-reference-assisted-output.json) · [run log](results/reproduction-2026-11-19/sleepy-alarm-reference-assisted.log) · [run manifest](results/reproduction-2026-11-19/sleepy-alarm-reference-assisted-manifest.json)

**Screenshots:** [Streamlit ASK diagnostics](evidence/visualization/2026-11-19-sleepy-alarm-streamlit.png) · [rendered run log](evidence/visualization/2026-11-19-sleepy-alarm-run-log.png)

The Streamlit screenshot shows the 350/38/39 metrics, the first 32 symbol projections, symbol boundaries, and the red alignment-overlap marker. The log screenshot shows the saved `.log` contents rendered in a browser; it is not a terminal capture.

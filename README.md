# STEGANO — Steganography CTF Project

**Course:** UET.CN3124 — Information Security (An toàn và an ninh mạng)  
**Topic:** Steganography (CTF Jeopardy)  
**Challenges:** Blue 3 (image) and Sleepy Alarm (audio)

## Project overview

This project investigates two public CTF challenges that conceal data in digital media: **Blue 3** (BYU-CSA) and **Sleepy Alarm** (ImaginaryCTF 2024). It implements independent extraction scripts, validates decoded outputs against the challenge formats, evaluates fixed-threshold baseline detectors and transformation robustness, and documents the experimental trace with reproducible verification records.

## Environment setup

Requires **Python 3.10 or newer**. The recorded verification runs in this repository use **Python 3.14.10**.

- `requirements.txt` specifies compatible version ranges for the core dependencies.
- `requirements-lock.txt` records the exact package versions (`pip freeze`) from the verified Python 3.14.10 environment.

Create and activate a virtual environment from the repository root:

```bash
python3 -m venv .venv/repro
source .venv/repro/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
# Optional exact-version lockfile from the verified Python 3.14.10 environment:
# pip install -r requirements-lock.txt
```

On Windows PowerShell, activate with `.venv\repro\Scripts\Activate.ps1` and set `$env:PYTHONPATH="src"` before running module commands.

## Verify artifacts and run tests

```bash
python scripts/verify_artifacts.py
PYTHONPATH=src python -m unittest discover -s tests -v
```

- `verify_artifacts.py` checks file sizes and SHA-256 digests of the three challenge inputs against `results/artifact_manifest.json` (expected: `3/3` pass).
- The `unittest` suite contains **22 tests** covering image/audio decoding, alignment, exact-match validation, and Streamlit visualization pages.

## Run the decoders

From the repository root:

```bash
PYTHONPATH=src python -m stegano blue3 data/blue3/blue.png
PYTHONPATH=src python -m stegano sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3 --reference data/sleepy_alarm/morning_n_breakfast_original.mp3
```

Sleepy Alarm's reference-assisted run uses the original recording to align and subtract the carrier audio; this is reference-assisted extraction, not blind steganalysis. Omitting `--reference` runs reference-free mode, which fails to recover a valid flag and is retained as a negative result:

```bash
PYTHONPATH=src python -m stegano sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3
```

## Steganalysis benchmark, robustness, and figures

```bash
python scripts/run_steganalysis_benchmark.py
python scripts/run_extended_robustness.py
PYTHONPATH=src python scripts/run_audio_asymmetric.py
python scripts/inspect_discovery_signals.py
python scripts/render_report_figures.py
```

- `run_steganalysis_benchmark.py` evaluates fixed-threshold image and audio heuristic detectors on challenge samples plus deterministic synthetic benign controls (`results/steganalysis/benchmark.json`), and compares reference-free vs reference-assisted Sleepy Alarm decoding. Comparisons with [Aperi'Solve](https://github.com/Zeecka/AperiSolve), [The-A-Files](https://github.com/pawel-kaczmarek/The-A-Files), and [WavSteg](https://github.com/ragibson/Steganography) record method scope only; those external tools are not executed.
- `run_extended_robustness.py` saves the 9-variant Blue 3 matrix and 23-trial Sleepy Alarm matrix under `results/robustness/`. PASS requires `format_valid`, exact ground-truth match, and zero byte errors.
- `run_audio_asymmetric.py` runs the earlier 6-variant one-sided audio robustness experiment (`results/asymmetric/`).
- `render_report_figures.py` generates the four static SVG figures in `report/figures/`.

## Visualizations

Launch the Streamlit diagnostic dashboard from the repository root:

```bash
streamlit run visualization/app.py
```

The dashboard displays artifact integrity and exact-match status (`visualization/app.py`), Blue 3 RGB channel histogram and selected diagonal blocks (`visualization/pages/1_Blue_3.py`), and Sleepy Alarm resampling, cross-correlation alignment, residual, ASK symbol clustering, first-32-symbol zoom, and 6-variant asymmetric robustness (`visualization/pages/2_Sleepy_Alarm.py`).

## Evidence collection workflow

1. Keep original files in `data/` untouched and verify checksums via `python scripts/verify_artifacts.py`.
2. Save terminal outputs and machine-readable JSON/CSV records under a dedicated run folder in `results/` (without overwriting historical folders).
3. Store unaltered terminal and dashboard screenshots under `evidence/terminal/` and `evidence/visualization/`.
4. Record commands, environments, actual outputs, exit codes, and limitations in [LOGBOOK.md](LOGBOOK.md) and [report/APPENDIX.md](report/APPENDIX.md).

## Quality gate and packaging

After changes to reports, scripts, or tests, rebuild the submission archive and run the automated quality gate into a **new** results directory (for example `results/final/`) so historical snapshots (`results/verification/`, `results/recheck/`) remain preserved:

```bash
python scripts/create_submission_zip.py
python scripts/verify_reproducibility.py \
  --output results/final/quality-gate.json \
  --provenance-output results/final/provenance.json \
  --log-output results/final/reproducibility.log
```

`verify_reproducibility.py` executes artifact verification, the full 22-test `unittest` suite, source provenance hashing, and archive CRC/byte-comparison checks.

## Repository structure

| Path | Role |
|---|---|
| `data/` | Official challenge artifacts (`blue3/blue.png`, `sleepy_alarm/*.mp3`) — read-only |
| `src/stegano/` | Decoder package (`image.py`, `audio.py`, `cli.py`, `__main__.py`) |
| `src/audio_alignment.py` | Audio resampling and cross-correlation alignment helper for the visualizer |
| `src/steganalysis.py` | Explainable first-pass image/audio heuristic detectors with fixed thresholds |
| `scripts/` | Verification, benchmark, robustness, figure rendering, provenance, and packaging scripts |
| `tests/` | `unittest` suite (22 tests) |
| `visualization/` | Streamlit multi-page diagnostic application |
| `results/artifact_manifest.json` | Pinned byte sizes, SHA-256 digests, and official challenge URLs |
| `results/` | Saved historical run logs, JSON/CSV records, and `results/final/` quality gate outputs |
| `evidence/` | Unaltered terminal and dashboard screenshots |
| `report/` | Vietnamese report (`REPORT.md`), exported PDF, `APPENDIX.md`, and `figures/*.svg` |
| `LOGBOOK.md` | Chronological experiment log (Entries 00–16) |
| `requirements.txt` / `requirements-lock.txt` | Dependency ranges and pinned Python 3.14.10 lockfile |
| `submission_package_current.zip` | Submission archive generated by `scripts/create_submission_zip.py` |

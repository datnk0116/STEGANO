# STEGANO — Steganography CTF Project

**Course:** UET.CN3124 — CTF Jeopardy  
**Topic:** Steganography  
**Challenges:** Blue 3 (image) and Sleepy Alarm (audio)

## Project overview

This project investigates two public CTF challenges that conceal data in digital media. It implements independent extraction workflows, validates their output using the challenge formats, and documents the experimental process, evidence and limitations.

## Environment setup

Requires Python 3.10 or newer. The highest Python version used in this project’s recorded runs is Python 3.14.10, in `.venv/repro314`. Use Python 3.14.10 for reproducing the later project runs; older environment readings remain attached to their original entries.

```bash
python3.14 --version  # project reproduction environment: Python 3.14.10
python3.14 -m venv .venv/repro314
source .venv/repro314/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with `.venv\\Scripts\\Activate.ps1`.

## Run the challenges

From the repository root:

```bash
PYTHONPATH=src python -m stegano blue3 data/blue3/blue.png
PYTHONPATH=src python -m stegano sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3 --reference data/sleepy_alarm/morning_n_breakfast_original.mp3
```

On Windows, use `$env:PYTHONPATH="src"` before the commands.

Sleepy Alarm's reference-assisted run uses the original recording to align and subtract the carrier audio. This is a reference-assisted extraction, not blind steganalysis. The reference-free mode is available by omitting `--reference`; its output must be assessed separately.

## Steganalysis benchmark and robustness

From the repository root, run the fixed-threshold image/audio baseline benchmark and the expanded challenge-specific robustness matrices:

```bash
python scripts/run_steganalysis_benchmark.py
python scripts/run_extended_robustness.py
```

The benchmark records sample-level predictions and TP/TN/FP/FN metrics in `results/steganalysis/benchmark.json`. It also compares reference-free and reference-assisted Sleepy Alarm extraction. Benign controls are deterministic synthetic samples, not a representative real-world corpus. The comparison with [Aperi'Solve](https://github.com/Zeecka/AperiSolve), [The-A-Files](https://github.com/pawel-kaczmarek/The-A-Files), and [WavSteg](https://github.com/ragibson/Steganography) records capability and method scope only; the tools are not executed by these scripts.

The robustness run saves JSON and CSV results under `results/robustness/`. PASS requires exact ground-truth recovery, a valid challenge format, and no byte errors. Reference-free Sleepy Alarm remains a failed extraction and is reported separately.

To keep output visible while saving a terminal log, run:

```bash
rtk proxy .venv/repro314/bin/python scripts/run_steganalysis_benchmark.py | tee results/steganalysis/benchmark-run.log
rtk proxy .venv/repro314/bin/python scripts/run_extended_robustness.py | tee results/robustness/extended-robustness-run.log
```

## Capture evidence

Run the Streamlit decoder views from the repository root:

```bash
rtk proxy .venv/repro314/bin/python -m streamlit run visualization/app.py
```

Capture the overview's artifact/exact-match status and separate Blue 3 and Sleepy Alarm diagnostic sections. The current Streamlit pages show decoder diagnostics and the earlier six-case asymmetric audio experiment; the new detector benchmark and 9/23-case extended matrices are not wired into those pages. Capture their TP/TN/FP/FN and PASS summaries from the terminal commands above. Keep screenshots as direct, unaltered captures under `evidence/terminal/` or `evidence/visualization/`; see [Appendix A.19](report/APPENDIX.md#app-a19-visualization-evidence-review) for the indexed dashboard captures.

## Visualizations

Launch the Streamlit overview from the repository root:

```bash
streamlit run visualization/app.py
```

The Sleepy Alarm page shows bounded source waveforms and alignment diagnostics from `src/audio_alignment.py`, including the resampled reference, correlation profile, aligned overlap and residual. Its ASK diagnosis plots the decoder's channel-0 amplitude measurements for each symbol with the three cluster centers and labels, and reports symbol, separator and decoded character counts. A close-up of the first 32 symbols shows symbol boundaries and the reference-overlap start; the decoded byte table lists bits and characters. On Blue 3, the plot labeled **RGB channel distribution** is the histogram of pixel values (0–255) for the red, green and blue channels. The page also highlights the selected diagonal blocks and lists each block's RGB delta, character code and decoded character.

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

A passing integration test checks the decoder output against the expected challenge text. Keep the complete terminal output as evidence and record the actual exit code and environment in [LOGBOOK.md](LOGBOOK.md).

## Repository structure

- `src/stegano/`: extraction algorithms and CLI.
- `src/steganalysis.py`: explainable first-pass image/audio heuristic detectors.
- `scripts/run_steganalysis_benchmark.py` and `scripts/run_extended_robustness.py`: reproducible benchmark and robustness runs.
- `results/steganalysis/` and `results/robustness/`: benchmark, matrix results, and run logs.
- `visualization/`: Streamlit overview and Blue 3 and Sleepy Alarm pages.
- `data/`: official challenge artifacts used by the experiments.
- `tests/`: image and audio integration tests.
- `report/REPORT.md`: technical report.
- `LOGBOOK.md`: experiment log, exact commands and evidence register.
- `evidence/`: screenshots and captured run evidence.

## Run instructions and evidence

Do not edit original files under `data/`. Store generated plots, decoded outputs and logs under `results/`; store screenshots under `evidence/`. Record the command, date, environment, actual result and corresponding evidence filename for every run. Do not claim a run passed until it has actually completed successfully.

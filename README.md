# STEGANO — Steganography CTF Project

**Course:** UET.CN3124 — CTF Jeopardy  
**Topic:** Steganography  
**Challenges:** Blue 3 (image) and Sleepy Alarm (audio)

## Project overview

This project investigates two public CTF challenges that conceal data in digital media. It implements independent extraction workflows, validates their output using the challenge formats, and documents the experimental process, evidence and limitations.

## Environment setup

Requires Python 3.10 or newer.

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
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

## Visualizations

Launch the Streamlit overview from the repository root:

```bash
streamlit run visualization/app.py
```

The Sleepy Alarm page shows bounded source waveforms and alignment diagnostics from `src/audio_alignment.py`, including the resampled reference, correlation profile, aligned overlap and residual. Its ASK diagnosis plots the decoder's channel-0 amplitude measurements for each symbol with the three cluster centers and labels, and reports symbol, separator and decoded character counts. A close-up of the first 32 symbols shows symbol boundaries and the reference-overlap start; the decoded byte table lists bits and characters. The Blue 3 page shows the RGB baseline and histogram, highlights the selected diagonal blocks, and lists each block's RGB delta, character code and decoded character.

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

A passing integration test checks the decoder output against the expected challenge text. Keep the complete terminal output as evidence and record the actual exit code and environment in [LOGBOOK.md](LOGBOOK.md).

## Repository structure

- `src/stegano/`: extraction algorithms and CLI.
- `visualization/`: Streamlit overview and Blue 3 and Sleepy Alarm pages.
- `data/`: official challenge artifacts used by the experiments.
- `tests/`: image and audio integration tests.
- `report/REPORT.md`: technical report.
- `LOGBOOK.md`: experiment log, exact commands and evidence register.
- `evidence/`: screenshots and captured run evidence.

## Run instructions and evidence

Do not edit original files under `data/`. Store generated plots, decoded outputs and logs under `results/`; store screenshots under `evidence/`. Record the command, date, environment, actual result and corresponding evidence filename for every run. Do not claim a run passed until it has actually completed successfully.

#!/usr/bin/env python3
"""Render the report's static SVG figures from saved STEGANO result JSON."""

from __future__ import annotations

import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINAL_DATA = ROOT / "results/final-2026-11-27"
ROBUSTNESS_DATA = ROOT / "results/robustness"
STEGANALYSIS_DATA = ROOT / "results/steganalysis"
OUT = ROOT / "report/figures"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def text(x: int, y: int, value: object, size: int = 16, fill: str = "#1c2940", weight: int = 400) -> str:
    return f'<text x="{x}" y="{y}" font-family="Arial,Helvetica,sans-serif" font-size="{size}px" font-weight="{weight}" fill="{fill}">{esc(value)}</text>'


def rect(x: int, y: int, w: int, h: int, fill: str, rx: int = 12, stroke: str = "#d9e0ea") -> str:
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>'


def start(width: int, height: int, title: str, subtitle: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#7890ad"/></marker></defs>',
        '<rect width="100%" height="100%" fill="#f6f8fb"/>',
        text(34, 48, title, 27, "#17243a", 700),
        text(34, 76, subtitle, 14, "#53647c"),
    ]


def finish(parts: list[str], path: Path) -> None:
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def status_color(value: str) -> str:
    normalized = value.lower()
    if normalized in {"passed", "verified", "pass"}:
        return "#17804b"
    if normalized in {"failed", "fail"}:
        return "#bd3b37"
    return "#9a6b13"


def render_quality_gate() -> None:
    gate = read_json(FINAL_DATA / "quality-gate.json")
    provenance = read_json(FINAL_DATA / "provenance.json")
    run = gate["verification_run"]
    tests = run["tests"]
    artifacts = run["artifact_integrity"]
    inventory = provenance["source_inventory"]
    quality = gate["quality_gate"]
    cards = [
        ("UNITTEST", f'{tests["passed"]}/{tests["total"]}', f'{tests["failed"]} failures', tests["status"]),
        ("ARTIFACTS", f'{artifacts["passed"]}/{artifacts["total"]}', "size + SHA-256", artifacts["status"]),
        ("PROVENANCE", provenance["status"], f'{inventory["file_count"]} inventoried files', provenance["status"]),
    ]
    parts = start(
        1000,
        400,
        "Quality gate summary",
        "Values read from results/final-2026-11-27/quality-gate.json and provenance.json",
    )
    q_color = status_color(quality["status"])
    parts += [
        rect(30, 96, 940, 64, "#e8f4ed" if q_color == "#17804b" else "#f9e8e7", 14),
        text(54, 136, f'QUALITY GATE  {quality["status"].upper()}', 25, q_color, 700),
    ]
    for i, (label, value, detail, state) in enumerate(cards):
        x = 30 + i * 320
        parts.append(rect(x, 183, 300, 150, "#ffffff"))
        parts.append(text(x + 20, 215, label, 13, "#53647c", 700))
        parts.append(text(x + 20, 263, value, 27, status_color(state), 700))
        parts.append(text(x + 20, 295, detail, 13, "#53647c"))
    env = provenance.get("environment", {})
    parts.append(
        text(
            34,
            372,
            f'Python {env.get("python", "unknown")} · submission_ready={str(quality.get("submission_ready", False)).lower()} · packaging: manual from tracked Git files',
            14,
            "#53647c",
        )
    )
    finish(parts, OUT / "quality-gate-summary.svg")


def short_label(row: dict) -> str:
    if row.get("variant") == "baseline":
        return "baseline"
    side = row.get("transformed_side", "")
    variant = row.get("variant", "").replace("target_", "").replace("reference_", "").replace("_", " ")
    prefix = f"{side}: " if side in {"target", "reference"} else ""
    label = prefix + variant
    return label if len(label) <= 42 else label[:39] + "…"


def render_robustness() -> None:
    blue = read_json(ROBUSTNESS_DATA / "blue3_extended_robustness.json")
    audio = read_json(ROBUSTNESS_DATA / "sleepy_alarm_robustness_matrix.json")
    parts = start(1100, 760, "Extended robustness results", "PASS/FAIL by saved trial; baseline is shown separately for Blue 3")
    parts += [rect(28, 100, 410, 620, "#ffffff"), rect(455, 100, 617, 620, "#ffffff")]
    parts += [text(50, 134, f'Blue 3 · {blue["success_count"]}/{blue["variant_count"]} variants', 19, "#17243a", 700),
              text(478, 134, f'Sleepy Alarm · {audio["pass_count"]}/{audio["trial_count"]} trials', 19, "#17243a", 700)]
    base = blue["baseline"]
    base_color = status_color(base["status"])
    parts += [rect(50, 151, 365, 36, "#f1f4f8", 8), text(62, 175, f'Baseline · {base["decoded_length"]}/50 chars', 13),
              text(350, 175, base["status"], 13, base_color, 700)]
    for i, row in enumerate(blue["results"]):
        y = 205 + i * 47
        c = status_color(row["status"])
        parts += [text(62, y + 19, row.get("transformation", row["variant"]), 13),
                  rect(350, y, 60, 28, "#e7f4eb" if c == "#17804b" else "#fae9e8", 7, "none"),
                  text(363, y + 19, row["status"], 12, c, 700)]
    for i, row in enumerate(audio["results"]):
        y = 155 + i * 23
        c = status_color(row["status"])
        parts += [text(478, y + 16, short_label(row), 12),
                  rect(990, y, 60, 19, "#e7f4eb" if c == "#17804b" else "#fae9e8", 5, "none"),
                  text(1001, y + 14, row["status"], 10, c, 700)]
    parts.append(text(34, 744, "PASS criteria: valid format + exact ground-truth match + no byte errors. One challenge artifact per matrix.", 13, "#53647c"))
    finish(parts, OUT / "robustness-heatmaps.svg")


def render_matrix(parts: list[str], x: int, y: int, title: str, metric: dict) -> None:
    parts.append(rect(x, y, 500, 360, "#ffffff"))
    parts.append(text(x + 24, y + 38, f'{title} · n={metric["sample_count"]}', 19, "#17243a", 700))
    parts += [text(x + 181, y + 78, "Predicted benign", 12, "#53647c", 700),
              text(x + 347, y + 78, "Predicted stego", 12, "#53647c", 700),
              text(x + 22, y + 133, "Actual benign", 12, "#53647c", 700),
              text(x + 22, y + 233, "Actual stego", 12, "#53647c", 700)]
    cells = [
        (x + 178, y + 94, metric["tn"], "TN"), (x + 342, y + 94, metric["fp"], "FP"),
        (x + 178, y + 194, metric["fn"], "FN"), (x + 342, y + 194, metric["tp"], "TP"),
    ]
    for cx, cy, value, label in cells:
        parts += [rect(cx, cy, 145, 78, "#edf3f8", 8), text(cx + 20, cy + 34, value, 26, "#17243a", 700),
                  text(cx + 20, cy + 58, label, 12, "#53647c")]
    parts.append(text(x + 24, y + 317, f'Recall {metric["recall"]:.2f} · F1 {metric["f1"]:.2f}', 14, "#53647c"))


def render_benchmark() -> None:
    benchmark = read_json(STEGANALYSIS_DATA / "benchmark.json")
    parts = start(1100, 545, "Baseline detector confusion matrices", "Rows are actual labels; columns are predicted labels")
    render_matrix(parts, 30, 105, "Image", benchmark["metrics"]["image"])
    render_matrix(parts, 570, 105, "Audio", benchmark["metrics"]["audio"])
    parts.append(text(35, 512, "Image: 12 synthetic benign controls + 5 positive samples. Audio: 8 synthetic benign controls + 5 positive samples.", 13, "#53647c"))
    finish(parts, OUT / "benchmark-confusion-matrices.svg")


def node(parts: list[str], x: int, y: int, w: int, title: str, value: str, color: str = "#eaf0f7") -> None:
    parts.append(rect(x, y, w, 88, color, 12))
    parts.append(text(x + 14, y + 30, title, 13, "#53647c", 700))
    parts.append(text(x + 14, y + 59, value, 16, "#17243a", 700))


def arrow(parts: list[str], x1: int, y1: int, x2: int, y2: int) -> None:
    parts.append(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="#7890ad" stroke-width="2" fill="none" marker-end="url(#arrow)"/>')


def render_provenance() -> None:
    gate = read_json(FINAL_DATA / "quality-gate.json")
    provenance = read_json(FINAL_DATA / "provenance.json")
    artifacts = provenance["artifact_integrity"]
    inventory = provenance["source_inventory"]
    tests = gate["verification_run"]["tests"]
    status = gate["quality_gate"]["status"].upper()
    parts = start(1100, 480, "Provenance and verification flow", "Manifested challenge inputs, current checkout, run suite, and manual packaging")
    node(parts, 50, 120, 270, "SOURCE + MANIFEST", "2 official challenge URLs")
    node(parts, 410, 120, 270, "ARTIFACT INTEGRITY", f'{artifacts["passed"]}/{artifacts["total"]} SHA-256 checks')
    node(parts, 780, 120, 270, "CURRENT CHECKOUT", f'{inventory["file_count"]} files inventoried')
    node(parts, 780, 260, 270, "SUBMISSION PACKAGING", "Manual (clean Git branch)", "#eaf0f7")
    node(parts, 50, 280, 270, "UNITTEST", f'{tests["passed"]}/{tests["total"]} passed', "#e8f4ed" if tests["status"] == "passed" else "#fae9e8")
    node(parts, 410, 310, 270, "QUALITY GATE", status, "#e8f4ed" if status == "PASSED" else "#fae9e8")
    arrow(parts, 320, 164, 410, 164)
    arrow(parts, 915, 208, 915, 260)
    arrow(parts, 320, 324, 410, 354)
    arrow(parts, 545, 208, 545, 310)
    arrow(parts, 780, 304, 680, 354)
    parts.append(text(34, 438, "All source, script, test, evidence, figure, and report files are SHA-256 hashed; submission archive is packaged manually from tracked Git files.", 12, "#53647c"))
    finish(parts, OUT / "provenance-flow.svg")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    render_quality_gate()
    render_robustness()
    render_benchmark()
    render_provenance()
    print(f"Rendered 4 report figures in {OUT}")


if __name__ == "__main__":
    main()

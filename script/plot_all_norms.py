#!/usr/bin/env python3
"""
Plot self_coop vs eq0 from main_ExhaustiveSearch output.

Reads script/output/all_norms.tsv. Points with
behavioral_max_advantage_bc2 >= 0.05 are plotted in gray.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from utils import figure_path, output_path


INPUT_FILE = output_path("all_norms.tsv")
OUTPUT_FILE = figure_path("all_norms_self_coop_vs_eq0.pdf")
BEHAVIORAL_ADVANTAGE_THRESHOLD = 0.05


@dataclass(frozen=True)
class AllNormsPoint:
  rd: int
  rr: int
  self_coop: float
  eq0: float
  behavioral_max_advantage: float


@dataclass(frozen=True)
class HighlightSpec:
  rd: int
  rr: int
  label: str
  color: str
  marker: str


HIGHLIGHTS: tuple[HighlightSpec, ...] = (
  HighlightSpec(186, 204, "L1v-base", "tab:orange", "o"),
  HighlightSpec(154, 204, "L2v-base", "tab:orange", "o"),
  HighlightSpec(187, 204, "L3-base", "tab:orange", "o"),
  HighlightSpec(185, 204, "L4-base", "tab:orange", "o"),
  HighlightSpec(155, 204, "L5-base", "tab:orange", "o"),
  HighlightSpec(153, 204, "L6-base", "tab:orange", "o"),
  HighlightSpec(184, 204, "L7-base", "tab:orange", "o"),
  HighlightSpec(152, 204, "L8-base", "tab:orange", "o"),
  HighlightSpec(186, 170, "L1v-RIS", "tab:green", "s"),
  HighlightSpec(154, 170, "L2v-RIS", "tab:green", "s"),
  HighlightSpec(187, 170, "L3-RIS", "tab:green", "s"),
  HighlightSpec(185, 170, "L4-RIS", "tab:green", "s"),
  HighlightSpec(155, 170, "L5-RIS", "tab:green", "s"),
  HighlightSpec(153, 170, "L6-RIS", "tab:green", "s"),
  HighlightSpec(184, 170, "L7-RIS", "tab:green", "s"),
  HighlightSpec(152, 170, "L8-RIS", "tab:green", "s"),
)


def format_axis_tick(value: float, _position: int) -> str:
  if abs(value) < 1.0e-12:
    value = 0.0
  label = f"{value:.2f}".rstrip("0").rstrip(".")
  if "." not in label:
    label += ".0"
  return label


def parse_header(row: list[str]) -> list[str]:
  if not row:
    raise ValueError("empty TSV header")
  first = row[0].strip()
  if first.startswith("#"):
    first = first[1:].strip()
  return [first, *row[1:]]


def load_all_norms(path: Path) -> list[AllNormsPoint]:
  points: list[AllNormsPoint] = []

  with path.open("r", newline="") as f:
    reader = csv.reader(f, delimiter="\t")
    header: list[str] | None = None

    for row in reader:
      if not row:
        continue
      if header is None:
        header = parse_header(row)
        continue

      values = dict(zip(header, row))
      points.append(AllNormsPoint(
        rd=int(values["rd"]),
        rr=int(values["rr"]),
        self_coop=float(values["self_coop"]),
        eq0=float(values["eq0"]),
        behavioral_max_advantage=float(values["behavioral_max_advantage_bc2"]),
      ))

  return points


def is_behaviorally_unstable(point: AllNormsPoint) -> bool:
  return (
    not math.isfinite(point.behavioral_max_advantage)
    or point.behavioral_max_advantage >= BEHAVIORAL_ADVANTAGE_THRESHOLD
  )


def find_point(points: list[AllNormsPoint], rd: int, rr: int) -> AllNormsPoint | None:
  for point in points:
    if point.rd == rd and point.rr == rr:
      return point
  return None


def add_highlights(ax, points: list[AllNormsPoint]) -> None:
  for highlight in HIGHLIGHTS:
    point = find_point(points, highlight.rd, highlight.rr)
    if point is None:
      print(f"[WARN] Highlight point not found: {highlight.label} ({highlight.rd}, {highlight.rr})")
      continue

    ax.scatter(
      [point.self_coop],
      [point.eq0],
      s=90,
      color=highlight.color,
      marker=highlight.marker,
      edgecolors="black",
      linewidths=0.8,
      zorder=4,
    )


def plot_self_coop_vs_eq0(points: list[AllNormsPoint]):
  unstable = [point for point in points if is_behaviorally_unstable(point)]
  stable = [point for point in points if not is_behaviorally_unstable(point)]

  fig, ax = plt.subplots(figsize=(6, 5))

  ax.scatter(
    [point.self_coop for point in unstable],
    [point.eq0 for point in unstable],
    s=9,
    color="lightgray",
    alpha=0.45,
    edgecolors="none",
    label=fr"behavioral advantage $\geq {BEHAVIORAL_ADVANTAGE_THRESHOLD:g}$",
    zorder=1,
  )
  ax.scatter(
    [point.self_coop for point in stable],
    [point.eq0 for point in stable],
    s=10,
    color="tab:blue",
    alpha=0.75,
    edgecolors="none",
    label=fr"behavioral advantage $< {BEHAVIORAL_ADVANTAGE_THRESHOLD:g}$",
    zorder=2,
  )
  add_highlights(ax, points)

  ax.set_xlabel("self-cooperation level", fontsize=24)
  ax.set_ylabel("equilibrium fraction", fontsize=24)
  ax.set_xlim(-0.03, 1.03)
  ax.set_ylim(-0.05, 1.05)
  ax.xaxis.set_major_formatter(FuncFormatter(format_axis_tick))
  ax.yaxis.set_major_formatter(FuncFormatter(format_axis_tick))
  ax.tick_params(axis="both", labelsize=16)
  ax.grid(True, linestyle=":", alpha=0.5)
  ax.spines["top"].set_visible(False)
  ax.spines["right"].set_visible(False)

  fig.subplots_adjust(left=0.16, right=0.97, top=0.96, bottom=0.15)
  return fig, ax


def main() -> None:
  points = load_all_norms(INPUT_FILE)
  if not points:
    raise RuntimeError(f"No data rows found in {INPUT_FILE}")

  unstable_count = sum(is_behaviorally_unstable(point) for point in points)
  print(f"[INFO] Loaded {len(points)} points from {INPUT_FILE}")
  print(
    "[INFO] Gray points: "
    f"{unstable_count} with behavioral_max_advantage_bc2 >= {BEHAVIORAL_ADVANTAGE_THRESHOLD:g}"
  )

  fig, _ax = plot_self_coop_vs_eq0(points)
  fig.savefig(OUTPUT_FILE)
  print(f"[INFO] Saved: {OUTPUT_FILE}")
  plt.show()


if __name__ == "__main__":
  main()
